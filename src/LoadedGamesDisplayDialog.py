from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QDialog, QHBoxLayout, QVBoxLayout, QPushButton, QListWidget, QLabel, QListWidgetItem, \
    QTabWidget, QWidget, QGridLayout

from guicontrols import DBDMatchListItem
from models import DBDMatch, SurvivorMatch, KillerMatch
from util import setQWidgetLayout


class LoadedGamesDisplayDialog(QDialog):

    def __init__(self, games: list[DBDMatch], errors: list[str], title="PyQt5 dialog", dialogSize=(1000,750), parent=None):
        super().__init__(parent)
        self.games = games
        self.errors = errors
        self.resize(*dialogSize)
        self.setWindowTitle(title)

        #setup code
        mainLayout = QVBoxLayout()
        self.setLayout(mainLayout)
        displayLayout = QGridLayout()
        buttonsLayout = QHBoxLayout()
        mainLayout.addLayout(displayLayout)
        mainLayout.addLayout(buttonsLayout)
        discardButton = QPushButton("Discard")
        acceptButton = QPushButton("Accept")
        acceptButton.clicked.connect(self.accept)
        discardButton.clicked.connect(self.close)
        buttonsLayout.addStretch(1)
        buttonsLayout.addWidget(acceptButton)
        buttonsLayout.addWidget(discardButton)
        buttonsLayout.setAlignment(acceptButton, Qt.AlignRight)
        buttonsLayout.setAlignment(discardButton,Qt.AlignRight)
        gamesDisplayLayout = QVBoxLayout()
        errorsDisplayLayout = QVBoxLayout()
        displayLayout.addLayout(gamesDisplayLayout, 0, 0, 1, 4)
        displayLayout.addLayout(errorsDisplayLayout, 0, 4, 1, 2)
        self.survivorGamesListWidget = QListWidget()
        self.killerGamesListWidget = QListWidget()
        self.errorsListWidget = QListWidget()
        errorsLabel = QLabel('Encountered errors')
        gamesDisplayTabWidget = QTabWidget()
        gamesDisplayTabWidget.addTab(self.killerGamesListWidget, "Killer games")
        gamesDisplayTabWidget.addTab(self.survivorGamesListWidget, "Survivor games")
        gamesDisplayLayout.addWidget(gamesDisplayTabWidget)
        errorsDisplayLayout.addWidget(errorsLabel)
        errorsDisplayLayout.addWidget(self.errorsListWidget)
        self.errorsListWidget.addItems(self.errors if len(self.errors) > 0 else ('No errors',))
        survivorGames = filter(lambda g: isinstance(g, SurvivorMatch), self.games)
        killerGames = filter(lambda g: isinstance(g, KillerMatch), self.games)
        for listWidget, gamesList in zip((self.killerGamesListWidget, self.survivorGamesListWidget),(killerGames, survivorGames)):
            for match in gamesList:
                matchWidget = DBDMatchListItem(match)
                listItem = QListWidgetItem()
                listItem.setSizeHint(matchWidget.sizeHint())
                listWidget.addItem(listItem)
                listWidget.setItemWidget(listItem, matchWidget)
        # for match in self.games:
        #     matchWidget = DBDMatchListItem(match)
