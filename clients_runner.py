import os
import subprocess

from helpers import get_this_script_full_dir


if __name__ == '__main__':
    client_script_name = os.path.join(get_this_script_full_dir(), 'client.py')

    start_client_readmode_command = f'python "{client_script_name}"'
    start_client_writemode_command = f'{start_client_readmode_command} -w'

    subprocess.Popen(start_client_readmode_command, creationflags=subprocess.CREATE_NEW_CONSOLE)
    subprocess.Popen(start_client_writemode_command, creationflags=subprocess.CREATE_NEW_CONSOLE)
