from PyQt5.QtWidgets import QDialog

from models import DBDMatch


class LoadedGamesDisplayDialog(QDialog):

    def __init__(self, games: list[DBDMatch], errors: list[str], parent=None):
        super().__init__(parent)