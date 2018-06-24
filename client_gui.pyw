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
        self.storage_file = None
        self.server_ip = None
        self.server_port = None

        # connect slots
        self.ui.pushButton_connect.clicked.connect(self.connect_click)
        self.ui.pushButton_add_contact.clicked.connect(self.add_contact_click)
        self.ui.pushButton_delete_contact.clicked.connect(self.delete_contact_click)
        self.ui.pushButton_send.clicked.connect(self.send_message_click)

    def print_info(self, info: str):
        current_text = self.ui.textBrowser_service_info.toPlainText()
        new_text = info if not current_text else f'{current_text}\n{info}'
        self.ui.textBrowser_service_info.setText(new_text)
        self.ui.textBrowser_service_info.moveCursor(QtGui.QTextCursor.End)

    def connect_click(self):
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
            self.storage_file = os.path.join(helpers.get_this_script_full_dir(), f'{self.username}.sqlite')
            self.server_ip = server_ip
            self.server_port = server_port
            self.client = Client(self.username, self.storage_file)
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
        except BaseException as e:
            self.print_info(f'Error: {str(e)}')

    def send_message_click(self):
        # call client send message
        # print messages history in widget
        pass


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
