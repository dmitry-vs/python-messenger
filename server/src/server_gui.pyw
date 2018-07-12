import sys
from PyQt5 import QtWidgets, QtGui
from PyQt5.QtCore import QObject, QThread, pyqtSignal, pyqtSlot
import os
import traceback
import logging
import datetime

import server_pyqt
from server import Server
import helpers
from storage import DBStorageServer
from security import create_password_hash
import log_confing

log = logging.getLogger(helpers.CLIENT_LOGGER_NAME)


class ServerMonitor(QObject):
    gotPrintStr = pyqtSignal(str)

    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self._print_queue = None

    def set_queue(self, queue):
        self._print_queue = queue

    def check_new_data(self):
        while True:
            if self._print_queue:
                text = self._print_queue.get()
                if text is None:
                    return
                self.gotPrintStr.emit(text)


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, parent=None):
        QtWidgets.QWidget.__init__(self, parent)
        self.ui = server_pyqt.Ui_MainWindow()
        self.ui.setupUi(self)
        self.server = None
        self.listen_ip = None
        self.listen_port = None
        self.storage_name = os.path.join(helpers.get_this_script_full_dir(), 'server.sqlite')
        self.storage = DBStorageServer(self.storage_name)

        # connect slots
        self.ui.pushButton_start_server.clicked.connect(self.start_server_click)
        self.ui.pushButton_stop_server.clicked.connect(self.stop_server_click)
        self.ui.pushButton_add_new_client.clicked.connect(self.add_new_client_click)

        # create monitor and thread
        self.monitor = ServerMonitor(self)
        self.monitor_thread = QThread()
        self.monitor.moveToThread(self.monitor_thread)
        self.monitor.gotPrintStr.connect(self.new_print_data)
        self.monitor_thread.started.connect(self.monitor.check_new_data)

        # setup table widget parameters
        header = self.ui.tableWidget_clients.horizontalHeader()
        header.setSectionResizeMode(0, QtWidgets.QHeaderView.Stretch)
        header.setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QtWidgets.QHeaderView.Stretch)
        self.update_clients_table()

    @pyqtSlot(str)
    def new_print_data(self, text: str):
        if text.startswith('Client disconnected') or '"action": "get_contacts"' in text:
            self.update_clients_table()
        self.print_info(text)

    def update_clients_table(self):
        current_clients = self.storage.get_clients()
        self.ui.tableWidget_clients.setRowCount(len(current_clients))
        for index, client in enumerate(current_clients):
            self.ui.tableWidget_clients.setItem(index, 0, QtWidgets.QTableWidgetItem(client[0]))
            last_time = datetime.datetime.fromtimestamp(client[1]).strftime('%Y-%m-%d %H:%M:%S') if client[1] else None
            self.ui.tableWidget_clients.setItem(index, 1, QtWidgets.QTableWidgetItem(last_time))
            self.ui.tableWidget_clients.setItem(index, 2, QtWidgets.QTableWidgetItem((client[2])))

    def add_new_client_click(self):
        try:
            client_login = self.ui.lineEdit_add_new_client_login.text()
            client_password = self.ui.lineEdit_add_new_client_password.text()
            if not client_password or not client_password:
                self.print_info('Login and password must be non-empty')
                return
            if self.storage.check_client_exists(client_login):
                self.print_info(f'Client with this login already exists: {client_login}')
                return
            self.storage.add_client(client_login, create_password_hash(client_password))
            self.print_info(f'Client added: {client_login}')
            self.update_clients_table()
        except:
            self.print_info(traceback.format_exc())

    def start_server_click(self):
        try:
            if self.server:
                self.print_info('Already started')
                return
            self.print_info('Starting server')
            self.listen_ip = self.ui.lineEdit_ip.text()
            self.listen_port = int(self.ui.lineEdit_port.text())
            self.server = Server(self.listen_ip, self.listen_port, self.storage_name)
            self.server.start()
            self.monitor.set_queue(self.server.print_queue)
            self.monitor_thread.start()
            self.set_server_status_started(True)
            self.update_clients_table()
        except:
            self.print_info(traceback.format_exc())

    def stop_server_click(self):
        try:
            if not self.server:
                self.print_info('Not running')
                return
            self.print_info('Stopping server')
            self.server.print_queue.put(None)
            self.monitor_thread.terminate()
            self.server.close_server()
            self.server = None
            self.set_server_status_started(False)
            self.ui.tableWidget_clients.clearContents()
            self.ui.lineEdit_add_new_client_login.clear()
            self.ui.lineEdit_add_new_client_password.clear()
        except:
            self.print_info(traceback.format_exc())

    def print_info(self, info: str):
        current_text = self.ui.textBrowser_service_info.toPlainText()
        new_text = info if not current_text else f'{current_text}\n{info}'
        self.ui.textBrowser_service_info.setText(new_text)
        self.ui.textBrowser_service_info.moveCursor(QtGui.QTextCursor.End)

    def set_server_status_started(self, state: bool):
        self.ui.label_status_value.setText('Started' if state else 'Not started')


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
