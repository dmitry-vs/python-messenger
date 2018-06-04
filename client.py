import sys
from socket import socket, AF_INET, SOCK_STREAM
import argparse
import uuid
from time import sleep
import logging
import inspect

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


class ClientVerifierMeta(type):
    def __init__(cls, clsname, bases, clsdict):
        tcp_found = False

        for key, value in clsdict.items():
            if type(value) is socket:  # check this is not class-level socket
                raise RuntimeError('Client must not use class-level sockets')

            if not hasattr(value, '__call__'):  # we need only methods further
                continue

            source = inspect.getsource(value)
            if '.accept(' in source or '.listen(' in source:  # check there are no accept() or listen() socket calls
                raise RuntimeError('Client must not use accept or listen for sockets')

            if 'SOCK_STREAM' in source:  # check that TCP sockets are used
                tcp_found = True

        if not tcp_found:
            raise RuntimeError('Client must use only TCP sockets')

        type.__init__(cls, clsname, bases, clsdict)


class Client(metaclass=ClientVerifierMeta):
    def __init__(self, username):
        self._username = username
        self._socket = socket(AF_INET, SOCK_STREAM)

    def connect(self, server_ip: str, server_port: int):
        self._socket.connect((server_ip, server_port))

    def __del__(self):
        self._socket.close()

    @property
    def username(self):
        return self._username

    def create_presence_message(self):
        presence_message = JimRequest()
        presence_message.set_field('action', 'presence')
        presence_message.set_time()
        presence_message.set_field('user', {'account_name': self._username})
        return presence_message

    def send_data(self, data: bytes) -> int:
        if type(data) is not bytes:
            raise TypeError
        return self._socket.send(data)

    def receive_data(self, size=helpers.TCP_MSG_BUFFER_SIZE) -> bytes:
        if size <= 0:
            raise ValueError
        return self._socket.recv(size)

    def send_message_to_server(self, msg: JimRequest):
        msg_bytes = msg.to_bytes()
        msg_bytes_len = len(msg_bytes)
        bytes_sent = self.send_data(msg_bytes)
        if bytes_sent != msg_bytes_len:
            raise RuntimeError(f'socket.send() returned {bytes_sent}, but expected {msg_bytes_len}')

    def receive_message_from_server(self) -> JimRequest:  # this must be JimResponse later
        received_data = self.receive_data()
        return jim_request_from_bytes(received_data)


if __name__ == '__main__':
    log.info('Client started')
    try:
        args = parse_commandline_args(sys.argv[1:])
        client = Client(username=uuid.uuid4().hex[:8])  # using random username
        print(f'Started client with username {client.username}, mode', 'write' if args.mode_write else 'read')
        client.connect(args.server_ip, args.server_port)
        while True:
            if args.mode_write:
                message = client.create_presence_message()
                print(f'Sending message to server: {message}')
                client.send_message_to_server(message)
                sleep(1)
            else:
                response = client.receive_message_from_server()
                print(f'Received from server: {response}')
    except Exception as e:
        log.critical(str(e))
        raise e
