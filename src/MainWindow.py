from __future__ import annotations
import operator
import sqlalchemy
from PyQt5.QtCore import *
from PyQt5.QtGui import QKeySequence
from PyQt5.QtWidgets import QMainWindow, QWidget, QGridLayout, QHBoxLayout, QVBoxLayout, QLineEdit, QLabel, QSpinBox, \
    QDateEdit, QTabWidget, QAction, QMessageBox, QSpacerItem, QProgressDialog, QListWidget, QPushButton, QComboBox, \
    QFileDialog

from classutil import DBDMatchParser, DBDMatchLogFileLoader, LogFileLoadWorker
from database import Database, DatabaseUpdateWorker
from globaldata import Globals
from guicontrols import KillerSelect, AddonSelection, FacedSurvivorSelectionWindow, PerkSelection, \
    OfferingSelection, MapSelect, SurvivorSelect, SurvivorItemSelect
from models import KillerAddon, Killer, Offering, Survivor, Realm, KillerMatch, KillerMatchPerk, \
    MatchKillerAddon, DBDMatch, ItemAddon, Perk, PerkType, Item, SurvivorMatchResult, SurvivorMatchPerk, MatchItemAddon, \
    SurvivorMatch
from util import setQWidgetLayout, nonNegativeIntValidator, addWidgets, splitUpper


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
        self.parser = DBDMatchParser(killers, survivors, addons, items, offerings, realms, killerPerks + survivorPerks)
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

        self.killerSelection = KillerSelect(killers=killers, icons=Globals.KILLER_ICONS, iconSize=Globals.CHARACTER_ICON_SIZE)

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

        self.facedSurvivorSelection = FacedSurvivorSelectionWindow(survivors, icons=Globals.SURVIVOR_ICONS, iconSize=(Globals.CHARACTER_ICON_SIZE[0] // 2, Globals.CHARACTER_ICON_SIZE[1] // 2), size=(2,2))
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
        survivorListLayout.addSpacerItem(QSpacerItem(0, 15))
        survivorListLayout.addWidget(self.addSurvivorMatchButton)
        survivorListLayout.addSpacerItem(QSpacerItem(0, 90))
        self.addSurvivorMatchButton.clicked.connect(self.addNewSurvivorMatch)
        survivorListLayout.setAlignment(self.addSurvivorMatchButton, Qt.AlignCenter)
        self.survivorSelect = SurvivorSelect(survivors,icons=Globals.SURVIVOR_ICONS, iconSize=Globals.CHARACTER_ICON_SIZE)
        self.itemAddonSelection = AddonSelection(itemAddons)
        self.survivorOfferingSelect = OfferingSelection(offerings=offerings)
        self.itemSelection = SurvivorItemSelect(items=items, icons=Globals.ITEM_ICONS, iconSize=Globals.ITEM_ICON_SIZE)
        self.itemSelection.selectionChanged.connect(lambda item: self.itemAddonSelection.filterAddons(lambda addon: isinstance(addon, ItemAddon) and addon.itemType == item.itemType))
        self.itemSelection.selectFromIndex(0)
        self.survivorPerkSelection = PerkSelection(survivorPerks)
        upperSurvivorWidget, upperSurvivorLayout = setQWidgetLayout(QWidget(), QHBoxLayout())
        upperSurvivorLayout.addWidget(self.survivorSelect)
        upperSurvivorLayout.addWidget(self.itemSelection)
        upperSurvivorLayout.addWidget(self.itemAddonSelection)
        survivorInfoLayout.addWidget(upperSurvivorWidget)
        survivorInfoLayout.addWidget(self.survivorPerkSelection)
        self.survivorMapSelection = MapSelect(realms)
        self.survivorPointsTextBox = QLineEdit()
        self.survivorPointsTextBox.setValidator(nonNegativeIntValidator())
        self.survivorRankSpinner = QSpinBox()
        self.survivorRankSpinner.setRange(Globals.HIGHEST_RANK, Globals.LOWEST_RANK)
        self.survivorMatchDatePicker = QDateEdit(calendarPopup=True)
        self.survivorMatchDatePicker.setDate(QDate.currentDate())
        self.survivorMatchResultComboBox = QComboBox()
        self.partySizeSpinner = QSpinBox()
        self.partySizeSpinner.setRange(1, 4) #minimum one person (you), maximum 4 people (max party size in DBD)
        otherMatchInfoWidget, otherMatchInfoLayout = setQWidgetLayout(QWidget(), QVBoxLayout())
        spinnersParentWidget, spinnersParentLayout = setQWidgetLayout(QWidget(), QHBoxLayout())
        for spinner, labelStr in zip([self.survivorRankSpinner, self.partySizeSpinner], ['Survivor rank','Party size']):
            cellWidget, cellLayout = setQWidgetLayout(QWidget(), QVBoxLayout())
            cellLayout.addWidget(QLabel(labelStr))
            cellLayout.addWidget(spinner)
            spinnersParentLayout.addWidget(cellWidget)
        widgets = [
            self.survivorMatchDatePicker,
            self.survivorMatchResultComboBox,
            spinnersParentWidget,
            self.survivorPointsTextBox
        ]
        for widget, labelStr in zip(widgets,['Match date','Match result','','Points']):
            cellWidget, cellLayout = setQWidgetLayout(QWidget(), QVBoxLayout())
            if labelStr:
                cellLayout.addWidget(QLabel(labelStr))
            cellLayout.addWidget(widget)
            otherMatchInfoLayout.addWidget(cellWidget)
        upperSurvivorMatchInfoWidget, upperSurvivorMatchInfoLayout = setQWidgetLayout(QWidget(), QHBoxLayout())
        upperSurvivorMatchInfoLayout.addWidget(otherMatchInfoWidget)
        upperSurvivorMatchInfoLayout.addSpacerItem(QSpacerItem(75,1))
        upperSurvivorMatchInfoLayout.addWidget(self.survivorMapSelection)
        upperSurvivorMatchInfoLayout.addSpacerItem(QSpacerItem(35,1))
        survivorMatchInfoLayout.addWidget(upperSurvivorMatchInfoWidget)
        self.survivorMatchResultComboBox.addItems(' '.join(splitUpper(x.name)).lower().capitalize() for x in SurvivorMatchResult)
        self.facedKillerSelect = KillerSelect(killers, icons=Globals.KILLER_ICONS, iconSize=Globals.CHARACTER_ICON_SIZE)
        lowerSurvivorMatchInfoWidget, lowerSurvivorMatchInfoLayout = setQWidgetLayout(QWidget(), QHBoxLayout())
        lowerSurvivorMatchInfoLayout.addWidget(self.facedKillerSelect)
        lowerSurvivorMatchInfoLayout.addSpacerItem(QSpacerItem(25, 1))
        lowerSurvivorMatchInfoLayout.addWidget(self.survivorOfferingSelect)
        survivorMatchInfoLayout.addWidget(lowerSurvivorMatchInfoWidget)
        self.addSurvivorMatchButton.setFixedWidth(150)
        survivorListLayout.setContentsMargins(5, 23, 5, 0)

    def addNewKillerMatch(self):
        killer = self.killerSelection.getSelectedItem()
        offering = self.killerOfferingSelection.selectedItem
        addons = list(i for i in self.killerAddonSelection.selectedAddons.values() if i is not None)
        perks = list(i for i in self.killerPerkSelection.selectedPerks.values() if i is not None)
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
        survivor = self.survivorSelect.getSelectedItem()
        offering = self.survivorOfferingSelect.selectedItem
        addons = list(i for i in self.itemAddonSelection.selectedAddons.values() if i is not None)
        perks = list(i for i in self.survivorPerkSelection.selectedPerks.values() if i is not None)
        pointsStr = self.killerMatchPointsTextBox.text().strip()
        points = 0 if not pointsStr else int(pointsStr)
        matchDate = self.survivorMatchDatePicker.date().toPyDate()
        rank = self.survivorRankSpinner.value()
        gameMap = self.survivorMapSelection.selectedMap
        facedKiller = self.facedKillerSelect.getSelectedItem()
        item = self.itemSelection.getSelectedItem()
        survivorMatchPerks = [SurvivorMatchPerk(perk=perk) for perk in perks]
        itemAddons = [MatchItemAddon(itemAddon=addon) for addon in addons]
        survivorMatchResult = SurvivorMatchResult(self.survivorMatchResultComboBox.currentIndex())
        partySize = self.partySizeSpinner.value()
        survivorMatch = SurvivorMatch(survivor=survivor,facedKiller=facedKiller,item=item,itemAddons=itemAddons,
                                      rank=rank, partySize=partySize,matchResult=survivorMatchResult, gameMap=gameMap,
                                      matchDate=matchDate, offering=offering, points=points, perks=survivorMatchPerks)
        self.currentlyAddedMatches.append(survivorMatch)

    def __setupMenuBar(self):
        updateAction = QAction('Update game data and image database', self)
        updateAction.triggered.connect(self.__confirmUpdate)
        loadLogAction = QAction('Load match log data', self)
        loadLogAction.setShortcut(QKeySequence("Ctrl+O"))
        loadLogAction.triggered.connect(self.__loadMatchLogs)
        logHelpAction = QAction('Show match log file help', self)
        logHelpAction.triggered.connect(self.__showLogHelpWindow)
        saveMatchesAction = QAction("Save current match data", self)
        saveMatchesAction.triggered.connect(self.__saveMatches)
        saveMatchesAction.setShortcut(QKeySequence("Ctrl+S"))
        exportDBAction = QAction("Export database as a log file", self)
        exportDBAction.triggered.connect(self.__exportDBAsLog)
        menubar = self.menuBar()
        fileMenu = menubar.addMenu('&File')
        optionsMenu = menubar.addMenu('&Options')
        helpMenu = menubar.addMenu('&Help')
        optionsMenu.addAction(saveMatchesAction)
        optionsMenu.addAction(updateAction)
        fileMenu.addAction(loadLogAction)
        fileMenu.addAction(exportDBAction)
        helpMenu.addAction(logHelpAction)

    def __saveMatches(self):
        if len(self.currentlyAddedMatches) > 0:
            return
        # with Database.instance().getNewSession() as s:
        #     s.add_all(self.currentlyAddedMatches)
        #     s.commit()
        # self.currentlyAddedMatches.clear()

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
        files, _ = QFileDialog.getOpenFileNames(self,"Select match log files",filter="Text files (*.txt)")
        loader = DBDMatchLogFileLoader(self.parser)
        progressDialog = QProgressDialog()
        progressDialog.setRange(0,0)
        progressDialog.setWindowTitle("Loading match log files")
        progressDialog.setCancelButton(None)
        progressDialog.setFixedSize(450, 100)
        progressDialog.setModal(True)
        self.loadWorker = LogFileLoadWorker(loader, files)
        self.loadWorker.signals.fileLoadStarted.connect(lambda fileName: progressDialog.setLabelText(f"Loading file: {fileName}"))
        self.loadWorker.signals.finished.connect(lambda l,e: progressDialog.close())
        self.loadWorker.signals.finished.connect(lambda l,e: print(f'{l}\n{e}'))
        # loadWorker.signals.finished.connect() #todo: connect a function showing a new dialog window with information about errors and loaded games (that lets you confirm if you want to save data)
        #maybe paginate loaded elements?
        self.threadPool.start(self.loadWorker)
        progressDialog.show()

    def __showLogHelpWindow(self):
        pass

    def __exportDBAsLog(self):
        pass