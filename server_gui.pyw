import sys
from PyQt5 import QtWidgets, QtGui
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


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
