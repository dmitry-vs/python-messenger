import sys
import socket as sck

import helpers


def parse_commandline_args(args):
    temp_args = args[1:]
    ip = temp_args[0]
    port = int(temp_args[1]) if len(temp_args) > 1 else helpers.DEFAULT_SERVER_PORT
    return ip, port


def print_usage():
    print(f'usage: client.py <server_ip> [server_port]')


# create JIM presense-message

# send message to server, get response

# parse response


# add tests (pytest)


if __name__ == '__main__':
    server_ip, server_port = None, None
    try:
        server_ip, server_port = parse_commandline_args(sys.argv)
    except:
        print_usage()
        exit(1)

    client_socket = sck.socket(sck.AF_INET, sck.SOCK_STREAM)
    client_socket.connect((server_ip, server_port))
    client_socket.send(b'test_from_client')
    response = client_socket.recv(helpers.TCP_MSG_BUFFER_SIZE)
    print(f'message from server: {response}')
    client_socket.close()
