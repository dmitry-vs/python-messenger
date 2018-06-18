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
        try:
            return self._cursor.fetchall()[0][0]
        except IndexError:
            return None

    def add_new_client(self, login: str):
        if not login:
            raise ValueError('login cannot be None nor empty')
        self._cursor.execute('INSERT INTO `Clients` VALUES (NULL, ?, NULL, NULL, NULL)', (login,))
        self._conn.commit()

    def update_client(self, client_id: int, connection_time: float, connection_ip: str, info=None):
        self._cursor.execute(
            """
            UPDATE `Clients` SET 
                `info` = ?, 
                `last_connect_time` = ?, 
                `last_connect_ip` = ? 
            WHERE `id` == ?;
            """, (info, connection_time, connection_ip, client_id)
        )
        self._conn.commit()

    def check_client_in_contacts(self, owner_id: int, client_id: int) -> bool:
        self._cursor.execute('SELECT COUNT() FROM `ClientContacts` WHERE `owner_id` == ? AND `contact_id` == ?;',
                       (owner_id, client_id))
        return True if self._cursor.fetchall()[0][0] == 1 else False

    def add_client_to_contacts(self, owner_id: int, client_id: int):
        self._cursor.execute('INSERT INTO `ClientContacts` VALUES (?, ?);', (owner_id, client_id))
        self._conn.commit()


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
            FOREIGN KEY(`contact_id`) REFERENCES `Contacts`(`id`)
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

    def add_message(self, contact_id: int, incoming: bool, text: str):
        self._cursor.execute('INSERT INTO `Messages` VALUES (NULL, ?, ?, ?)', (contact_id, int(incoming), text))
        self._conn.commit()

    def get_contacts(self) -> list:
        self._cursor.execute('SELECT `login` FROM `Contacts`')
        return [item[0] for item in self._cursor.fetchall()]

    def delete_contact(self, login: str):
        self._cursor.execute('DELETE FROM `Contacts` WHERE `login` == ?', (login,))
        self._conn.commit()


class FileStorage:
    pass
