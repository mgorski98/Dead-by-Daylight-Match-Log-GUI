from collections import namedtuple
from functools import partial
import operator

import sqlalchemy
from PyQt5.QtCore import *
from PyQt5.QtGui import QRegularExpressionValidator, QKeySequence
from PyQt5.QtWidgets import QMainWindow, QWidget, QGridLayout, QHBoxLayout, QVBoxLayout, QLineEdit, QLabel, QSpinBox, \
    QDateEdit, QTabWidget, QAction, QMessageBox, QDialogButtonBox, QSpacerItem, QSizePolicy, QApplication, \
    QProgressDialog, QListWidget, QPushButton, QComboBox

from database import Database, DatabaseUpdateWorker
from guicontrols import KillerSelect, AddonSelectPopup, AddonSelection, FacedSurvivorSelectionWindow, PerkSelection, \
    OfferingSelection, MapSelect, SurvivorSelect, SurvivorItemSelect
from models import KillerAddon, Killer, Offering, Survivor, Realm, GameMap, KillerMatch, KillerMatchPerk, \
    MatchKillerAddon, DBDMatch, ItemAddon, Perk, PerkType, Item
from util import setQWidgetLayout, nonNegativeIntValidator, addWidgets
from globaldata import Globals


class MainWindow(QMainWindow):
    def __init__(self, parent=None, title='PyQt5 Application', windowSize=(800,600)):
        super(MainWindow, self).__init__(parent=parent)
        with Database.instance().getNewSession() as s:
            extractor = operator.itemgetter(0)
            killers = list(map(extractor, s.execute(sqlalchemy.select(Killer)).all())) #for some ungodly reason this returns list of 1-element tuples
            realms = list(map(extractor, s.execute(sqlalchemy.select(Realm)).all()))
            survivors = list(map(extractor, s.execute(sqlalchemy.select(Survivor)).all()))
            killerAddons = list(map(extractor, s.execute(sqlalchemy.select(KillerAddon)).all()))
            itemAddons = list(map(extractor, s.execute(sqlalchemy.select(ItemAddon)).all()))
            addons = killerAddons + itemAddons
            offerings = list(map(extractor, s.execute(sqlalchemy.select(Offering)).all()))
            killerPerks = list(map(extractor, s.execute(sqlalchemy.select(Perk).where(Perk.perkType == PerkType.Killer)).all()))
            survivorPerks = list(map(extractor, s.execute(sqlalchemy.select(Perk).where(Perk.perkType == PerkType.Survivor)).all()))
            items = list(map(extractor, s.execute(sqlalchemy.select(Item)).all()))

        self.currentlyAddedMatches: list[DBDMatch] = []
        self.setWindowTitle(title)
        self.setContentsMargins(5, 5, 5, 5)
        self.resize(windowSize[0], windowSize[1])
        self.setCentralWidget(QTabWidget())
        killerWidget, killerLayout = setQWidgetLayout(QWidget(), QGridLayout())
        survivorWidget, survivorLayout = setQWidgetLayout(QWidget(), QGridLayout())
        self.centralWidget().addTab(killerWidget, "Killers")
        self.centralWidget().addTab(survivorWidget, "Survivors")
        self.__setupMenuBar()
        self.threadPool = QThreadPool.globalInstance()
        self.worker = None
        #<editor-fold desc="setting up killer form">
        killerMatchInfoTabWidget = QTabWidget()
        killerInfoWidget, killerInfoLayout = setQWidgetLayout(QWidget(), QVBoxLayout())
        killerMatchInfoWidget, killerMatchInfoLayout = setQWidgetLayout(QWidget(), QVBoxLayout())
        killerMatchInfoTabWidget.addTab(killerInfoWidget, "Killer info")
        killerMatchInfoTabWidget.addTab(killerMatchInfoWidget, "Match info")
        killerLayout.addWidget(killerMatchInfoTabWidget, 0, 0, 1, 3)
        killerListWidget, killerListLayout = setQWidgetLayout(QWidget(), QVBoxLayout())
        killerLayout.addWidget(killerListWidget, 0, 4, 1, 2)

        self.killerSelection = KillerSelect(killers, iconSize=Globals.CHARACTER_ICON_SIZE)


        self.killerMatchPointsTextBox = QLineEdit()
        self.killerMatchPointsTextBox.setValidator(nonNegativeIntValidator())
        self.killerMatchDatePicker = QDateEdit(calendarPopup=True)
        self.killerMatchDatePicker.setDate(QDate.currentDate())
        self.killerRankSpinner = QSpinBox()
        self.killerRankSpinner.setRange(Globals.HIGHEST_RANK, Globals.LOWEST_RANK)#lowest rank is 20, DBD ranks are going down the better they are, so rank 1 is the best
        otherInfoWidget, otherInfoLayout = setQWidgetLayout(QWidget(),QGridLayout())
        for label, obj in zip(['Match date','Points','Killer rank'], [self.killerMatchDatePicker, self.killerMatchPointsTextBox, self.killerRankSpinner]):
            cellWidget, cellLayout = setQWidgetLayout(QWidget(),QVBoxLayout())
            addWidgets(cellLayout, QLabel(label), obj)
            otherInfoLayout.addWidget(cellWidget)

        self.facedSurvivorSelection = FacedSurvivorSelectionWindow(survivors, size=(2,2))
        self.killerPerkSelection = PerkSelection(killerPerks)
        self.killerAddonSelection = AddonSelection(addons)

        self.killerSelection.selectionChanged.connect(lambda killer: self.killerAddonSelection.filterAddons(lambda addon: isinstance(addon, KillerAddon) and killer.killerAlias == addon.killer.killerAlias))
        self.killerSelection.selectFromIndex(0)
        self.killerOfferingSelection = OfferingSelection(offerings)

        killerInfoUpperRowWidget, killerInfoUpperRowLayout = setQWidgetLayout(QWidget(), QHBoxLayout())
        killerInfoUpperRowLayout.addWidget(self.killerSelection)
        killerInfoUpperRowLayout.addWidget(self.killerAddonSelection)
        killerInfoUpperRowLayout.addWidget(self.killerOfferingSelection)
        killerInfoLayout.addWidget(killerInfoUpperRowWidget)
        killerInfoLowerRowWidget, killerInfoLowerRowLayout = setQWidgetLayout(QWidget(), QHBoxLayout())
        killerInfoLowerRowLayout.addWidget(self.killerPerkSelection)
        killerInfoLayout.addWidget(killerInfoLowerRowWidget)

        self.killerMapSelection = MapSelect(realms)
        widget, layout = setQWidgetLayout(QWidget(), QHBoxLayout())
        layout.addWidget(otherInfoWidget)
        layout.addWidget(self.killerMapSelection)
        killerMatchInfoLayout.addWidget(widget)
        killerMatchInfoLayout.addWidget(self.facedSurvivorSelection)

        killerListLayout.setContentsMargins(5,23,5,0)
        self.killerMatchListWidget = QListWidget()
        killerListLayout.addWidget(self.killerMatchListWidget)
        killerListLayout.addSpacerItem(QSpacerItem(1, 15))
        self.addKillerMatchButton = QPushButton("Add new killer match")
        self.addKillerMatchButton.clicked.connect(self.addNewKillerMatch)
        self.addKillerMatchButton.setFixedWidth(150)
        killerListLayout.addWidget(self.addKillerMatchButton)
        killerListLayout.setAlignment(self.addKillerMatchButton, Qt.AlignHCenter)
        killerListLayout.addSpacerItem(QSpacerItem(1, 90))
        #</editor-fold>
        survivorMainTabWidget = QTabWidget()
        self.survivorMatchListWidget = QListWidget()
        survivorListWidget, survivorListLayout = setQWidgetLayout(QWidget(), QVBoxLayout())
        survivorInfoWidget, survivorInfoLayout = setQWidgetLayout(QWidget(), QVBoxLayout())
        survivorMatchInfoWidget, survivorMatchInfoLayout = setQWidgetLayout(QWidget(), QVBoxLayout())
        survivorMainTabWidget.addTab(survivorInfoWidget, "Survivor info")
        survivorMainTabWidget.addTab(survivorMatchInfoWidget, "Match info")
        survivorLayout.addWidget(survivorMainTabWidget, 0, 0, 1, 3)
        survivorLayout.addWidget(survivorListWidget, 0, 4, 1, 2)
        survivorListLayout.addWidget(self.survivorMatchListWidget)
        self.addSurvivorMatchButton = QPushButton("Add new survivor match")
        survivorListLayout.addWidget(self.addSurvivorMatchButton)
        self.addSurvivorMatchButton.clicked.connect(self.addNewSurvivorMatch)
        survivorListLayout.setAlignment(self.addSurvivorMatchButton, Qt.AlignCenter)
        self.survivorSelect = SurvivorSelect(survivors,iconSize=Globals.CHARACTER_ICON_SIZE)
        self.itemAddonSelection = AddonSelection(itemAddons)
        self.survivorOfferingSelect = OfferingSelection(offerings=offerings)
        self.itemSelection = SurvivorItemSelect(items=items)
        self.itemSelection.selectionChanged.connect(lambda item: self.itemAddonSelection.filterAddons(lambda addon: isinstance(addon, ItemAddon) and addon.itemType == item.itemType))
        self.itemSelection.selectFromIndex(0)
        self.survivorPerkSelection = PerkSelection(survivorPerks)
        upperSurvivorWidget, upperSurvivorLayout = setQWidgetLayout(QWidget(), QHBoxLayout())
        upperSurvivorLayout.addWidget(self.survivorSelect)
        upperSurvivorLayout.addWidget(self.itemSelection)
        upperSurvivorLayout.addWidget(self.itemAddonSelection)
        upperSurvivorLayout.addWidget(self.survivorOfferingSelect)
        survivorInfoLayout.addWidget(upperSurvivorWidget)
        survivorInfoLayout.addWidget(self.survivorPerkSelection)
        self.survivorMapSelection = MapSelect(realms)
        self.survivorPointsTextBox = QLineEdit()
        self.survivorRankSpinner = QSpinBox()
        self.survivorMatchDatePicker = QDateEdit(calendarPopup=True)
        self.survivorMatchDatePicker.setDate(QDate.currentDate())
        self.survivorMatchResultComboBox = QComboBox()
        self.partySizeSpinner = QSpinBox()
        otherMatchInfoWidget, otherMatchInfoLayout = setQWidgetLayout(QWidget(), QVBoxLayout())
        spinnersParentWidget, spinnersParentLayout = setQWidgetLayout(QWidget(), QHBoxLayout())


    def addNewKillerMatch(self):
        killer = self.killerSelection.getSelectedItem()
        offering = self.killerOfferingSelection.selectedItem
        addons = list(self.killerAddonSelection.selectedAddons.values())
        perks = list(self.killerPerkSelection.selectedPerks.values())
        pointsStr = self.killerMatchPointsTextBox.text().strip()
        points = 0 if not pointsStr else int(pointsStr)
        matchDate = self.killerMatchDatePicker.date().toPyDate()
        rank = self.killerRankSpinner.value()
        gameMap = self.killerMapSelection.selectedMap
        facedSurvivors = [selection.getFacedSurvivor() for selection in self.facedSurvivorSelection.selections.values()]
        killerMatchPerks = [KillerMatchPerk(perk=perk) for perk in perks if perk is not None]
        killerAddons = [MatchKillerAddon(killerAddon=addon) for addon in addons if addon is not None]
        killerMatch = KillerMatch(killer=killer, facedSurvivors=facedSurvivors, gameMap=gameMap,
                                  points=points, offering=offering, rank=rank,
                                  matchDate=matchDate, killerAddons=killerAddons, perks=killerMatchPerks)
        self.currentlyAddedMatches.append(killerMatch)

    def addNewSurvivorMatch(self):
        pass

    def __setupMenuBar(self):
        updateAction = QAction('Update game data and image database', self)
        updateAction.triggered.connect(self.__confirmUpdate)
        loadLogAction = QAction('Load match log data', self)
        loadLogAction.triggered.connect(self.__loadMatchLogs)
        logHelpAction = QAction('Show match log file help', self)
        logHelpAction.triggered.connect(self.__showLogHelpWindow)
        saveMatchesAction = QAction("Save current match data", self)
        saveMatchesAction.triggered.connect(self.__saveMatches)
        saveMatchesAction.setShortcut(QKeySequence("Ctrl+S"))
        menubar = self.menuBar()
        fileMenu = menubar.addMenu('&File')
        optionsMenu = menubar.addMenu('&Options')
        helpMenu = menubar.addMenu('&Help')
        optionsMenu.addAction(saveMatchesAction)
        optionsMenu.addAction(updateAction)
        fileMenu.addAction(loadLogAction)
        helpMenu.addAction(logHelpAction)

    def __saveMatches(self):
        pass

    def __confirmUpdate(self):
        msgBox = QMessageBox()
        msgBox.setIcon(QMessageBox.Question)
        msgBox.setText('Resources update')
        msgBox.setInformativeText('Do you really want to update resources? It might take a while.')
        msgBox.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        result = msgBox.exec_()
        if result == QMessageBox.Yes:
            progressDialog = QProgressDialog()
            progressDialog.setWindowTitle("Updating database")
            progressDialog.setModal(True)
            progressDialog.setCancelButton(None)
            progressDialog.setFixedSize(450, 75)
            progressDialog.setRange(0,0)
            self.worker = DatabaseUpdateWorker()
            self.worker.signals.progressUpdated.connect(lambda s: progressDialog.setLabelText(s))
            self.worker.signals.finished.connect(progressDialog.close)
            self.threadPool.start(self.worker)
            progressDialog.show()



    def __loadMatchLogs(self):
        pass

    def __showLogHelpWindow(self):
        pass