import sys
from socket import socket, AF_INET, SOCK_STREAM
import argparse
import uuid
from time import sleep
import logging

import helpers
from jim import JimRequest, jim_request_from_bytes
import log_confing

log = logging.getLogger(helpers.CLIENT_LOGGER_NAME)


def parse_commandline_args(cmd_args):
    parser = argparse.ArgumentParser()
    parser.add_argument('-s', dest='server_ip', type=str, default='127.0.0.1', help='server ip, default 127.0.0.1')
    parser.add_argument('-p', dest='server_port', type=int, default=7777, help='server port, default 7777')
    parser.add_argument('-w', dest='mode_write', action='store_true', default=False,
                        help='client mode "write" (otherwise "read"), default False')
    return parser.parse_args(cmd_args)


class Client:
    def __init__(self, username):
        self.__username = username

    @property
    def username(self):
        return self.__username

    def create_presence(self):
        presence_message = JimRequest()
        presence_message.set_field('action', 'presence')
        presence_message.set_time()
        presence_message.set_field('user', {'account_name': self.__username})
        return presence_message


def send_data(sock, data: bytes) -> int:
    if type(data) is not bytes:
        raise TypeError
    return sock.send(data)


def receive_data(sock, size: int) -> bytes:
    if size <= 0:
        raise ValueError
    return sock.recv(size)


if __name__ == '__main__':
    log.info('Client started')
    try:
        args = parse_commandline_args(sys.argv[1:])
        client = Client(username=uuid.uuid4().hex[:8])  # using random username
        print(f'Started client with username {client.username}, mode', 'write' if args.mode_write else 'read')
        with socket(AF_INET, SOCK_STREAM) as client_socket:
            client_socket.connect((args.server_ip, args.server_port))
            while True:
                if args.mode_write:
                    message = client.create_presence()
                    print(f'Sending message to server: {message}')
                    send_data(client_socket, message.to_bytes())
                    sleep(1)
                else:
                    response = receive_data(client_socket, helpers.TCP_MSG_BUFFER_SIZE)
                    print(f'Received from server: {jim_request_from_bytes(response)}')
    except Exception as e:
        log.critical(str(e))
        raise e
