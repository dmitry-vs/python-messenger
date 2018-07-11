import sqlite3


class DBStorage:
    def __init__(self, database):
        self._conn = sqlite3.connect(database)
        self._cursor = self._conn.cursor()

    def __del__(self):
        self._conn.close()

    @property
    def conn(self):
        return self._conn

    @property
    def cursor(self):
        return self._cursor


class DBStorageServer(DBStorage):
    def __init__(self, database):
        super().__init__(database)
        self._cursor.executescript('''
        CREATE TABLE IF NOT EXISTS `Clients`(
            `id`    INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE, 
            `login` TEXT NOT NULL UNIQUE, 
            `info`  TEXT,
            `last_connect_time`	INTEGER,
            `last_connect_ip`	TEXT
        );
        ''')
        self._cursor.execute('PRAGMA foreign_keys = ON;')
        self._cursor.executescript('''
        CREATE TABLE IF NOT EXISTS `ClientContacts` (
            `owner_id`	    INTEGER,
            `contact_id`	INTEGER,
            PRIMARY KEY(`owner_id`,`contact_id`),
            FOREIGN KEY(`owner_id`) REFERENCES `Clients`(`id`),
            FOREIGN KEY(`contact_id`) REFERENCES `Clients`(`id`)
        );
        ''')
        self._conn.commit()

    def get_client_id(self, login: str):
        """ Returns client id by login from Clients table, or None if there is no such client """
        self._cursor.execute('SELECT `id` FROM `Clients` WHERE `login` == ?', (login,))
        return self._cursor.fetchall()[0][0]

    def get_clients(self):
        self._cursor.execute(
            '''
            SELECT `login`, `last_connect_time`, `last_connect_ip`
            FROM `Clients`
            ORDER BY `last_connect_time` DESC
            '''
        )
        result = self._cursor.fetchall()
        return result if result else []

    def get_client_hash(self, login: str) -> str:
        self._cursor.execute('SELECT `info` FROM `Clients` WHERE `login` == ?', (login,))
        return self._cursor.fetchall()[0][0]

    def check_client_exists(self, login: str) -> bool:
        try:
            self.get_client_id(login)
            return True
        except IndexError:
            return False

    def add_client(self, login: str, password_hash: str):
        if not login:
            raise ValueError('login cannot be None or empty')
        if not password_hash:
            raise ValueError('password hash cannot be None or empty')
        if self.check_client_exists(login) is True:
            raise RuntimeError(f'client with this login already exists: {login}')
        self._cursor.execute('INSERT INTO `Clients` VALUES (NULL, ?, ?, NULL, NULL)', (login, password_hash))
        self._conn.commit()

    def update_client(self, login: str, connection_time: float, connection_ip: str):
        client_id = self.get_client_id(login)
        self._cursor.execute(
            """
            UPDATE `Clients` SET 
                `last_connect_time` = ?, 
                `last_connect_ip` = ? 
            WHERE `id` == ?;
            """, (connection_time, connection_ip, client_id)
        )
        self._conn.commit()

    def check_client_in_contacts(self, owner_login: str, client_login: str) -> bool:
        owner_id = self.get_client_id(owner_login)
        client_id = self.get_client_id(client_login)
        self._cursor.execute('SELECT COUNT() FROM `ClientContacts` WHERE `owner_id` == ? AND `contact_id` == ?;',
                             (owner_id, client_id))
        return True if self._cursor.fetchall()[0][0] == 1 else False

    def add_client_to_contacts(self, owner_login: str, client_login: str):
        owner_id = self.get_client_id(owner_login)
        client_id = self.get_client_id(client_login)
        self._cursor.execute('INSERT INTO `ClientContacts` VALUES (?, ?);', (owner_id, client_id))
        self._conn.commit()

    def del_client_from_contacts(self, owner_login: str, client_login: str):
        owner_id = self.get_client_id(owner_login)
        client_id = self.get_client_id(client_login)
        self._cursor.execute('DELETE FROM `ClientContacts` WHERE `owner_id` == ? AND `contact_id` == ?',
                             (owner_id, client_id))
        self._conn.commit()

    def get_client_contacts(self, client_login: str) -> list:
        client_id = self.get_client_id(client_login)
        query = '''select `Clients`.login from `ClientContacts` join `Clients` 
        where (`ClientContacts`.contact_id == `Clients`.id and `ClientContacts`.owner_id == ?);'''
        self._cursor.execute(query, (client_id,))
        result = self._cursor.fetchall()
        return [item[0] for item in result] if result is not None else []


class DBStorageClient(DBStorage):
    def __init__(self, database):
        # connect to database, create it if not exists,
        # create db schema if not exists (tables Contacts, Messages)
        super().__init__(database)
        self._cursor.executescript('''
        CREATE TABLE IF NOT EXISTS `Contacts`(
            `id`	INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
            `login`	TEXT NOT NULL UNIQUE
        );
        ''')
        self._cursor.execute('PRAGMA foreign_keys = ON;')
        self._cursor.executescript('''
        CREATE TABLE IF NOT EXISTS `Messages` (
            `id`	INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
            `contact_id`	INTEGER NOT NULL,
            `incoming`	INTEGER NOT NULL,
            `text`	TEXT NOT NULL,
            FOREIGN KEY(`contact_id`) REFERENCES `Contacts`(`id`) ON DELETE CASCADE
        );
        ''')
        self._conn.commit()

    def add_contact(self, login: str):
        self._cursor.execute('INSERT INTO `Contacts` VALUES(NULL, ?)', (login,))
        self._conn.commit()

    def get_contact_id(self, login: str):
        self._cursor.execute('SELECT `id` FROM `Contacts` WHERE `login` == ?', (login,))
        try:
            return self._cursor.fetchall()[0][0]
        except IndexError:
            return None

    def add_message(self, login: str, text: str, incoming: bool=False):
        contact_id = self.get_contact_id(login)
        self._cursor.execute('INSERT INTO `Messages` VALUES (NULL, ?, ?, ?)', (contact_id, int(incoming), text))
        self._conn.commit()

    def get_messages(self, login: str):
        contact_id = self.get_contact_id(login)
        self.cursor.execute('''
        SELECT `text`, `incoming` 
        FROM `Messages` 
        WHERE `contact_id` == ?
        ORDER BY `id`
        ''', (contact_id,))
        return self._cursor.fetchall()

    def get_contacts(self) -> list:
        self._cursor.execute('SELECT `login` FROM `Contacts`')
        return [item[0] for item in self._cursor.fetchall()]

    def delete_contact(self, login: str):
        self._cursor.execute('DELETE FROM `Contacts` WHERE `login` == ?', (login,))
        self._conn.commit()

    def update_contacts(self, server_contacts: list):
        """
        If contact in client list, but not in server list - delete from client list
        If contact in server list, but not in client list - add to client list
        """
        client_contacts = self.get_contacts()
        for contact in client_contacts:
            if contact not in server_contacts:
                self.delete_contact(contact)
        for contact in server_contacts:
            if contact not in client_contacts:
                self.add_contact(contact)


class FileStorage:
    pass
