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


def jim_msg_from_bytes(bytedata):
    ret = JimMessage()
    ret.from_bytes(bytedata)
    return ret
