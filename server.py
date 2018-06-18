import argparse
from socket import socket, AF_INET, SOCK_STREAM
import sys
import select
import logging
import inspect

import helpers
from jim import jim_request_from_bytes, JimRequest, JimResponse
from storage import DBStorageServer
import log_confing

log = logging.getLogger(helpers.SERVER_LOGGER_NAME)


def parse_commandline_args(cmd_args):
    parser = argparse.ArgumentParser()
    parser.add_argument('-a', dest='listen_address', type=str, default='', help='ip-address to listen on, default empty')
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
    def __init__(self, storage):
        self.__socket = socket(AF_INET, SOCK_STREAM)
        self.__storage = DBStorageServer(storage)

    def set_settings(self, listen_address, listen_port,
                     clients_limit=helpers.CLIENTS_COUNT_LIMIT, timeout=helpers.SERVER_SOCKET_TIMEOUT):
        self.__socket.bind((listen_address, listen_port))
        self.__socket.listen(clients_limit)
        self.__socket.settimeout(timeout)

    def __del__(self):
        self.__socket.close()

    def update_client(self, login, last_connection_ip, last_connection_time, info=None):
        client_id = self.__storage.get_client_id(login)
        if not client_id:
            self.__storage.add_new_client(login)
            client_id = self.__storage.get_client_id(login)
        self.__storage.update_client(client_id, last_connection_time, last_connection_ip, info)

    def add_client_contact(self, client_login, contact_login):
        client_id = self.__storage.get_client_id(client_login)
        contact_id = self.__storage.get_client_id(contact_login)
        self.__storage.add_client_to_contacts(client_id, contact_id)

    def delete_client_contact(self, client_login, contact_login):
        client_id = self.__storage.get_client_id(client_login)
        contact_id = self.__storage.get_client_id(contact_login)
        self.__storage.del_client_from_contacts(client_id, contact_id)

    def get_client_contacts(self, client_login) -> list:
        client_id = self.__storage.get_client_id(client_login)
        return self.__storage.get_client_contacts(client_id)

    def mainloop(self):
        clients = []
        logins = {}
        while True:
            try:
                conn, addr = self.__socket.accept()  # check for new connections
            except OSError:
                pass  # timeout, do nothing
            else:
                print(f'Client connected: {str(addr)}')
                clients.append(conn)
            finally:  # check for input data, if found - translate it to all clients
                readable, writable, erroneous = [], [], []
                try:
                    readable, writable, erroneous = select.select(clients, clients, clients, 0)
                except:
                    pass  # if some client unexpectedly disconnected, do nothing

                for client_socket in readable:
                    try:
                        if client_socket not in writable:
                            continue
                        request = jim_request_from_bytes(client_socket.recv(helpers.TCP_MSG_BUFFER_SIZE))
                        request_action = request.datadict['action']
                        responses = []
                        if request_action == 'presence':
                            client_login = request.datadict['user']['account_name']
                            client_time = request.datadict['time']
                            client_ip = client_socket.getpeername()[0]
                            logins[client_socket] = client_login
                            server.update_client(client_login, client_ip, client_time)
                            response = JimResponse()
                            response.set_field('response', 200)
                            responses.append(response)
                        elif request_action == 'add_contact':
                            client_login = logins[client_socket]
                            contact_login = request.datadict['user_id']
                            server.add_client_contact(client_login, contact_login)
                            resp = JimResponse()
                            resp.set_field('response', 200)
                            responses.append(resp)
                        elif request_action == 'del_contact':
                            client_login = logins[client_socket]
                            contact_login = request.datadict['user_id']
                            server.delete_client_contact(client_login, contact_login)
                            resp = JimResponse()
                            resp.set_field('response', 200)
                            responses.append(resp)
                        elif request_action == 'get_contacts':
                            client_login = logins[client_socket]
                            client_contacts = server.get_client_contacts(client_login)
                            if not client_contacts:
                                client_contacts = []
                            quantity_resp = JimResponse()
                            quantity_resp.set_field('response', 202)
                            quantity_resp.set_field('quantity', len(client_contacts))
                            responses.append(quantity_resp)
                            for contact in client_contacts:
                                contact_resp = JimResponse()
                                contact_resp.set_field('action', 'contact_list')
                                contact_resp.set_field('user_id', contact)
                                responses.append(contact_resp)
                        else:
                            raise RuntimeError(f'Unknown JIM action: {request_action}')
                        for resp in responses:
                            print(resp)
                            client_socket.send(resp.to_bytes())
                    except BaseException as e:
                        print(f'Client disconnected: {client_socket.getpeername()}, {e}')
                        client_socket.close()
                        clients.remove(client_socket)
                        del logins[client_socket]
                        if client_socket in writable:
                            writable.remove(client_socket)


if __name__ == '__main__':
    print('Server started')
    log.info('Server started')
    try:
        args = parse_commandline_args(sys.argv[1:])
        server = Server(':memory:')
        server.set_settings(args.listen_address, args.listen_port)
        server.mainloop()
    except Exception as e:
        log.critical(str(e))
        raise e
