import pytest

from server import parse_commandline_args, Server
from helpers import DEFAULT_SERVER_PORT


# tests for: parse_commandline_args
test_ip = '1.2.3.4'
test_port = '55555'


def test_none_args_set__results_are_default_values():
    args = parse_commandline_args([])
    assert args.listen_address == ''
    assert args.listen_port == DEFAULT_SERVER_PORT


def test_address_arg_set__one_result_is_correct_other_is_default():
    args = parse_commandline_args(['-a', test_ip])
    assert args.listen_address == test_ip
    assert args.listen_port == DEFAULT_SERVER_PORT


def test_port_arg_set__one_result_is_correct_other_is_default():
    args = parse_commandline_args(['-p', test_port])
    assert args.listen_address == ''
    assert args.listen_port == int(test_port)


def test_two_args_set__both_results_are_correct():
    args = parse_commandline_args(['-a', test_ip, '-p', test_port])
    assert args.listen_address == test_ip
    assert args.listen_port == int(test_port)


def test_unknown_args__raises():
    with pytest.raises(SystemExit):
        parse_commandline_args(['-z', 'zzz'])


class TestServer:
    def test__init__no_errors(self):
        Server(':memory:')

    def test__set_settings__correct_settings_no_errors(self):
        test_server = Server(':memory:')
        test_server.set_settings('', int(test_port), clients_limit=1000, timeout=1)
