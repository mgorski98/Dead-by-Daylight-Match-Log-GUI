from __future__ import annotations

import sys

from PyQt5.QtCore import QLocale, Qt
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QApplication, QSplashScreen

from MainWindow import MainWindow
from database import Database
from globaldata import Globals

def updateSplash(splash: QSplashScreen, message:str) -> None:
    splash.showMessage(message, Qt.AlignBottom)
    QApplication.processEvents()

def main() -> None:
    Database.init('sqlite:///../dbd-match-log-DEV.db')
    app = QApplication(sys.argv)
    splash = QSplashScreen(app.primaryScreen())
    splash.show()
    QLocale.setDefault(QLocale(QLocale.English))
    Globals.init()
    window = MainWindow(title='Dead by Daylight match log', windowSize=(1280, 920))
    window.show()
    splash.finish(window)
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()