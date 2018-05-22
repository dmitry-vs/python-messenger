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


def read_requests(source_clients, all_clients):
    requests = {}
    for client_socket in source_clients:
        try:
            data = client_socket.recv(helpers.TCP_MSG_BUFFER_SIZE)
            requests[client_socket] = data
        except:
            print(f'Client disconnected: {client_socket.getpeername()}')
            client_socket.close()
            all_clients.remove(client_socket)
    return requests


def translate_requests(requests, target_clients, all_clients):
    for author_socket in requests:
        response = requests[author_socket]
        for client_socket in target_clients:
            try:
                client_socket.send(response)
            except:
                print(f'Client disconnected: {client_socket.getpeername()}')
                client_socket.close()
                all_clients.remove(client_socket)


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

            requests = read_requests(source_clients=readable, all_clients=clients)
            translate_requests(requests, target_clients=writable, all_clients=clients)


if __name__ == '__main__':
    args = parse_commandline_args(sys.argv[1:])
    mainloop(args)
