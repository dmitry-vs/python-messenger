import sys
from PyQt5 import QtWidgets, QtGui
from PyQt5.QtCore import QObject, QThread, pyqtSignal, pyqtSlot
import os
import traceback
import logging

import server_pyqt
from server import Server
import helpers
import log_confing

log = logging.getLogger(helpers.CLIENT_LOGGER_NAME)


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, parent=None):
        QtWidgets.QWidget.__init__(self, parent)
        self.ui = server_pyqt.Ui_MainWindow()
        self.ui.setupUi(self)
        self.server = None
        self.listen_ip = None
        self.listen_port = None
        self.storage_name = os.path.join(helpers.get_this_script_full_dir(), 'server.sqlite')

        # connect slots
        self.ui.pushButton_start_server.clicked.connect(self.start_server_click)
        self.ui.pushButton_stop_server.clicked.connect(self.stop_server_click)

    def start_server_click(self):
        try:
            self.listen_ip = self.ui.lineEdit_ip.text()
            self.listen_port = int(self.ui.lineEdit_port.text())
            self.server = Server(self.listen_ip, self.listen_port, self.storage_name)
            self.server.start()
            self.set_server_status_started(True)
        except:
            self.print_info(traceback.format_exc())

    def stop_server_click(self):
        try:
            if not self.server:
                self.print_info('Not running')
            self.server.close_server()
            self.server = None
            self.set_server_status_started(False)
        except:
            self.print_info(traceback.format_exc())

    def print_info(self, info: str):
        current_text = self.ui.textBrowser_service_info.toPlainText()
        new_text = info if not current_text else f'{current_text}\n{info}'
        self.ui.textBrowser_service_info.setText(new_text)
        self.ui.textBrowser_service_info.moveCursor(QtGui.QTextCursor.End)

    def set_server_status_started(self, state: bool):
        self.ui.label_status_value.setText('Started' if state else 'Not started')

    def clear_state(self):
        pass


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
