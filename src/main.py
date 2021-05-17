from __future__ import annotations

import sys

from PyQt5.QtCore import QLocale
from PyQt5.QtWidgets import QApplication

from MainWindow import MainWindow
from database import Database
from globaldata import Globals


def main() -> None:
    Database.init('sqlite:///../dbd-match-log-DEV.db')
    app = QApplication(sys.argv)
    QLocale.setDefault(QLocale(QLocale.English))
    Globals.init()
    window = MainWindow(title='Dead by Daylight match log', windowSize=(1280, 920))
    window.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()