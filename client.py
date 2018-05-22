import sys
import socket as sck

import helpers
from jim import JimMessage, jim_msg_from_bytes


def parse_commandline_args(args):
    if len(args) not in [1, 2]:
        raise IndexError('Incorrect number of arguments')

    ip = args[0]
    port = int(args[1]) if len(args) > 1 else helpers.DEFAULT_SERVER_PORT
    return ip, port


def print_usage():
    print(f'usage: client.py <server_ip> [server_port]')


if __name__ == '__main__':
    server_ip, server_port = None, None
    try:
        server_ip, server_port = parse_commandline_args(sys.argv[1:])
    except:
        print_usage()
        exit(1)

    client_socket = sck.socket(sck.AF_INET, sck.SOCK_STREAM)
    client_socket.connect((server_ip, server_port))
    message = JimMessage()
    message.set_field('action', 'presence')
    message.set_time()
    print('sending presence message to server')
    client_socket.send(message.to_bytes())
    response = client_socket.recv(helpers.TCP_MSG_BUFFER_SIZE)
    server_message = jim_msg_from_bytes(response)
    print(f'response from server: {server_message}')
    client_socket.close()
