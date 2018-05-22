import argparse
from socket import socket, AF_INET, SOCK_STREAM
import sys
import select

import helpers


def parse_commandline_args(cmd_args):
    parser = argparse.ArgumentParser()
    parser.add_argument('-a', dest='listen_address', type=str, default='', help='ip-address to listen on, default empty')
    parser.add_argument('-p', dest='listen_port', type=int, default=helpers.DEFAULT_SERVER_PORT,
                        help=f'tcp port to listen on, default {str(helpers.DEFAULT_SERVER_PORT)}')
    return parser.parse_args(cmd_args)


def mainloop(cmd_args: argparse.Namespace):
    server_socket = socket(AF_INET, SOCK_STREAM)
    server_socket.bind((cmd_args.listen_address, cmd_args.listen_port))
    server_socket.listen(helpers.CLIENTS_COUNT_LIMIT)
    server_socket.settimeout(helpers.SERVER_SOCKET_TIMEOUT)
    clients = []

    while True:
        try:
            conn, addr = server_socket.accept()  # check for new connections
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

            # translate requests to all writable clients
            for req in requests.values():
                for client_socket in writable:
                    try:
                        client_socket.send(req)
                    except:
                        print(f'Client disconnected: {client_socket.getpeername()}')
                        client_socket.close()
                        clients.remove(client_socket)


if __name__ == '__main__':
    args = parse_commandline_args(sys.argv[1:])
    mainloop(args)
