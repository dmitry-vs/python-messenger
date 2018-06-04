import json
import time


class JimMessage:
    def __init__(self):
        self.__datadict = {}

    def set_field(self, key, val):
        self.__datadict[key] = val

    def set_time(self):
        self.set_field('time', str(time.time()))

    @property
    def datadict(self):
        return self.__datadict

    def to_bytes(self):
        self_json = json.dumps(self.__datadict)
        return self_json.encode('utf-8')

    def from_bytes(self, bytedata):
        json_data = bytedata.decode('utf-8')
        self.__datadict = json.loads(json_data)

    def __str__(self):
        return json.dumps(self.__datadict, indent=1)

    def __eq__(self, other):
        return self.__datadict == other.datadict


class JimRequest(JimMessage):
    def __init__(self):
        super().__init__()


def jim_request_from_bytes(bytedata: bytes) -> JimRequest:
    ret = JimRequest()
    ret.from_bytes(bytedata)
    return ret


class JimResponse(JimMessage):
    def __init__(self):
        self._response = None
        self._alert = None
        self._error = None
        super().__init__()

    @property
    def response(self):
        return self._response

    @response.setter
    def response(self, value: int):
        self.set_field("response", value)
        self._response = value

    @property
    def alert(self):
        return self._alert

    @alert.setter
    def alert(self, value: str):
        self.set_field("alert", value)
        self._alert = value

    @property
    def error(self):
        return self._error

    @error.setter
    def error(self, value: str):
        self.set_field("error", value)
        self._error = value

    def from_bytes(self, bytedata):
        json_data = bytedata.decode('utf-8')
        dict_data = json.loads(json_data)
        self.response = dict_data["response"]
        alert_key, error_key = "alert", "error"
        if alert_key in dict_data:
            self.alert = dict_data["alert"]
        if error_key in dict_data:
            self.error = dict_data["error"]


def jim_response_from_bytes(bytedata: bytes) -> JimResponse:
    ret = JimResponse()
    ret.from_bytes(bytedata)
    return ret
