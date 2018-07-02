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

        # create monitor and thread
        self.monitor = ServerMonitor(self)
        self.thread = QThread()
        self.monitor.moveToThread(self.thread)
        self.monitor.gotPrintStr.connect(self.new_print_data)
        self.thread.started.connect(self.monitor.check_new_data)

    @pyqtSlot(str)
    def new_print_data(self, text: str):
        if text.startswith('Client disconnected'):
            self.update_clients_table()
        self.print_info(text)

    def update_clients_table(self):
        current_clients = self.storage.get_clients()
        self.ui.tableWidget_clients.setRowCount(len(current_clients))
        for index, client in enumerate(current_clients):
            self.ui.tableWidget_clients.setItem(index, 0, QtWidgets.QTableWidgetItem(client[0]))
            last_time = datetime.datetime.fromtimestamp(client[1]).strftime('%Y-%m-%d %H:%M:%S')
            self.ui.tableWidget_clients.setItem(index, 1, QtWidgets.QTableWidgetItem(last_time))
            self.ui.tableWidget_clients.setItem(index, 2, QtWidgets.QTableWidgetItem((client[2])))

    def start_server_click(self):
        try:
            if self.server:
                self.print_info('Already started')
                return
            self.listen_ip = self.ui.lineEdit_ip.text()
            self.listen_port = int(self.ui.lineEdit_port.text())
            self.server = Server(self.listen_ip, self.listen_port, self.storage_name)
            self.monitor.set_queue(self.server.print_queue)
            self.thread.start()
            self.server.start()
            self.set_server_status_started(True)
            self.update_clients_table()
        except:
            print(traceback.format_exc())

    def stop_server_click(self):
        try:
            if not self.server:
                self.print_info('Not running')
                return
            self.server.close_server()
            self.server = None
            self.set_server_status_started(False)
            self.ui.tableWidget_clients.clear()
        except:
            print(traceback.format_exc())

    def print_info(self, info: str):
        current_text = self.ui.textBrowser_service_info.toPlainText()
        new_text = info if not current_text else f'{current_text}\n{info}'
        self.ui.textBrowser_service_info.setText(new_text)
        self.ui.textBrowser_service_info.moveCursor(QtGui.QTextCursor.End)

    def set_server_status_started(self, state: bool):
        self.ui.label_status_value.setText('Started' if state else 'Not started')


if __name__ == '__main__':
    try:
        app = QtWidgets.QApplication(sys.argv)
        window = MainWindow()
        window.show()
        sys.exit(app.exec_())
    except:
        print(traceback.format_exc())
