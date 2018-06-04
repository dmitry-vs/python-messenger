import argparse
from socket import socket, AF_INET, SOCK_STREAM
import sys
import select
import logging

import helpers
import log_confing

log = logging.getLogger(helpers.SERVER_LOGGER_NAME)


def parse_commandline_args(cmd_args):
    parser = argparse.ArgumentParser()
    parser.add_argument('-a', dest='listen_address', type=str, default='', help='ip-address to listen on, default empty')
    parser.add_argument('-p', dest='listen_port', type=int, default=helpers.DEFAULT_SERVER_PORT,
                        help=f'tcp port to listen on, default {str(helpers.DEFAULT_SERVER_PORT)}')
    return parser.parse_args(cmd_args)


class Server:
    def __init__(self):
        self._socket = socket(AF_INET, SOCK_STREAM)

    def set_settings(self, listen_address, listen_port,
                     clients_limit=helpers.CLIENTS_COUNT_LIMIT, timeout=helpers.SERVER_SOCKET_TIMEOUT):
        self._socket.bind((listen_address, listen_port))
        self._socket.listen(clients_limit)
        self._socket.settimeout(timeout)

    def __del__(self):
        self._socket.close()

    def mainloop(self):
        clients = []
        while True:
            try:
                conn, addr = self._socket.accept()  # check for new connections
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

                # read requests from all readable clients and save to dictionary
                requests = {}
                for client_socket in readable:
                    try:
                        requests[client_socket] = client_socket.recv(helpers.TCP_MSG_BUFFER_SIZE)
                    except:
                        print(f'Client disconnected: {client_socket.getpeername()}')
                        client_socket.close()
                        clients.remove(client_socket)

                # broadcast requests to all writable clients
                for req in requests.values():
                    for client_socket in writable:
                        try:
                            client_socket.send(req)
                        except:
                            print(f'Client disconnected: {client_socket.getpeername()}')
                            client_socket.close()
                            clients.remove(client_socket)


if __name__ == '__main__':
    print('Server started')
    log.info('Server started')
    try:
        args = parse_commandline_args(sys.argv[1:])
        server = Server()
        server.set_settings(args.listen_address, args.listen_port)
        server.mainloop()
    except Exception as e:
        log.critical(str(e))
        raise e
