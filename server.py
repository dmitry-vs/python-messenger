import argparse
import socket as sck
import sys

import helpers
from jim import JimMessage, jim_msg_from_bytes

CLIENTS_COUNT_LIMIT = 5


def parse_commandline_args(cmd_args):
    parser = argparse.ArgumentParser()
    parser.add_argument('-a', dest='listen_address', type=str, default='', help='ip-address to listen on')
    parser.add_argument('-p', dest='listen_port', type=int, default=helpers.DEFAULT_SERVER_PORT, help='tcp port to listen on')
    return parser.parse_args(cmd_args)


if __name__ == '__main__':
    args = parse_commandline_args(sys.argv[1:])
    server_socket = sck.socket(sck.AF_INET, sck.SOCK_STREAM)
    server_socket.bind((args.listen_address, args.listen_port))
    server_socket.listen(CLIENTS_COUNT_LIMIT)
    print('Waiting for incoming connections...')

    while True:
        client, addr = server_socket.accept()
        print(f'connection from client {addr}')
        message_bytes = client.recv(helpers.TCP_MSG_BUFFER_SIZE)
        message = jim_msg_from_bytes(message_bytes)
        print(f'message from client: {message}')
        response = JimMessage()
        response.set_field('response', 200)
        response.set_time()
        client.send(response.to_bytes())
        client.close()
