import pytest
import sqlite3

from storage import DBStorageServer


class TestDBStorageServer:
    test_db = ':memory:'
    clients_table_name = 'Clients'
    contacts_table_name = 'ClientContacts'
    test_login = 'TestLogin'
    test_time = 123456
    test_ip = '1.2.3.4'
    test_info = 'test_info'
    test_second_login = 'TestLogin2'

    def setup(self):
        self.storage = DBStorageServer(self.test_db)
        self.conn = self.storage.conn
        self.cursor = self.conn.cursor()

    def test__init__tables_created(self):
        self.cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        table_names = [t[0] for t in self.cursor.fetchall()]
        assert self.clients_table_name in table_names
        assert self.contacts_table_name in table_names

    def test__get_client_id__client_exists__return_correct_id(self):
        self.cursor.execute(f'INSERT INTO {self.clients_table_name} VALUES (NULL, ?, NULL, NULL, NULL)', (self.test_login,))
        self.conn.commit()
        actual = self.storage.get_client_id(self.test_login)
        assert actual == 1

    def test__get_client_id__no_such_client__return_none(self):
        assert self.storage.get_client_id(self.test_login) is None

    def test__get_client_id___input_none_or_empty__return_none(self):
        assert self.storage.get_client_id(None) is None
        assert self.storage.get_client_id('') is None

    def test__get_client_id__input_collection__raises(self):
        with pytest.raises(sqlite3.Error):
            self.storage.get_client_id([1, 2, 3])
        with pytest.raises(sqlite3.Error):
            self.storage.get_client_id({})

    def test__add_new_client__correct_input__can_find_client_by_login(self):
        self.storage.add_new_client(self.test_login)
        assert self.storage.get_client_id(self.test_login) == 1

    def test__add_new_client__already_exists__raises(self):
        with pytest.raises(sqlite3.Error):
            self.storage.add_new_client(self.test_login)
            self.storage.add_new_client(self.test_login)

    def test__add_new_client__login_none_or_empty__raises(self):
        with pytest.raises(ValueError):
            self.storage.add_new_client(None)
        with pytest.raises(ValueError):
            self.storage.add_new_client('')

    def test__add_new_client__login_not_str__raises(self):
        with pytest.raises(sqlite3.Error):
            self.storage.add_new_client([1, 2])
        with pytest.raises(ValueError):
            self.storage.add_new_client({})

    def test__update_client__client_exists__correct_parameters_in_table(self):
        self.storage.add_new_client(self.test_login)
        client_id = self.storage.get_client_id(self.test_login)

        self.storage.update_client(client_id, self.test_time, self.test_ip, self.test_info)
        self.cursor.execute('SELECT login, info, last_connect_time, last_connect_ip FROM Clients WHERE id == ?',
                            (client_id,))
        actual_values = self.cursor.fetchall()
        assert actual_values[0] == (self.test_login, self.test_info, self.test_time, self.test_ip)

    def test__update_client__info_is_none__correct_parameters_in_table(self):
        self.storage.add_new_client(self.test_login)
        client_id = self.storage.get_client_id(self.test_login)

        self.storage.update_client(client_id, self.test_time, self.test_ip)

        self.cursor.execute('SELECT login, info, last_connect_time, last_connect_ip FROM Clients WHERE id == ?',
                            (client_id,))
        actual_values = self.cursor.fetchall()
        assert actual_values[0] == (self.test_login, None, self.test_time, self.test_ip)

    def test__add_client_to_contacts__client_not_in_contacts__client_added(self):
        self.storage.add_new_client(self.test_login)
        self.storage.add_new_client(self.test_second_login)
        first_client_id = self.storage.get_client_id(self.test_login)
        second_client_id = self.storage.get_client_id(self.test_second_login)

        self.storage.add_client_to_contacts(first_client_id, second_client_id)

        self.cursor.execute('SELECT COUNT() FROM `ClientContacts` WHERE `owner_id` == ? AND `contact_id` == ?;',
                            (first_client_id, second_client_id))
        assert self.cursor.fetchall()[0][0] == 1

    def test__add_client_to_contacts__client_already_in_contacts__raises(self):
        self.storage.add_new_client(self.test_login)
        self.storage.add_new_client(self.test_second_login)
        first_client_id = self.storage.get_client_id(self.test_login)
        second_client_id = self.storage.get_client_id(self.test_second_login)
        self.storage.add_client_to_contacts(first_client_id, second_client_id)

        with pytest.raises(sqlite3.Error):
            self.storage.add_client_to_contacts(first_client_id, second_client_id)

    def test__add_client_to_contacts__incorrect_input__raises(self):
        with pytest.raises(sqlite3.Error):
            self.storage.add_client_to_contacts('qwerty', 'asdfgh')

    def test__check_client_in_contacts__client_in_contacts__return_true(self):
        self.storage.add_new_client(self.test_login)
        self.storage.add_new_client(self.test_second_login)
        first_client_id = self.storage.get_client_id(self.test_login)
        second_client_id = self.storage.get_client_id(self.test_second_login)
        self.storage.add_client_to_contacts(first_client_id, second_client_id)

        assert self.storage.check_client_in_contacts(first_client_id, second_client_id) is True

    def test__check_client_in_contacts__client_not_in_contacts__return_false(self):
        self.storage.add_new_client(self.test_login)
        self.storage.add_new_client(self.test_second_login)
        first_client_id = self.storage.get_client_id(self.test_login)
        second_client_id = self.storage.get_client_id(self.test_second_login)

        assert self.storage.check_client_in_contacts(first_client_id, second_client_id) is False

    def test__check_client_in_contacts__input_incorrect__return_false(self):
        assert self.storage.check_client_in_contacts('qwerty', 'asdfgh') is False
        assert self.storage.check_client_in_contacts(None, None) is False
