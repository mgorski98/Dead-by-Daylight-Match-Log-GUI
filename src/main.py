import sys
from PyQt5.QtWidgets import QApplication
from MainWindow import MainWindow
from database import Database
from src.models import Killer, KillerAddon, GameMap, Realm, Item, ItemType
from sqlalchemy import insert, select


def main() -> None:
    Database.init('sqlite:///../dbd-match-log-DEV.db')
    # Database.update()
    app = QApplication(sys.argv)
    window = MainWindow(title='Dead by Daylight match log', windowSize=(1200, 800))
    window.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()