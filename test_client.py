import pytest

from client import parse_commandline_args
from helpers import DEFAULT_SERVER_IP, DEFAULT_SERVER_PORT


# tests for: parse_commandline_args
test_ip = '1.2.3.4'
test_port = '1234'


def test_none_args_set__correct_default_values():
    test = parse_commandline_args([])
    assert test.server_ip == DEFAULT_SERVER_IP
    assert test.server_port == DEFAULT_SERVER_PORT
    assert test.mode_write is False


def test_sever_set__correct_server_others_default():
    test = parse_commandline_args(['-s', test_ip])
    assert test.server_ip == test_ip
    assert test.server_port == DEFAULT_SERVER_PORT
    assert test.mode_write is False


def test_port_set__correct_port_others_default():
    test = parse_commandline_args(['-p', test_port])
    assert test.server_ip == DEFAULT_SERVER_IP
    assert test.server_port == int(test_port)
    assert test.mode_write is False


def test_write_mode_set__correct_mode_others_default():
    test = parse_commandline_args(['-w'])
    assert test.server_ip == DEFAULT_SERVER_IP
    assert test.server_port == DEFAULT_SERVER_PORT
    assert test.mode_write is True
