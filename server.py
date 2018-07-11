import argparse
from socket import socket, AF_INET, SOCK_STREAM
import sys
import select
import logging
import inspect
import os
from time import sleep
from threading import Thread
from queue import Queue

import helpers
from jim import request_from_bytes, JimResponse, auth_server_message
from storage import DBStorageServer
import security
import log_confing

log = logging.getLogger(helpers.SERVER_LOGGER_NAME)


def parse_commandline_args(cmd_args):
    parser = argparse.ArgumentParser()
    parser.add_argument('-a', dest='listen_address', type=str, default='',
                        help='ip-address to listen on, default empty')
    parser.add_argument('-p', dest='listen_port', type=int, default=helpers.DEFAULT_SERVER_PORT,
                        help=f'tcp port to listen on, default {str(helpers.DEFAULT_SERVER_PORT)}')
    return parser.parse_args(cmd_args)


class ServerVerifierMeta(type):
    def __init__(cls, clsname, bases, clsdict):
        tcp_found = False

        for key, value in clsdict.items():
            if not hasattr(value, '__call__'):  # we need only methods further
                continue

            source = inspect.getsource(value)
            if '.connect(' in source:  # check there are no connect() socket calls
                raise RuntimeError('Server must not use connect for sockets')

            if 'SOCK_STREAM' in source:  # check that TCP sockets are used
                tcp_found = True

        if not tcp_found:
            raise RuntimeError('Server must use only TCP sockets')

        type.__init__(cls, clsname, bases, clsdict)


class Server(metaclass=ServerVerifierMeta):
    def __init__(self, host, port, storage,
                 clients_limit=helpers.CLIENTS_COUNT_LIMIT, timeout=helpers.SERVER_SOCKET_TIMEOUT):
        self.__host = host
        self.__port = port
        self.__storage_name = storage
        self.__clients_limit = clients_limit
        self.__timeout = timeout

        self.__socket = None
        self.__storage = None
        self.__need_terminate = False
        self.__worker_thread = None
        self.__print_queue = Queue()

    def start(self):
        if self.__socket:
            raise RuntimeError('Already started')
        self.__socket = socket(AF_INET, SOCK_STREAM)
        self.__socket.bind((self.__host, self.__port))
        self.__socket.listen(self.__clients_limit)
        self.__socket.settimeout(self.__timeout)
        self.__worker_thread = Thread(target=self.worker_thread_function)
        self.__worker_thread.daemon = True
        self.__worker_thread.start()

    def close_server(self):
        if not self.__socket:
            raise RuntimeError('Not running')
        self.__socket.close()
        self.__socket = None
        self.__need_terminate = True
        self.__worker_thread.join()
        self.__worker_thread = None

    def worker_thread_function(self):
        self.__storage = DBStorageServer(self.__storage_name)
        self.mainloop()
        self.__storage = None

    @property
    def print_queue(self):
        return self.__print_queue

    @property
    def storage(self):
        return self.__storage

    def mainloop(self):
        clients = []
        logins = {}
        auth_tokens = {}

        while True:
            if self.__need_terminate:
                return

            try:
                conn, addr = self.__socket.accept()  # check for new connections
            except OSError:
                pass  # timeout, do nothing
            else:
                self.__print_queue.put(f'Client connected: {str(addr)}')
                clients.append(conn)
            finally:  # check for incoming requests
                readable, writable, erroneous = [], [], []
                try:
                    readable, writable, erroneous = select.select(clients, clients, clients, 0)
                except:
                    pass  # if some client unexpectedly disconnected, do nothing

                for client_socket in readable:
                    try:
                        if client_socket not in writable:
                            continue
                        request = request_from_bytes(client_socket.recv(helpers.TCP_MSG_BUFFER_SIZE))
                        self.__print_queue.put(f'Request:\n{request}')
                        responses = []
                        if request.action == 'presence':
                            client_login = request.datadict['user']['account_name']
                            resp = JimResponse()
                            if not self.storage.check_client_exists(client_login):  # unknown client - error
                                resp.response = 400
                                resp.set_field('error', f'No such client: {client_login}')
                            elif client_login not in logins.values():  # known client arrived - need auth
                                token = security.create_auth_token()
                                auth_tokens[client_socket] = token
                                resp = auth_server_message(token)
                            elif client_socket in logins.keys() and \
                                    logins[client_socket] == client_login:  # existing client from same socket - ok
                                client_time = request.datadict['time']
                                client_ip = client_socket.getpeername()[0]
                                self.storage.update_client(client_login, client_time, client_ip)
                                resp.response = 200
                            else:  # existing client from different ip - not correct
                                resp.response = 400
                                resp.set_field('error', 'Client already online')
                            responses.append(resp)
                        elif request.action == 'authenticate':
                            client_login = request.datadict['user']['account_name']
                            client_hash = self.storage.get_client_hash(client_login)
                            auth_token = auth_tokens[client_socket]
                            del auth_tokens[client_socket]
                            expected_digest = security.create_auth_digest(client_hash, auth_token)
                            client_digest = request.datadict['user']['password']
                            resp = JimResponse()
                            if not security.check_auth_digest_equal(expected_digest, client_digest):
                                resp.response = 402
                                resp.set_field('error', 'Access denied')
                            else:  # add client login to dict, update client in database
                                logins[client_socket] = client_login
                                client_time = request.datadict['time']
                                client_ip = client_socket.getpeername()[0]
                                self.storage.update_client(client_login, client_time, client_ip)
                                resp.response = 200
                            responses.append(resp)
                        elif request.action == 'add_contact':
                            client_login = logins[client_socket]
                            contact_login = request.datadict['user_id']
                            resp = JimResponse()
                            if not self.storage.check_client_exists(contact_login):
                                resp.response = 400
                                resp.set_field('error', f'No such client: {contact_login}')
                            elif self.storage.check_client_in_contacts(client_login, contact_login):
                                resp.response = 400
                                resp.set_field('error', f'Client already in contacts: {contact_login}')
                            else:
                                self.storage.add_client_to_contacts(client_login, contact_login)
                                resp.response = 200
                            responses.append(resp)
                        elif request.action == 'del_contact':
                            client_login = logins[client_socket]
                            contact_login = request.datadict['user_id']
                            resp = JimResponse()
                            if not self.storage.check_client_exists(contact_login):
                                resp.response = 400
                                resp.set_field('error', f'No such client: {contact_login}')
                            elif not self.storage.check_client_in_contacts(client_login, contact_login):
                                resp.response = 400
                                resp.set_field('error', f'Client not in contacts: {contact_login}')
                            else:
                                self.storage.del_client_from_contacts(client_login, contact_login)
                                resp.response = 200
                            responses.append(resp)
                        elif request.action == 'get_contacts':
                            client_login = logins[client_socket]
                            client_contacts = self.storage.get_client_contacts(client_login)
                            quantity_resp = JimResponse()
                            quantity_resp.response = 202
                            quantity_resp.set_field('quantity', len(client_contacts))
                            responses.append(quantity_resp)
                            for contact in client_contacts:
                                contact_resp = JimResponse()
                                contact_resp.set_field('action', 'contact_list')
                                contact_resp.set_field('user_id', contact)
                                responses.append(contact_resp)
                        elif request.action == 'msg':
                            target_client_login = request.datadict['to']
                            resp = JimResponse()
                            for key, val in logins.items():
                                if val == target_client_login:
                                    key.send(request.to_bytes())
                                    resp.response = 200
                                    break
                            else:
                                resp.response = 400
                                resp.set_field('error', f'Client not online: {target_client_login}')
                            responses.append(resp)
                        else:
                            raise RuntimeError(f'Unknown JIM action: {request.action}')
                        self.__print_queue.put('Response:')
                        for resp in responses:
                            self.__print_queue.put(str(resp))
                            sleep(0.001)  # this magic solves problem with multiple jim messages in one socket message!!
                            client_socket.send(resp.to_bytes())
                    except BaseException as e:
                        self.__print_queue.put(f'Client disconnected: {client_socket.getpeername()}, {e}')
                        client_socket.close()
                        clients.remove(client_socket)
                        try:
                            del logins[client_socket]
                        except:
                            pass
                        if client_socket in writable:
                            writable.remove(client_socket)


def check_new_print_data_thread_function(print_queue: Queue):
    while True:
        if print_queue:
            print(print_queue.get())


if __name__ == '__main__':
    try:
        args = parse_commandline_args(sys.argv[1:])
        storage_file = os.path.join(helpers.get_this_script_full_dir(), 'server.sqlite')
        server = Server(args.listen_address, args.listen_port, storage_file)
        print_monitor = Thread(target=check_new_print_data_thread_function,
                               args=(server.print_queue,))
        print_monitor.daemon = True
        print_monitor.start()
        supported_commands = ['start', 'stop']
        main_menu = helpers.Menu(supported_commands)
        while True:
            user_choice = int(input(main_menu))
            command = main_menu.get_command(user_choice)
            if command == 'start':
                server.start()
            if command == 'stop':
                server.close_server()
    except BaseException as e:
        print(f'Error: {str(e)}')
        log.critical(str(e))
        raise e
