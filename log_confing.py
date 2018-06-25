import logging.handlers
import os

import helpers

log_format = logging.Formatter('%(asctime)-s %(levelname)-s %(module)-s %(funcName)-s %(message)s')

# logger for server
server_logger_name = helpers.SERVER_LOGGER_NAME
server_log_file = os.path.join(helpers.get_this_script_full_dir(), f'{server_logger_name}.log')
server_log_handler = logging.handlers.TimedRotatingFileHandler(filename=server_log_file, when='D', interval=1, delay=True)
server_log_handler.setFormatter(log_format)
server_logger = logging.getLogger(server_logger_name)
server_logger.setLevel(logging.INFO)
server_logger.addHandler(server_log_handler)

# logger for client
client_logger_name = helpers.CLIENT_LOGGER_NAME
client_log_file = os.path.join(helpers.get_this_script_full_dir(), f'{client_logger_name}.log')
client_log_handler = logging.FileHandler(filename=client_log_file, delay=True)
client_log_handler.setFormatter(log_format)
client_logger = logging.getLogger(client_logger_name)
client_logger.setLevel(logging.DEBUG)
client_logger.addHandler(client_log_handler)
