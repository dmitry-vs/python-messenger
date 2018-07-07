import sys
from PyQt5 import QtWidgets, QtGui
from PyQt5.QtCore import QObject, QThread, pyqtSignal, pyqtSlot
import os
import logging

import client_pyqt
from client import Client
import helpers
from jim import request_from_bytes
import log_confing

log = logging.getLogger(helpers.CLIENT_LOGGER_NAME)

ERROR_FORMAT = 'Error: {}'


class ClientMonitor(QObject):
    gotUserMessage = pyqtSignal(bytes)

    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self._user_messages_queue = None

    def set_queue(self, queue):
        self._user_messages_queue = queue

    def check_new_messages(self):
        while True:
            if self._user_messages_queue:
                msg = self._user_messages_queue.get()
                self.gotUserMessage.emit(msg.to_bytes())


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, parent=None):
        QtWidgets.QWidget.__init__(self, parent)
        self.ui = client_pyqt.Ui_MainWindow()
        self.ui.setupUi(self)
        self.ui.label_username_val.setText('')
        self.ui.label_server_ip_val.setText('')
        self.ui.label_server_port_val.setText('')
        self.client = None
        self.username = None
        self.password = None
        self.server_ip = None
        self.server_port = None

        # connect slots
        self.ui.pushButton_connect.clicked.connect(self.connect_click)
        self.ui.pushButton_disconnect.clicked.connect(self.disconnect_click)
        self.ui.pushButton_add_contact.clicked.connect(self.add_contact_click)
        self.ui.pushButton_delete_contact.clicked.connect(self.delete_contact_click)
        self.ui.pushButton_send.clicked.connect(self.send_message_click)
        self.ui.listWidget_contacts.itemClicked.connect(self.contact_clicked)

        # create monitor and thread
        self.monitor = ClientMonitor(self)
        self.thread = QThread()
        self.monitor.moveToThread(self.thread)
        self.monitor.gotUserMessage.connect(self.new_message_received)
        self.thread.started.connect(self.monitor.check_new_messages)

    @pyqtSlot(bytes)
    def new_message_received(self, msg_bytes):
        msg = request_from_bytes(msg_bytes)
        login = msg.datadict['from']
        text = msg.datadict['message']
        if not self.client.storage.get_contact_id(login):
            self.client.add_contact_on_server(login)
            self.client.update_contacts_from_server()
            self.update_contacts_widget()
        self.client.storage.add_message(login, text, True)
        if login == self.get_current_contact():
            self.update_messages_widget(login)

    def print_info(self, info: str):
        current_text = self.ui.textBrowser_service_info.toPlainText()
        new_text = info if not current_text else f'{current_text}\n{info}'
        self.ui.textBrowser_service_info.setText(new_text)
        self.ui.textBrowser_service_info.moveCursor(QtGui.QTextCursor.End)

    def clear_state(self):
        self.monitor.set_queue(None)
        self.client.close_client()
        self.client = None
        self.username = None
        self.password = None
        self.server_ip = None
        self.server_port = None

    def connect_click(self):
        # check already connected
        if self.client:
            try:
                self.client.check_connection()
                self.print_info('Already connected')
                return
            except BaseException as e:  # connection lost, need to make new one
                self.print_info(ERROR_FORMAT.format(str(e)))

        # read input values
        username = self.ui.lineEdit_username.text()
        password = self.ui.lineEdit_password.text()
        server_ip = self.ui.lineEdit_server_ip.text()
        server_port_str = self.ui.lineEdit_server_port.text()
        if not username or not server_ip or not server_port_str:
            self.print_info('Error: user name, server ip and server port cannot be empty')
            return

        # create client and connect to server, update contacts, start monitor
        try:
            server_port = int(server_port_str)
            self.username = username
            self.password = password
            storage_file = os.path.join(helpers.get_this_script_full_dir(), f'{self.username}.sqlite')
            self.server_ip = server_ip
            self.server_port = server_port
            self.client = Client(username=self.username, password=self.password, storage_file=storage_file)
            self.print_info(f'Connecting to server {self.server_ip} on port {str(self.server_port)}...')
            self.client.connect(self.server_ip, self.server_port)
            self.print_info('Connected')
            self.ui.label_username_val.setText(self.username)
            self.ui.label_server_ip_val.setText(self.server_ip)
            self.ui.label_server_port_val.setText(str(self.server_port))
            self.client.update_contacts_from_server()
            self.update_contacts_widget()
            self.monitor.set_queue(self.client.user_messages_queue)
            self.thread.start()
        except BaseException as e:
            self.print_info(ERROR_FORMAT.format(str(e)))
            self.clear_state()

    def clear_parameters_widgets(self):
        self.ui.label_username_val.clear()
        self.ui.label_server_ip_val.clear()
        self.ui.label_server_port_val.clear()

    def disconnect_click(self):
        if not self.client:
            self.print_info('Not connected')
            return
        self.print_info('Disconnecting')
        self.clear_state()
        self.clear_parameters_widgets()
        self.clear_messages_widget()
        self.clear_contacts_widget()

    def clear_contacts_widget(self):
        self.ui.listWidget_contacts.clear()

    def update_contacts_widget(self):
        contacts = self.client.get_current_contacts()
        self.clear_contacts_widget()
        for contact in contacts:
            self.ui.listWidget_contacts.addItem(QtWidgets.QListWidgetItem(contact))

    def add_contact_click(self):
        try:
            login = self.ui.lineEdit_add_contact.text()
            self.client.add_contact_on_server(login)
            self.client.update_contacts_from_server()
            self.update_contacts_widget()
        except BaseException as e:
            self.print_info(ERROR_FORMAT.format(str(e)))

    def delete_contact_click(self):
        try:
            login = self.ui.listWidget_contacts.selectedItems()[0].text()
            self.client.delete_contact_on_server(login)
            self.client.update_contacts_from_server()
            self.update_contacts_widget()
            self.clear_messages_widget()
        except BaseException as e:
            self.print_info(ERROR_FORMAT.format(str(e)))

    def send_message_click(self):
        try:
            selected_contacts = self.ui.listWidget_contacts.selectedItems()
            if not selected_contacts:
                self.print_info('Contact not selected')
                return
            login = selected_contacts[0].text()
            text = self.ui.textEdit_input.toPlainText()
            if not text:
                self.print_info('Message text cannot be empty')
                return
            self.client.send_message_to_contact(login, text)
            self.update_messages_widget(login)
            self.ui.textEdit_input.clear()
        except BaseException as e:
            self.print_info(ERROR_FORMAT.format(str(e)))

    def format_message(self, login: str, message: dict) -> str:
        """Format message dict returned by Client.get_messages()"""
        login_from = login if message['incoming'] else self.username
        login_to = self.username if message['incoming'] else login
        return f'{login_from} -> {login_to}:\n{message["text"]}'

    def update_messages_widget(self, login: str):
        current_messages = self.client.get_messages(login)
        messages_widget_text = ''
        for message in current_messages:
            msg_formatted = self.format_message(login, message)
            messages_widget_text = msg_formatted if not messages_widget_text else \
                f'{messages_widget_text}\n{msg_formatted}'
        self.ui.textBrowser_messages.setText(messages_widget_text)
        self.ui.textBrowser_messages.moveCursor(QtGui.QTextCursor.End)

    def contact_clicked(self):
        login = self.get_current_contact()
        self.update_messages_widget(login)

    def get_current_contact(self):
        selected_items = self.ui.listWidget_contacts.selectedItems()
        return self.ui.listWidget_contacts.selectedItems()[0].text() if selected_items else None

    def clear_messages_widget(self):
        self.ui.textBrowser_messages.clear()


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
