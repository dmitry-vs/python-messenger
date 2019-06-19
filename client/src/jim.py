import json
import time


class JimMessage:
    def __init__(self):
        self._datadict = {}

    def set_field(self, key, val):
        self._datadict[key] = val

    def set_time(self):
        self.set_field('time', str(int(time.time())))

    @property
    def datadict(self):
        return self._datadict

    def to_bytes(self):
        self_json = json.dumps(self._datadict)
        return self_json.encode('utf-8')

    def from_bytes(self, bytedata):
        json_data = bytedata.decode('utf-8')
        self._datadict = json.loads(json_data)

    def __str__(self):
        return json.dumps(self._datadict, indent=1)

    def __eq__(self, other):
        return self._datadict == other.datadict


class JimRequest(JimMessage):
    def __init__(self, action=None):
        super().__init__()
        self._action = None
        if action is not None:
            self.action = action

    @property
    def action(self):
        return self._action

    @action.setter
    def action(self, value: str):
        self._action = value
        self.set_field('action', self._action)

    def from_bytes(self, bytedata):
        super().from_bytes(bytedata)
        if 'action' in self._datadict:
            self._action = self._datadict['action']


def request_from_bytes(bytedata: bytes) -> JimRequest:
    ret = JimRequest()
    ret.from_bytes(bytedata)
    return ret


class JimResponse(JimMessage):
    def __init__(self, response_code=None):
        super().__init__()
        self._response = None
        if response_code is not None:
            self.response = response_code

    @property
    def response(self):
        return self._response

    @response.setter
    def response(self, value: int):
        self._response = value
        self.set_field('response', self._response)

    def from_bytes(self, bytedata):
        super().from_bytes(bytedata)
        if 'response' in self._datadict:
            self._response = self._datadict['response']


def response_from_bytes(bytedata: bytes) -> JimResponse:
    ret = JimResponse()
    ret.from_bytes(bytedata)
    return ret


def presence_request(username: str) -> JimRequest:
    message = JimRequest()
    message.set_field('action', 'presence')
    message.set_time()
    message.set_field('user', {'account_name': username})
    return message


def get_contacts_request() -> JimRequest:
    message = JimRequest()
    message.set_field('action', 'get_contacts')
    message.set_time()
    return message


def add_contact_request(login: str) -> JimRequest:
    message = JimRequest()
    message.set_field('action', 'add_contact')
    message.set_field('user_id', login)
    message.set_time()
    return message


def delete_contact_request(login: str) -> JimRequest:
    message = JimRequest()
    message.set_field('action', 'del_contact')
    message.set_field('user_id', login)
    message.set_time()
    return message


def message_request(login_from: str, login_to: str, text: str) -> JimRequest:
    message = JimRequest()
    message.set_field('action', 'msg')
    message.set_time()
    message.set_field('to', login_to)
    message.set_field('from', login_from)
    message.set_field('encoding', 'utf-8')
    message.set_field('message', text)
    return message


def auth_server_message(auth_token: str) -> JimResponse:
    message = JimResponse(401)
    message.set_field('error', 'Authentication required')
    message.set_field('token', auth_token)
    return message


def auth_client_message(login: str, auth_digest: str) -> JimRequest:
    message = JimRequest()
    message.set_field('action', 'authenticate')
    message.set_time()
    user_data = {'account_name': login, 'password': auth_digest}
    message.set_field('user', user_data)
    return message
