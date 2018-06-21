import sys
from socket import socket, AF_INET, SOCK_STREAM
import argparse
import logging
import inspect

import helpers
from jim import JimRequest, JimResponse, jim_request_from_bytes, jim_response_from_bytes
from storage import DBStorageClient
import log_confing

log = logging.getLogger(helpers.CLIENT_LOGGER_NAME)

MENU_ITEM_GET_CONTACTS = 'Get contacts'
MENU_ITEM_ADD_CONTACT = 'Add contact'
MENU_ITEM_DELETE_CONTACT = 'Delete contact'
MENU_ITEM_SEND_MESSAGE = 'Send message'


def parse_commandline_args(cmd_args):
    parser = argparse.ArgumentParser()
    parser.add_argument('-s', dest='server_ip', type=str, default=helpers.DEFAULT_SERVER_IP, help='server ip, default 127.0.0.1')
    parser.add_argument('-p', dest='server_port', type=int, default=helpers.DEFAULT_SERVER_PORT, help='server port, default 7777')
    parser.add_argument('-u', dest='user_name', type=str, default=helpers.DEFAULT_CLIENT_LOGIN, help='client login, default "TestClient"')
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
    def __init__(self, username, storage):
        self.__username = username
        self.__socket = socket(AF_INET, SOCK_STREAM)
        self.__storage = DBStorageClient(storage)

    def connect(self, server_ip: str, server_port: int):
        self.__socket.connect((server_ip, server_port))

    def __del__(self):
        self.__socket.close()

    @property
    def username(self):
        return self.__username

    @property
    def storage(self):
        return self.__storage

    def send_data(self, data: bytes) -> int:
        if type(data) is not bytes:
            raise TypeError
        return self.__socket.send(data)

    def receive_data(self, size=helpers.TCP_MSG_BUFFER_SIZE) -> bytes:
        if size <= 0:
            raise ValueError
        return self.__socket.recv(size)

    def send_message_to_server(self, msg: JimRequest):
        msg_bytes = msg.to_bytes()
        msg_bytes_len = len(msg_bytes)
        bytes_sent = self.send_data(msg_bytes)
        if bytes_sent != msg_bytes_len:
            raise RuntimeError(f'socket.send() returned {bytes_sent}, but expected {msg_bytes_len}')

    def receive_message_from_server(self) -> JimResponse:
        received_data = self.receive_data()
        return jim_response_from_bytes(received_data)

    def create_presence_message(self) -> JimRequest:
        message = JimRequest()
        message.set_field('action', 'presence')
        message.set_time()
        message.set_field('user', {'account_name': self.__username})
        return message

    @staticmethod
    def create_get_contacts_message() -> JimRequest:
        message = JimRequest()
        message.set_field('action', 'get_contacts')
        message.set_time()
        return message

    @staticmethod
    def create_add_contact_message(login: str) -> JimRequest:
        message = JimRequest()
        message.set_field('action', 'add_contact')
        message.set_field('user_id', login)
        message.set_time()
        return message

    @staticmethod
    def create_delete_contact_message(login: str) -> JimRequest:
        message = JimRequest()
        message.set_field('action', 'del_contact')
        message.set_field('user_id', login)
        message.set_time()
        return message

    def get_contacts(self) -> list:
        return self.__storage.get_contacts()

    def update_contacts(self, cont_server: list):
        cont_client = self.get_contacts()
        # if contact in client list, but not in server list - delete from client list
        # if contact in server list, but not in client list - add to client list
        for cont in cont_client:
            if cont not in cont_server:
                self.__storage.delete_contact(cont)
        for cont in contacts_server:
            if cont not in cont_client:
                self.__storage.add_contact(cont)


if __name__ == '__main__':
    log.info('Client started')
    try:
        args = parse_commandline_args(sys.argv[1:])
        client = Client(username=args.user_name, storage=':memory:')
        print(f'Started client with username {client.username}')
        client.connect(args.server_ip, args.server_port)

        # client work logic
        presence_request = client.create_presence_message()
        print('Sending presence message to server...')
        client.send_message_to_server(presence_request)
        presence_response = client.receive_message_from_server()
        if presence_response.datadict['response'] != 200:
            raise RuntimeError(f'Presence: expected 200, received {presence_response.datadict["response"]}')

        while True:
            menu = {
                1: MENU_ITEM_GET_CONTACTS,
                2: MENU_ITEM_ADD_CONTACT,
                3: MENU_ITEM_DELETE_CONTACT,
                4: MENU_ITEM_SEND_MESSAGE
            }

            menu_str = f'''
Choose operation:
1. {MENU_ITEM_GET_CONTACTS}
2. {MENU_ITEM_ADD_CONTACT}
3. {MENU_ITEM_DELETE_CONTACT}
4. {MENU_ITEM_SEND_MESSAGE}
>'''
            user_choice = None
            try:
                user_choice = int(input(menu_str))
            except:
                continue

            if menu[user_choice] == MENU_ITEM_GET_CONTACTS:
                request = client.create_get_contacts_message()
                client.send_message_to_server(request)
                response = client.receive_message_from_server()
                if response.datadict['response'] != 202:
                    raise RuntimeError(f'Get contacts: expected 202, received: {response.datadict["response"]}')

                contacts_server = []
                for _ in range(0, response.datadict['quantity']):
                    contact_message = client.receive_message_from_server()
                    if contact_message.datadict['action'] != 'contact_list':
                        raise RuntimeError(f'Get contacts: expected action "contact_list", received: {contact_message.datadict["action"]}')
                    if contact_message.datadict['nickname'] not in contacts_server:
                        contacts_server.append(contact_message.datadict['nickname'])

                client.update_contacts(contacts_server)
            elif menu[user_choice] == MENU_ITEM_ADD_CONTACT:
                contact_login = input('Print login of user to add: >')
                if not contact_login:
                    raise RuntimeError('Login cannot be empty')
                request = client.create_add_contact_message(contact_login)
                client.send_message_to_server(request)
                response = client.receive_message_from_server()
                if response.datadict['response'] != 200:
                    raise RuntimeError(f'Add contact: expected response 200, received: {response.datadict["response"]}')
            elif menu[user_choice] == MENU_ITEM_DELETE_CONTACT:
                contact_login = input('Print login of user to delete: >')
                if not contact_login:
                    raise RuntimeError('Login cannot be empty')
                request = client.create_delete_contact_message(contact_login)
                client.send_message_to_server(request)
                response = client.receive_message_from_server()
                if response.datadict['response'] != 200:
                    raise RuntimeError(f'Delete contact: expected response 200, received: response.datadict["response"]')
            elif menu[user_choice] == MENU_ITEM_SEND_MESSAGE:
                contacts = client.get_contacts()
                for contact, index in enumerate(client.get_contacts()):
                    print(f'{index + 1}. {contact}')
            else:
                continue
    except Exception as e:
        log.critical(str(e))
        raise e
