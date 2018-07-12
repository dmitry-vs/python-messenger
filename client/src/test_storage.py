import pytest
import sqlite3

from storage import DBStorageServer, DBStorageClient


class TestDBStorageServer:
    test_db = ':memory:'
    test_login = 'TestLogin'
    test_time = 123456
    test_ip = '1.2.3.4'
    test_info = 'test_info'
    test_second_login = 'TestLogin2'

    def setup(self):
        self.storage = DBStorageServer(self.test_db)
        self.conn = self.storage.conn
        self.cursor = self.storage.cursor

    def test__init__tables_created(self):
        self.cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        table_names = [t[0] for t in self.cursor.fetchall()]
        assert 'Clients' in table_names
        assert 'ClientContacts' in table_names

    def test__get_client_id__client_exists__return_correct_id(self):
        self.cursor.execute(f'INSERT INTO `Clients` VALUES (NULL, ?, NULL, NULL, NULL)', (self.test_login,))
        self.conn.commit()
        actual = self.storage.get_client_id(self.test_login)
        assert actual == 1

    def test__get_client_id__no_such_client__raises(self):
        with pytest.raises(IndexError):
            self.storage.get_client_id(self.test_login)
        # assert self.storage.get_client_id(self.test_login) is None

    def test__get_client_id___input_none_or_empty__return_none(self):
        with pytest.raises(IndexError):
            self.storage.get_client_id(None)
        with pytest.raises(IndexError):
            self.storage.get_client_id('')

    def test__get_client_id__input_collection__raises(self):
        with pytest.raises(sqlite3.Error):
            self.storage.get_client_id([1, 2, 3])
        with pytest.raises(sqlite3.Error):
            self.storage.get_client_id({})

    def test__add_new_client__correct_input__can_find_client_by_login(self):
        self.storage.add_client(self.test_login)
        assert self.storage.get_client_id(self.test_login) == 1

    def test__add_new_client__already_exists__raises(self):
        with pytest.raises(sqlite3.Error):
            self.storage.add_client(self.test_login)
            self.storage.add_client(self.test_login)

    def test__add_new_client__login_none_or_empty__raises(self):
        with pytest.raises(ValueError):
            self.storage.add_client(None)
        with pytest.raises(ValueError):
            self.storage.add_client('')

    def test__add_new_client__login_not_str__raises(self):
        with pytest.raises(sqlite3.Error):
            self.storage.add_client([1, 2])
        with pytest.raises(ValueError):
            self.storage.add_client({})

    def test__update_client__client_exists__correct_parameters_in_table(self):
        self.storage.add_client(self.test_login)
        client_id = self.storage.get_client_id(self.test_login)

        self.storage.update_client(self.test_login, self.test_time, self.test_ip, self.test_info)
        self.cursor.execute('SELECT login, info, last_connect_time, last_connect_ip FROM Clients WHERE id == ?',
                            (client_id,))
        actual_values = self.cursor.fetchall()
        assert actual_values[0] == (self.test_login, self.test_info, self.test_time, self.test_ip)

    def test__update_client__info_is_none__correct_parameters_in_table(self):
        self.storage.add_client(self.test_login)
        client_id = self.storage.get_client_id(self.test_login)

        self.storage.update_client(self.test_login, self.test_time, self.test_ip)

        self.cursor.execute('SELECT login, info, last_connect_time, last_connect_ip FROM Clients WHERE id == ?',
                            (client_id,))
        actual_values = self.cursor.fetchall()
        assert actual_values[0] == (self.test_login, None, self.test_time, self.test_ip)

    def test__add_client_to_contacts__client_not_in_contacts__client_added(self):
        self.storage.add_client(self.test_login)
        self.storage.add_client(self.test_second_login)
        first_client_id = self.storage.get_client_id(self.test_login)
        second_client_id = self.storage.get_client_id(self.test_second_login)

        self.storage.add_client_to_contacts(self.test_login, self.test_second_login)

        self.cursor.execute('SELECT COUNT() FROM `ClientContacts` WHERE `owner_id` == ? AND `contact_id` == ?;',
                            (first_client_id, second_client_id))
        assert self.cursor.fetchall()[0][0] == 1

    def test__add_client_to_contacts_clients_add_each_other__no_errors(self):
        self.storage.add_client(self.test_login)
        self.storage.add_client(self.test_second_login)
        self.storage.add_client_to_contacts(self.test_login, self.test_second_login)
        self.storage.add_client_to_contacts(self.test_second_login, self.test_login)

    def test__add_client_to_contacts__client_already_in_contacts__raises(self):
        self.storage.add_client(self.test_login)
        self.storage.add_client(self.test_second_login)
        self.storage.add_client_to_contacts(self.test_login, self.test_second_login)
        with pytest.raises(sqlite3.Error):
            self.storage.add_client_to_contacts(self.test_login, self.test_second_login)

    def test__add_client_to_contacts__incorrect_input__raises(self):
        with pytest.raises(IndexError):
            self.storage.add_client_to_contacts(None, {})
        with pytest.raises(sqlite3.InterfaceError):
            self.storage.add_client_to_contacts({}, None)

    def test__check_client_in_contacts__client_in_contacts__return_true(self):
        self.storage.add_client(self.test_login)
        self.storage.add_client(self.test_second_login)
        self.storage.add_client_to_contacts(self.test_login, self.test_second_login)
        assert self.storage.check_client_in_contacts(self.test_login, self.test_second_login) is True

    def test__check_client_in_contacts__client_not_in_contacts__return_false(self):
        self.storage.add_client(self.test_login)
        self.storage.add_client(self.test_second_login)
        assert self.storage.check_client_in_contacts(self.test_login, self.test_second_login) is False

    def test__check_client_in_contacts__incorrect_input__raises(self):
        with pytest.raises(IndexError):
            self.storage.check_client_in_contacts('qwerty', 'asdfgh')
        with pytest.raises(IndexError):
            self.storage.check_client_in_contacts(None, None)


class TestDBStorageClient:
    test_db = ':memory:'
    test_login = 'TestLogin'
    test_second_login = 'TestLogin2'
    test_message = 'Test message'

    def setup(self):
        self.storage = DBStorageClient(self.test_db)
        self.conn = self.storage.conn
        self.cursor = self.storage.cursor

    def test__init__tables_created(self):
        self.cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        table_names = [t[0] for t in self.cursor.fetchall()]
        assert 'Contacts' in table_names
        assert 'Messages' in table_names

    def test__add_new_contact__not_added_yet__correct_row_added(self):
        self.storage.add_contact(self.test_login)
        self.cursor.execute('SELECT `login` FROM `Contacts` WHERE `id` == 1')
        assert self.cursor.fetchall()[0][0] == self.test_login

    def test__add_new_contact__already_added__raises(self):
        self.storage.add_contact(self.test_login)
        with pytest.raises(sqlite3.Error):
            self.storage.add_contact(self.test_login)

    def test__add_new_contact__input_incorrect__raises(self):
        with pytest.raises(sqlite3.Error):
            self.storage.add_contact(None)
        with pytest.raises(sqlite3.Error):
            self.storage.add_contact({})

    def test__get_contact_id__contact_exists__return_correct_value(self):
        self.storage.add_contact(self.test_login)
        assert self.storage.get_contact_id(self.test_login) == 1

    def test__get_contact_id__no_such_contact__return_none(self):
        assert self.storage.get_contact_id(self.test_login) is None

    def test__get_contact_id__input_none__return_none(self):
        assert self.storage.get_contact_id(None) is None

    def test__add_new_message__input_ok_incoming__correct_row_added(self):
        self.storage.add_contact(self.test_login)
        self.storage.add_message(self.test_login, self.test_message, True)
        self.cursor.execute('SELECT * FROM `Messages`')
        result = self.cursor.fetchall()
        assert len(result) == 1
        assert result[0] == (1, 1, int(True), self.test_message)

    def test__add_new_message__input_ok_outcoming__correct_row_added(self):
        self.storage.add_contact(self.test_login)
        self.storage.add_message(self.test_login, self.test_message)
        self.cursor.execute('SELECT * FROM `Messages`')
        result = self.cursor.fetchall()
        assert len(result) == 1
        assert result[0] == (1, 1, int(False), self.test_message)

    def test__add_new_message__input_incorrect__raises(self):
        with pytest.raises(sqlite3.Error):
            self.storage.add_message(None, self.test_message, True)

        self.storage.add_contact(self.test_login)
        with pytest.raises(TypeError):
            self.storage.add_message(1, self.test_message, None)
        with pytest.raises(sqlite3.Error):
            self.storage.add_message(1, None, True)
        with pytest.raises(sqlite3.Error):
            self.storage.add_message(1, None, False)
