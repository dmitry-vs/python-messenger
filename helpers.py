import os
from functools import wraps

DEFAULT_SERVER_PORT = 7777
TCP_MSG_BUFFER_SIZE = 1024
DEFAULT_SERVER_IP = '127.0.0.1'
SERVER_SOCKET_TIMEOUT = 0.2
CLIENTS_COUNT_LIMIT = 100
APP_NAME = 'messenger'
SERVER_LOGGER_NAME = f'{APP_NAME}.server'
CLIENT_LOGGER_NAME = f'{APP_NAME}.client'


def get_this_script_full_dir():
    return os.path.dirname(os.path.realpath(__file__))


# decorator for function call logging
def log_func_call(logger):
    def log_func_call_decorator(func):
        @wraps(func)
        def log_func_call_decorated(*args, **kwargs):
            ret = func(*args, **kwargs)
            logger.info(f'Called function {func.__name__} with parameters: {args} {kwargs}, returned: {ret}')
            return ret
        return log_func_call_decorated
    return log_func_call_decorator
