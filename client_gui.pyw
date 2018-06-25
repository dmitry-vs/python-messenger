import sys
from PyQt5 import QtWidgets, QtGui
import os
import traceback
import logging

import client_pyqt
from client import Client
import helpers
import log_confing

log = logging.getLogger(helpers.CLIENT_LOGGER_NAME)


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
        self.server_ip = None
        self.server_port = None

        # connect slots
        self.ui.pushButton_connect.clicked.connect(self.connect_click)
        self.ui.pushButton_add_contact.clicked.connect(self.add_contact_click)
        self.ui.pushButton_delete_contact.clicked.connect(self.delete_contact_click)
        self.ui.pushButton_send.clicked.connect(self.send_message_click)
        self.ui.listWidget_contacts.itemDoubleClicked.connect(self.contact_double_clicked)

    def print_info(self, info: str):
        current_text = self.ui.textBrowser_service_info.toPlainText()
        new_text = info if not current_text else f'{current_text}\n{info}'
        self.ui.textBrowser_service_info.setText(new_text)
        self.ui.textBrowser_service_info.moveCursor(QtGui.QTextCursor.End)

    def clear_state(self):
        self.client = None
        self.username = None
        self.server_ip = None
        self.server_port = None

    def connect_click(self):
        # check already connected
        if self.client:
            try:
                self.client.check_connection()
                self.print_info('Already connected')
                return
            except:  # connection lost, need to make new one
                self.print_info(traceback.format_exc())

        # read input values
        username = self.ui.lineEdit_username.text()
        server_ip = self.ui.lineEdit_server_ip.text()
        server_port_str = self.ui.lineEdit_server_port.text()
        if not username or not server_ip or not server_port_str:
            self.print_info('Error: user name, server ip and server port cannot be empty')
            return

        # create client and connect to server, update contacts
        try:
            server_port = int(server_port_str)
            self.username = username
            storage_file = os.path.join(helpers.get_this_script_full_dir(), f'{self.username}.sqlite')
            self.server_ip = server_ip
            self.server_port = server_port
            self.client = Client(self.username, storage_file)
            self.print_info(f'Connecting to server {self.server_ip} on port {str(self.server_port)}...')
            self.client.connect(self.server_ip, self.server_port)
            self.print_info('Connected')
            self.ui.label_username_val.setText(self.username)
            self.ui.label_server_ip_val.setText(self.server_ip)
            self.ui.label_server_port_val.setText(str(self.server_port))
            self.client.update_contacts_from_server()
            self.update_contacts_widget()
        except:
            self.print_info(traceback.format_exc())
            self.clear_state()

    def update_contacts_widget(self):
        contacts = self.client.get_current_contacts()
        self.ui.listWidget_contacts.clear()
        for contact in contacts:
            self.ui.listWidget_contacts.addItem(QtWidgets.QListWidgetItem(contact))

    def add_contact_click(self):
        try:
            login = self.ui.lineEdit_add_contact.text()
            self.client.add_contact_on_server(login)
            self.client.update_contacts_from_server()
            self.update_contacts_widget()
        except BaseException as e:
            self.print_info(f'Error: {str(e)}')

    def delete_contact_click(self):
        try:
            login = self.ui.listWidget_contacts.selectedItems()[0].text()
            self.client.delete_contact_on_server(login)
            self.client.update_contacts_from_server()
            self.update_contacts_widget()
            self.clear_messages_widget()
        except BaseException as e:
            self.print_info(f'Error: {str(e)}')

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
        except:
            self.print_info(traceback.format_exc())

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

    def contact_double_clicked(self):
        login = self.ui.listWidget_contacts.selectedItems()[0].text()
        self.update_messages_widget(login)

    def clear_messages_widget(self):
        self.ui.textBrowser_messages.clear()


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
