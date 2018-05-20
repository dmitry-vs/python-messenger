import argparse
import socket as sck

import helpers

CLIENTS_COUNT_LIMIT = 5


def parse_commandline_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('-a', dest='listen_address', type=str, default='', help='ip-address to listen on')
    parser.add_argument('-p', dest='listen_port', type=int, default=helpers.DEFAULT_SERVER_PORT, help='tcp port to listen on')
    return parser.parse_args()


# receive client message, parse message, send answer

# add tests (pytest)


if __name__ == '__main__':
    args = parse_commandline_args()
    server_socket = sck.socket(sck.AF_INET, sck.SOCK_STREAM)
    server_socket.bind((args.listen_address, args.listen_port))
    server_socket.listen(CLIENTS_COUNT_LIMIT)
    print('Waiting for incoming connections...')

    while True:
        client, addr = server_socket.accept()
        print(f'received connection from {client}, {addr}')
        message = client.recv(helpers.TCP_MSG_BUFFER_SIZE)
        print(f'message from client: {message}')
        client.send(b'test_from_server')
        client.close()
