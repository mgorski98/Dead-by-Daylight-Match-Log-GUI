from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QDialog, QHBoxLayout, QVBoxLayout, QPushButton, QListWidget, QLabel, QListWidgetItem

from guicontrols import DBDMatchListItem
from models import DBDMatch


class LoadedGamesDisplayDialog(QDialog):

    def __init__(self, games: list[DBDMatch], errors: list[str], dialogSize=(1000,750), parent=None):
        super().__init__(parent)
        self.games = games
        self.errors = errors
        self.resize(*dialogSize)

        #setup code
        mainLayout = QVBoxLayout()
        self.setLayout(mainLayout)
        displayLayout = QHBoxLayout()
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
        displayLayout.addLayout(gamesDisplayLayout)
        displayLayout.addLayout(errorsDisplayLayout)
        self.gamesListWidget = QListWidget()
        self.errorsListWidget = QListWidget()
        gamesLabel = QLabel('Loaded games')
        errorsLabel = QLabel('Encountered errors')
        gamesDisplayLayout.addWidget(gamesLabel)
        gamesDisplayLayout.addWidget(self.gamesListWidget)
        errorsDisplayLayout.addWidget(errorsLabel)
        errorsDisplayLayout.addWidget(self.errorsListWidget)
        self.errorsListWidget.addItems(self.errors if len(self.errors) > 0 else ('No errors',))
        for match in self.games:
            matchWidget = DBDMatchListItem(match)
            listItem = QListWidgetItem()
            listItem.setSizeHint(matchWidget.sizeHint())
            self.gamesListWidget.addItem(listItem)
            self.gamesListWidget.setItemWidget(listItem, matchWidget)
