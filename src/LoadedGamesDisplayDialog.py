from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QDialog, QHBoxLayout, QVBoxLayout, QPushButton, QListWidget, QLabel, QTabWidget, \
    QGridLayout, QMessageBox

from guicontrols import PaginatedMatchListWidget
from models import DBDMatch, SurvivorMatch, KillerMatch
from util import confirmation


class LoadedGamesDisplayDialog(QDialog):

    def __init__(self, games: list[DBDMatch], errors: list[str], title="PyQt5 dialog", dialogSize=(1000,750), parent=None):
        super().__init__(parent)
        self.games = games
        self.survivorGames = list(filter(lambda g: isinstance(g, SurvivorMatch), self.games))
        self.killerGames = list(filter(lambda g: isinstance(g, KillerMatch), self.games))
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

        @confirmation(text="Confirm discard", informativeText="Are you sure you want to discard loaded games?", title="Discard")
        def closeDialog():
            self.close()


        discardButton = QPushButton("Discard")
        acceptButton = QPushButton("Accept")
        acceptButton.clicked.connect(self.accept)
        discardButton.clicked.connect(closeDialog)
        buttonsLayout.addStretch(1)
        buttonsLayout.addWidget(acceptButton)
        buttonsLayout.addWidget(discardButton)
        buttonsLayout.setAlignment(acceptButton, Qt.AlignRight)
        buttonsLayout.setAlignment(discardButton,Qt.AlignRight)
        gamesDisplayLayout = QVBoxLayout()
        errorsDisplayLayout = QVBoxLayout()
        displayLayout.addLayout(gamesDisplayLayout, 0, 0, 1, 4)
        displayLayout.addLayout(errorsDisplayLayout, 0, 4, 1, 2)
        self.survivorGamesListWidget = PaginatedMatchListWidget(self.survivorGames)
        self.killerGamesListWidget = PaginatedMatchListWidget(self.killerGames)

        self.errorsListWidget = QListWidget()
        errorsLabel = QLabel('Encountered errors')
        gamesDisplayTabWidget = QTabWidget()
        gamesDisplayTabWidget.addTab(self.killerGamesListWidget, "Killer games")
        gamesDisplayTabWidget.addTab(self.survivorGamesListWidget, "Survivor games")
        gamesDisplayLayout.addWidget(gamesDisplayTabWidget)
        errorsDisplayLayout.addWidget(errorsLabel)
        errorsDisplayLayout.addWidget(self.errorsListWidget)
        self.errorsListWidget.addItems(self.errors if len(self.errors) > 0 else ('No errors',))
