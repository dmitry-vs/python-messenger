import os
import subprocess
from time import sleep

from helpers import get_this_script_full_dir


if __name__ == '__main__':
    client_script_name = os.path.join(get_this_script_full_dir(), 'client.py')

    start_client_readmode_command = f'python "{client_script_name}"'
    start_client_writemode_command = f'{start_client_readmode_command} -w'

    process_pair_count = 5

    for _ in range(0, process_pair_count):
        sleep(0.33)
        subprocess.Popen(start_client_readmode_command, creationflags=subprocess.CREATE_NEW_CONSOLE)
        sleep(0.33)
        subprocess.Popen(start_client_writemode_command, creationflags=subprocess.CREATE_NEW_CONSOLE)
