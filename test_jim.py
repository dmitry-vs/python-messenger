import pytest

from jim import JimMessage, jim_msg_from_bytes


class TestJimMessageClass:
    test = None

    def setup(self):
        self.test = JimMessage()

    def teardown(self):
        self.test = None

    def test_init__dictionary_empty(self):
        assert len(self.test.datadict) == 0

    def test_setfield__correct_data_added(self):
        testkey, testval = 'testkey', 'testval'
        self.test.set_field(testkey, testval)
        assert self.test.datadict[testkey] == testval

    def test_settime__time_field_added_positive_float(self):
        self.test.set_time()
        time_value = float(self.test.datadict['time'])
        assert time_value > 0

    def test_eq__two_empty_messages_return_true(self):
        assert JimMessage() == JimMessage()

    def test_eq__one_empty_other_not_empty_return_false(self):
        self.test.set_time()
        assert self.test != JimMessage()

    def test_eq__both_not_empty_not_equal_return_false(self):
        test1, test2 = JimMessage(), JimMessage()
        test1.set_field('key1', 'val1')
        test2.set_field('key2', 'val2')
        assert test1 != test2

    def test_eq__both_not_empty_equal_return_true(self):
        test1, test2 = JimMessage(), JimMessage()
        testkey, testval = 'key', 'val'
        test1.set_field(testkey, testval)
        test2.set_field(testkey, testval)
        assert test1 == test2

    def test_tobytes__result_not_empty(self):
        assert len(JimMessage().to_bytes()) > 0

    def test_frombytes__tobytes_then_frombytes_result_the_same(self):
        self.test.set_time()
        test_bytes = self.test.to_bytes()
        decoded = JimMessage()
        decoded.from_bytes(test_bytes)
        assert decoded == self.test

    def test_frombytes__incorrect_binary_data_raises(self):
        baddata = b'\xde\xad\xbe\xef'
        with pytest.raises(UnicodeDecodeError):
            self.test.from_bytes(baddata)


# tests for: jim_msg_from_bytes
def test_incorrect_input__raises():
    baddata = b'\xde\xad\xbe\xef'
    with pytest.raises(UnicodeDecodeError):
        jim_msg_from_bytes(baddata)


def test_correct_input__correct_empty_object_created():
    test = jim_msg_from_bytes(b'{}')
    assert len(test.datadict) == 0


def test_correct_input__correct_not_empty_object_created():
    test = jim_msg_from_bytes(b'{"key":"val"}')
    assert test.datadict['key'] == 'val'
