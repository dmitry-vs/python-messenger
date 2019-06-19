import os
from functools import wraps
import inspect
import binascii

DEFAULT_SERVER_PORT = 7777
TCP_MSG_BUFFER_SIZE = 1024
DEFAULT_SERVER_IP = '127.0.0.1'
SERVER_SOCKET_TIMEOUT = 0.2
CLIENTS_COUNT_LIMIT = 100
APP_NAME = 'messenger'
SERVER_LOGGER_NAME = f'{APP_NAME}.server'
CLIENT_LOGGER_NAME = f'{APP_NAME}.client'
DEFAULT_CLIENT_LOGIN = 'TestUser'
DEFAULT_CLIENT_PASSWORD = 'TestPassword'


def get_this_script_full_dir():
    return os.path.dirname(os.path.realpath(__file__))


# decorator for function call logging
def log_func_call(logger):
    def log_func_call_decorator(func):
        @wraps(func)
        def log_func_call_decorated(*args, **kwargs):
            ret = func(*args, **kwargs)
            logger.info(f'Called function {func.__name__} with parameters: {args} {kwargs}, returned: {ret}, '
                        f'caller name: {str(inspect.stack()[1][3])}')
            return ret
        return log_func_call_decorated
    return log_func_call_decorator


class Menu:
    def __init__(self, commands: list):
        self._commands = {i + 1: item for i, item in enumerate(commands)}

    def get_command(self, command_index):
        return self._commands[command_index]

    def __str__(self):
        result = '\nChoose command:\n'
        for key, val in self._commands.items():
            result += f'{key}. {val}\n'
        result += '>'
        return result


def bytes_to_hexstring(data: bytes) -> str:
    return binascii.hexlify(data).decode('utf-8')


def hexstring_to_bytes(hexstring: str) -> bytes:
    return binascii.unhexlify(hexstring)
