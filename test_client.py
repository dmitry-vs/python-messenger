import pytest

from client import parse_commandline_args


# tests for: parse_commandline_args
def test_too_few_args__raises():
    with pytest.raises(IndexError):
        parse_commandline_args([])


def test_too_many_args__raises():
    with pytest.raises(IndexError):
        parse_commandline_args([1, 1, 1])


def test_value_for_port_is_not_number__raises():
    with pytest.raises(ValueError):
        parse_commandline_args(['test', 'test'])
