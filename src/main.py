from __future__ import annotations

import sys

from PyQt5.QtCore import QLocale, Qt
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QApplication, QSplashScreen

from MainWindow import MainWindow
from database import Database
from globaldata import Globals

import json

def loadConfig(path: str):
    with open(path,mode='r') as f:
        return json.load(f)


def updateSplash(splash: QSplashScreen, message:str) -> None:
    splash.showMessage(message, Qt.AlignBottom)
    QApplication.processEvents()

def main() -> None:
    config = loadConfig('../config.cfg' if len(sys.argv) <= 1 else sys.argv[1])
    Database.init(config["DB_URL"])
    app = QApplication(sys.argv)
    app.setAttribute(Qt.AA_DisableWindowContextHelpButton)
    splash = QSplashScreen(QPixmap())
    splash.show()
    QLocale.setDefault(QLocale(QLocale.English))
    Globals.init()
    window = MainWindow(title='Dead by Daylight match log', windowSize=(1280, 920))
    window.show()
    splash.finish(window)
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()