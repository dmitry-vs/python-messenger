import pytest

from security import *


# tests for create_password_hash()
def test__correct_input__correct_results():
    assert create_password_hash('test') is not None
    assert isinstance(create_password_hash('test'), str)
    assert create_password_hash('test') == create_password_hash('test')
    assert len(create_password_hash('test1')) == len(create_password_hash('test2'))
    assert create_password_hash('test1') != create_password_hash('test2')
    assert create_password_hash('test') != 'test'


def test__empty_or_incorrect_input__raises():
    with pytest.raises(RuntimeError):
        create_password_hash('')
    with pytest.raises(RuntimeError):
        create_password_hash(None)
    with pytest.raises(AttributeError):
        create_password_hash(1)
    with pytest.raises(AttributeError):
        create_password_hash([1, 2, 3])
    with pytest.raises(AttributeError):
        create_password_hash({'key': 'value'})
# end tests for create_password_hash()


# tests for create_auth_token()
def test__values_are_correct():
    assert create_auth_token() is not None
    assert isinstance(create_auth_token(), str)
    assert len(create_auth_token()) == AUTH_TOKEN_LEN * 2
    assert create_auth_token() != create_auth_token()
# end tests for create_auth_token()


test_secret = 'cafecafe'
test_token = 'fefefefe'


# tests for create_auth_digest()
def test__correct_input__correct_output():
    assert create_auth_digest(test_secret, test_token) is not None
    assert isinstance(create_auth_digest(test_secret, test_token), str)


def test__incorrect_input__raises():
    with pytest.raises(BaseException):
        create_auth_digest('not_hex_string', test_token)
    with pytest.raises(BaseException):
        create_auth_digest(test_secret, 'not_hex_string')
    with pytest.raises(RuntimeError):
        create_auth_digest(None, test_token)
    with pytest.raises(RuntimeError):
        create_auth_digest(test_secret, None)
    with pytest.raises(TypeError):
        create_auth_digest(1, test_token)
    with pytest.raises(TypeError):
        create_auth_digest(test_secret, 2)
    with pytest.raises(RuntimeError):
        create_auth_digest('', test_token)
    with pytest.raises(RuntimeError):
        create_auth_digest(test_secret, '')
# end tests for create_auth_digest()


test_digest = create_auth_digest(test_secret, test_token)


# tests for check_auth_digest_equal()
def test__equal_digests__return_true():
    digest2 = create_auth_digest(test_secret, test_token)
    assert check_auth_digest_equal(test_digest, digest2) is True
    assert check_auth_digest_equal(digest2, test_digest) is True


def test__different_digests__return_false():
    another_secret = 'aabbccddeeff'
    another_token = 'ffeeddccbb'
    digest2 = create_auth_digest(another_secret, test_token)
    assert check_auth_digest_equal(test_digest, digest2) is False
    digest3 = create_auth_digest(test_secret, another_token)
    assert check_auth_digest_equal(test_digest, digest3) is False
    digest4 = create_auth_digest(another_secret, another_token)
    assert check_auth_digest_equal(test_digest, digest4) is False
    digest5 = create_auth_digest(test_token, test_secret)
    assert check_auth_digest_equal(test_digest, digest5) is False


def test__input_empty__raises():
    with pytest.raises(TypeError):
        check_auth_digest_equal(None, test_digest)
    with pytest.raises(TypeError):
        check_auth_digest_equal(test_digest, None)
# end tests for check_auth_digest_equal()
