import pytest

from client import parse_commandline_args, Client
import helpers
from jim import JimRequest


# tests for: parse_commandline_args
test_ip = '1.2.3.4'
test_port = '1234'
test_user = 'TestClientUserName'


def test_none_args_set__correct_default_values():
    test = parse_commandline_args([])
    assert test.server_ip == helpers.DEFAULT_SERVER_IP
    assert test.server_port == helpers.DEFAULT_SERVER_PORT
    assert test.user_name == helpers.DEFAULT_CLIENT_LOGIN


def test_sever_set__correct_server_others_default():
    test = parse_commandline_args(['-s', test_ip])
    assert test.server_ip == test_ip
    assert test.server_port == helpers.DEFAULT_SERVER_PORT
    assert test.user_name == helpers.DEFAULT_CLIENT_LOGIN


def test_port_set__correct_port_others_default():
    test = parse_commandline_args(['-p', test_port])
    assert test.server_ip == helpers.DEFAULT_SERVER_IP
    assert test.server_port == int(test_port)
    assert test.user_name == helpers.DEFAULT_CLIENT_LOGIN


def test_user_name_set__correct_value_others_default():
    test = parse_commandline_args(['-u', test_user])
    assert test.server_ip == helpers.DEFAULT_SERVER_IP
    assert test.server_port == helpers.DEFAULT_SERVER_PORT
    assert test.user_name == test_user


class TestClient:
    test_username = helpers.DEFAULT_CLIENT_LOGIN

    @staticmethod
    def socket_send_mock(self, data):
        return len(data)

    @staticmethod
    def socket_recv_mock(self, size):
        return b'\xff' * size

    def setup(self):
        self.test_client = Client(self.test_username, ':memory:')

    def test__init_and_del__do_not_raise(self):
        Client(self.test_username, ':memory:')

    def test__send_data__test_data_not_empty__return_data_len(self, monkeypatch):
        test_data = b'test_data'
        monkeypatch.setattr('socket.socket.send', self.socket_send_mock)
        assert self.test_client.send_data(test_data) == len(test_data)

    def test__send_data__data_empty__return_zero(self, monkeypatch):
        monkeypatch.setattr('socket.socket.send', self.socket_send_mock)
        assert self.test_client.send_data(b'') == 0

    def test__send_data__data_has_wrong_type__raises_typeerror(self, monkeypatch):
        monkeypatch.setattr('socket.socket.send', self.socket_send_mock)
        with pytest.raises(Exception):
            self.test_client.send_data([1, 2, 3])

    def test__receive_data__size_positive__correct_number_of_bytes_received(self, monkeypatch):
        monkeypatch.setattr('socket.socket.recv', self.socket_recv_mock)
        test_len = 150
        assert len(self.test_client.receive_data(test_len)) == test_len

    def test__receive_data__size_not_positive__raises_valueerror(self, monkeypatch):
        monkeypatch.setattr('socket.socket.recv', self.socket_recv_mock)
        with pytest.raises(ValueError):
            self.test_client.receive_data(0)
        with pytest.raises(ValueError):
            self.test_client.receive_data(-123)

    def test__send_message_to_server__correct_message__no_errors(self, monkeypatch):
        monkeypatch.setattr('socket.socket.send', self.socket_send_mock)
        test_message = JimRequest()
        test_message.set_field('test_key', 'test_val')
        self.test_client.send_message_to_server(test_message)

    def test__send_message_to_server__incorrect_input_type_raises(self):
        with pytest.raises(AttributeError):
            self.test_client.send_message_to_server([1, 2, 3])
