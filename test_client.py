import pytest
import socket

from client import parse_commandline_args, send_data, receive_data
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


# tests for: send_data
test_sock = socket.socket()


def socket_send_mock(self, data):
    return len(data)


def test_data_not_empty__return_data_len(monkeypatch):
    test_data = b'test_data'
    monkeypatch.setattr('socket.socket.send', socket_send_mock)
    assert send_data(test_sock, test_data) == len(test_data)


def test_data_empty__return_zero(monkeypatch):
    monkeypatch.setattr('socket.socket.send', socket_send_mock)
    assert send_data(test_sock, b'') == 0


def test_data_has_wrong_type__raises_typeerror(monkeypatch):
    monkeypatch.setattr('socket.socket.send', socket_send_mock)
    with pytest.raises(Exception):
        send_data(test_sock, [1, 2, 3])


# tests for: receive_data
def socket_recv_mock(self, size):
    return b'a' * size


def test_size_positive__correct_number_of_bytes_received(monkeypatch):
    monkeypatch.setattr('socket.socket.recv', socket_recv_mock)
    test_len = 150
    assert len(receive_data(test_sock, test_len)) == test_len


def test_size_not_positive__raises_valueerror(monkeypatch):
    monkeypatch.setattr('socket.socket.recv', socket_recv_mock)
    with pytest.raises(ValueError):
        receive_data(test_sock, 0)
    with pytest.raises(ValueError):
        receive_data(test_sock, -123)
