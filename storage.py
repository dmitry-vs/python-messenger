import sqlite3


class DBStorageServer:
    def __init__(self, database):
        # connect to database, create it if not exists,
        # create db schema if not exists (tables Clients, ClientContacts)
        self.__conn = sqlite3.connect(database)
        cursor = self.__conn.cursor()
        cursor.executescript('''
        CREATE TABLE IF NOT EXISTS `Clients`(
            `id`    INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE, 
            `login` TEXT NOT NULL UNIQUE, 
            `info`  TEXT,
            `last_connect_time`	INTEGER,
            `last_connect_ip`	TEXT
        );
        ''')
        cursor.execute('PRAGMA foreign_keys = ON;')
        cursor.executescript('''
        CREATE TABLE IF NOT EXISTS `ClientContacts` (
            `owner_id`	    INTEGER,
            `contact_id`	INTEGER,
            PRIMARY KEY(`owner_id`,`contact_id`),
            FOREIGN KEY(`owner_id`) REFERENCES `Clients`(`id`),
            FOREIGN KEY(`contact_id`) REFERENCES `Clients`(`id`)
        );
        ''')
        self.__conn.commit()

    @property
    def conn(self):
        return self.__conn

    def get_client_id(self, login: str):
        """ Returns client id by login from Clients table, or None if there is no such client """
        cursor = self.__conn.cursor()
        cursor.execute('SELECT `id` FROM `Clients` WHERE `login` == ?', (login,))
        try:
            return cursor.fetchall()[0][0]
        except IndexError:
            return None

    def add_new_client(self, login: str):
        if not login:
            raise ValueError('login cannot be None nor empty')
        cursor = self.__conn.cursor()
        cursor.execute('INSERT INTO `Clients` VALUES (NULL, ?, NULL, NULL, NULL)', (login,))
        self.__conn.commit()

    def update_client(self, client_id: int, connection_time: float, connection_ip: str, info=None):
        cursor = self.__conn.cursor()
        cursor.execute(
            """
            UPDATE `Clients` SET 
                `info` = ?, 
                `last_connect_time` = ?, 
                `last_connect_ip` = ? 
            WHERE `id` == ?;
            """, (info, connection_time, connection_ip, client_id)
        )
        self.__conn.commit()

    def check_client_in_contacts(self, owner_id: int, client_id: int) -> bool:
        cursor = self.__conn.cursor()
        cursor.execute('SELECT COUNT() FROM `ClientContacts` WHERE `owner_id` == ? AND `contact_id` == ?;',
                       (owner_id, client_id))
        return True if cursor.fetchall()[0][0] == 1 else False

    def add_client_to_contacts(self, owner_id: int, client_id: int):
        cursor = self.__conn.cursor()
        cursor.execute('INSERT INTO `ClientContacts` VALUES (?, ?);', (owner_id, client_id))
        self.__conn.commit()

    def __del__(self):
        self.__conn.close()


class DBStorageClient:
    pass


class FileStorage:
    pass
