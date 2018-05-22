import sys
from socket import socket, AF_INET, SOCK_STREAM
import argparse

import helpers
from jim import JimMessage, jim_msg_from_bytes


def parse_commandline_args(cmd_args):
    parser = argparse.ArgumentParser()
    parser.add_argument('-s', dest='server_ip', type=str, default='127.0.0.1', help='server ip, default 127.0.0.1')
    parser.add_argument('-p', dest='server_port', type=int, default=7777, help='server port, default 7777')
    parser.add_argument('-w', dest='mode_write', action='store_true', default=False,
                        help='client mode "write" (otherwise "read"), default False')
    return parser.parse_args(cmd_args)


if __name__ == '__main__':
    args = parse_commandline_args(sys.argv[1:])
    with socket(AF_INET, SOCK_STREAM) as client_socket:
        client_socket.connect((args.server_ip, args.server_port))
        while True:
            import time
            if args.mode_write:
                message = JimMessage()
                message.set_field('action', 'presence')
                message.set_time()
                print(f'Sending message to server: {message}')
                client_socket.send(message.to_bytes())
                time.sleep(1)
            else:
                response = client_socket.recv(helpers.TCP_MSG_BUFFER_SIZE)
                print(jim_msg_from_bytes(response))
