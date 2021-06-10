from __future__ import annotations

import datetime
import operator

import sqlalchemy
from PyQt5 import QtGui
from PyQt5.QtCore import *
from PyQt5.QtGui import QKeySequence
from PyQt5.QtWidgets import QMainWindow, QWidget, QGridLayout, QHBoxLayout, QVBoxLayout, QLineEdit, QLabel, QSpinBox, \
    QDateEdit, QTabWidget, QAction, QMessageBox, QSpacerItem, QProgressDialog, QListWidget, QPushButton, QComboBox, \
    QFileDialog, QListWidgetItem, QDialog

from LoadedGamesDisplayDialog import LoadedGamesDisplayDialog
from classutil import DBDMatchParser, DBDMatchLogFileLoader, LogFileLoadWorker
from database import Database, DatabaseUpdateWorker, DatabaseMatchListSaveWorker
from globaldata import Globals
from guicontrols import KillerSelect, AddonSelection, FacedSurvivorSelectionWindow, PerkSelection, \
    OfferingSelection, MapSelect, SurvivorSelect, SurvivorItemSelect, DBDMatchListItem
from models import KillerAddon, KillerMatch, KillerMatchPerk, \
    MatchKillerAddon, DBDMatch, ItemAddon, PerkType, SurvivorMatchResult, SurvivorMatchPerk, MatchItemAddon, \
    SurvivorMatch, FacedSurvivorState
from statistics import StatisticsExporter, StatisticsCalculator
from util import setQWidgetLayout, nonNegativeIntValidator, addWidgets, splitUpper, confirmation


class MainWindow(QMainWindow):
    def __init__(self, parent=None, title='PyQt5 Application', windowSize=(800,600)):
        super(MainWindow, self).__init__(parent=parent)
        self.resources = Database.instance().newResourceInstance()
        self.currentlyAddedMatches: list[DBDMatch] = []
        self.setWindowTitle(title)
        self.setContentsMargins(5, 5, 5, 5)
        self.resize(windowSize[0], windowSize[1])
        self.setCentralWidget(QTabWidget())
        self.unsavedChangesLabel = QLabel("")
        self.unsavedChangesLabel.setStyleSheet("font-weight: bold; color: red;")
        self.__setupMenuBar()
        self.threadPool = QThreadPool.globalInstance()
        self.worker = None

        with Database.instance().getNewSession() as s:
            matches = list(map(lambda x: x[0], s.execute(sqlalchemy.select(KillerMatch)).all()))
            matches += list(map(lambda x: x[0], s.execute(sqlalchemy.select(SurvivorMatch)).all()))
            s = StatisticsCalculator(matches, self.resources)
            s.calculateGeneral()
            s.calculateSurvivorGeneral()
            s.calculateKillerGeneral()
        self.statusBar().showMessage("Ready", 5000)
        self.__setupKillerForm()
        self.__setupSurvivorForm()

    def closeEvent(self, e: QtGui.QCloseEvent) -> None:
        if len(self.currentlyAddedMatches) > 0:
            msgBox = QMessageBox()
            msgBox.setText("Unsaved data present")
            msgBox.setInformativeText("There are unsaved matches present. Are you sure you want to quit?")
            msgBox.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
            res = msgBox.exec_()
            if res == QMessageBox.Yes:
                super().closeEvent(e)
            else:
                e.ignore()
        else:
            super().closeEvent(e)

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
        sacrifices = sum(1 if fs.state == FacedSurvivorState.Sacrificed else 0 for fs in facedSurvivors)
        kills = sum(1 if fs.state == FacedSurvivorState.Killed else 0 for fs in facedSurvivors)
        disconnects = sum(1 if fs.state == FacedSurvivorState.Disconnected else 0 for fs in facedSurvivors)
        killerMatch = KillerMatch(killer=killer, facedSurvivors=facedSurvivors, gameMap=gameMap,
                                  points=points, offering=offering, rank=rank,
                                  matchDate=matchDate, killerAddons=killerAddons, perks=killerMatchPerks,
                                  sacrifices=sacrifices,kills=kills,disconnects=disconnects)
        self.currentlyAddedMatches.append(killerMatch)
        self.__onMatchAdded(killerMatch, self.killerMatchDateComboBox, self.killerMatchListWidget)
        self.killerMatchPointsTextBox.setText('')

    def addNewSurvivorMatch(self):
        survivor = self.survivorSelect.getSelectedItem()
        offering = self.survivorOfferingSelect.selectedItem
        addons = list(i for i in self.itemAddonSelection.selectedAddons.values() if i is not None)
        perks = list(i for i in self.survivorPerkSelection.selectedPerks.values() if i is not None)
        pointsStr = self.survivorPointsTextBox.text().strip()
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
        self.__onMatchAdded(survivorMatch, self.survivorMatchDateComboBox, self.survivorMatchListWidget)
        self.survivorPointsTextBox.setText('')

    def __setupKillerForm(self):
        killerWidget, killerLayout = setQWidgetLayout(QWidget(), QGridLayout())
        self.centralWidget().addTab(killerWidget, "Killers")
        killerMatchInfoTabWidget = QTabWidget()
        killerInfoWidget, killerInfoLayout = setQWidgetLayout(QWidget(), QVBoxLayout())
        killerMatchInfoWidget, killerMatchInfoLayout = setQWidgetLayout(QWidget(), QVBoxLayout())
        killerMatchInfoTabWidget.addTab(killerInfoWidget, "Killer info")
        killerMatchInfoTabWidget.addTab(killerMatchInfoWidget, "Match info")
        killerLayout.addWidget(killerMatchInfoTabWidget, 0, 0, 1, 3)
        killerListWidget, killerListLayout = setQWidgetLayout(QWidget(), QVBoxLayout())
        killerLayout.addWidget(killerListWidget, 0, 4, 1, 2)

        self.killerMatchDateComboBox = QComboBox()
        self.killerMatchDateComboBox.setFixedWidth(250)
        self.killerMatchDateComboBox.activated.connect(lambda index: self.__filterMatches(KillerMatch, self.killerMatchListWidget, self.killerMatchDateComboBox.itemText(index)))
            
        with Database.instance().getNewSession() as s:
            dates = s.query(KillerMatch.matchDate).distinct().all()
            self.killerMatchDateComboBox.addItems(map(lambda tup: tup[0].strftime('%d/%m/%Y'), dates))

        self.killerSelection = KillerSelect(killers=self.resources.killers, icons=Globals.KILLER_ICONS,
                                            iconSize=Globals.CHARACTER_ICON_SIZE)

        self.killerMatchPointsTextBox = QLineEdit()
        self.killerMatchPointsTextBox.setValidator(nonNegativeIntValidator())
        self.killerMatchDatePicker = QDateEdit(calendarPopup=True)
        self.killerMatchDatePicker.setDate(QDate.currentDate())
        self.killerMatchDatePicker.setDisplayFormat('dd-MM-yyyy')
        self.killerRankSpinner = QSpinBox()
        self.killerRankSpinner.setRange(Globals.HIGHEST_RANK,
                                        Globals.LOWEST_RANK)  # lowest rank is 20, DBD ranks are going down the better they are, so rank 1 is the best
        otherInfoWidget, otherInfoLayout = setQWidgetLayout(QWidget(), QGridLayout())
        for label, obj in zip(['Match date', 'Points', 'Killer rank'],
                              [self.killerMatchDatePicker, self.killerMatchPointsTextBox, self.killerRankSpinner]):
            cellWidget, cellLayout = setQWidgetLayout(QWidget(), QVBoxLayout())
            addWidgets(cellLayout, QLabel(label), obj)
            otherInfoLayout.addWidget(cellWidget)

        self.facedSurvivorSelection = FacedSurvivorSelectionWindow(self.resources.survivors, icons=Globals.SURVIVOR_ICONS, iconSize=(
        Globals.CHARACTER_ICON_SIZE[0] // 2, Globals.CHARACTER_ICON_SIZE[1] // 2), size=(2, 2))
        self.killerPerkSelection = PerkSelection([p for p in self.resources.perks if p.perkType == PerkType.Killer])
        self.killerAddonSelection = AddonSelection([a for a in self.resources.addons if isinstance(a, KillerAddon)])

        self.killerSelection.selectionChanged.connect(lambda killer: self.killerAddonSelection.filterAddons(
            lambda addon: isinstance(addon, KillerAddon) and killer.killerAlias == addon.killer.killerAlias))
        self.killerSelection.selectFromIndex(0)
        self.killerOfferingSelection = OfferingSelection(self.resources.offerings)

        killerInfoUpperRowWidget, killerInfoUpperRowLayout = setQWidgetLayout(QWidget(), QHBoxLayout())
        killerInfoUpperRowLayout.addWidget(self.killerSelection)
        killerInfoUpperRowLayout.addWidget(self.killerAddonSelection)
        killerInfoUpperRowLayout.addWidget(self.killerOfferingSelection)
        killerInfoLayout.addWidget(killerInfoUpperRowWidget)
        killerInfoLowerRowWidget, killerInfoLowerRowLayout = setQWidgetLayout(QWidget(), QHBoxLayout())
        killerInfoLowerRowLayout.addWidget(self.killerPerkSelection)
        killerInfoLayout.addWidget(killerInfoLowerRowWidget)

        self.killerMapSelection = MapSelect(self.resources.realms)
        widget, layout = setQWidgetLayout(QWidget(), QHBoxLayout())
        layout.addWidget(otherInfoWidget)
        layout.addWidget(self.killerMapSelection)
        killerMatchInfoLayout.addWidget(widget)
        killerMatchInfoLayout.addWidget(self.facedSurvivorSelection)

        killerListLayout.setContentsMargins(5, 23, 5, 0)
        self.killerMatchListWidget = QListWidget()
        killerListLayout.addWidget(QLabel("Filter matches by date"))
        killerListLayout.addWidget(self.killerMatchDateComboBox)
        killerListLayout.addWidget(self.killerMatchListWidget)
        killerListLayout.addSpacerItem(QSpacerItem(1, 15))
        self.addKillerMatchButton = QPushButton("Add new killer match")
        self.addKillerMatchButton.clicked.connect(self.addNewKillerMatch)
        self.addKillerMatchButton.setFixedWidth(150)
        killerListLayout.addWidget(self.addKillerMatchButton)
        killerListLayout.setAlignment(self.addKillerMatchButton, Qt.AlignHCenter)
        killerListLayout.addSpacerItem(QSpacerItem(1, 90))

    def __filterMatches(self, matchType, listWidget: QListWidget, dateStr: str):
        if not dateStr.strip():
            return
        listWidget.clear()
        filterDate = datetime.datetime.strptime(dateStr, '%d/%m/%Y').date()
        with Database.instance().getNewSession() as s:
            items = map(operator.itemgetter(0), s.execute(sqlalchemy.select(matchType).where(matchType.matchDate == filterDate)).all())
            for item in items:
                self.__addMatchToList(listWidget, item)

    def __onMatchAdded(self, match: DBDMatch, dateFilterComboBox: QComboBox, listWidget: QListWidget):
        matchDate = match.matchDate
        if matchDate is not None:
            matchDateStr = matchDate.strftime("%d/%m/%Y")
            textIndex = dateFilterComboBox.findText(matchDateStr)
            if textIndex == -1:
                dateFilterComboBox.addItem(matchDateStr)
                dateFilterComboBox.model().sort(0, Qt.AscendingOrder)
        self.__addMatchToList(listWidget, match)
        self.__updateUnsavedChanges("Unsaved changes!")

    def __updateUnsavedChanges(self, text: str):
        self.unsavedChangesLabel.setText(text)
        self.unsavedChangesLabel.adjustSize() #this is needed to properly adjust it inside the menubar
        x = (self.unsavedChangesLabel.parent().width() - self.unsavedChangesLabel.size().width()) #we move it to fit exactly where we want to
        self.unsavedChangesLabel.move(x, self.unsavedChangesLabel.y()) #and then call move on them parameters

    def __setupSurvivorForm(self):
        survivorWidget, survivorLayout = setQWidgetLayout(QWidget(), QGridLayout())
        self.centralWidget().addTab(survivorWidget, "Survivors")
        survivorMainTabWidget = QTabWidget()
        self.survivorMatchListWidget = QListWidget()
        self.survivorMatchDateComboBox = QComboBox()
        self.survivorMatchDateComboBox.setFixedWidth(250)
        self.survivorMatchDateComboBox.activated.connect(lambda index: self.__filterMatches(SurvivorMatch, self.survivorMatchListWidget, self.survivorMatchDateComboBox.itemText(index)))
        with Database.instance().getNewSession() as s:
            dates = s.query(SurvivorMatch.matchDate).distinct().all()
            self.survivorMatchDateComboBox.addItems(map(lambda tup: tup[0].strftime('%d/%m/%Y'), dates))

        survivorListWidget, survivorListLayout = setQWidgetLayout(QWidget(), QVBoxLayout())
        survivorInfoWidget, survivorInfoLayout = setQWidgetLayout(QWidget(), QVBoxLayout())
        survivorMatchInfoWidget, survivorMatchInfoLayout = setQWidgetLayout(QWidget(), QVBoxLayout())
        survivorMainTabWidget.addTab(survivorInfoWidget, "Survivor info")
        survivorMainTabWidget.addTab(survivorMatchInfoWidget, "Match info")
        survivorLayout.addWidget(survivorMainTabWidget, 0, 0, 1, 3)
        survivorLayout.addWidget(survivorListWidget, 0, 4, 1, 2)
        survivorListLayout.addWidget(QLabel("Filter matches by date"))
        survivorListLayout.addWidget(self.survivorMatchDateComboBox)
        survivorListLayout.addWidget(self.survivorMatchListWidget)
        self.addSurvivorMatchButton = QPushButton("Add new survivor match")
        survivorListLayout.addSpacerItem(QSpacerItem(0, 15))
        survivorListLayout.addWidget(self.addSurvivorMatchButton)
        survivorListLayout.addSpacerItem(QSpacerItem(0, 90))
        self.addSurvivorMatchButton.clicked.connect(self.addNewSurvivorMatch)
        survivorListLayout.setAlignment(self.addSurvivorMatchButton, Qt.AlignCenter)
        self.survivorSelect = SurvivorSelect(self.resources.survivors, icons=Globals.SURVIVOR_ICONS,
                                             iconSize=Globals.CHARACTER_ICON_SIZE)
        self.itemAddonSelection = AddonSelection([addon for addon in self.resources.addons if isinstance(addon, ItemAddon)])
        self.survivorOfferingSelect = OfferingSelection(offerings=self.resources.offerings)
        self.itemSelection = SurvivorItemSelect(items=self.resources.items, icons=Globals.ITEM_ICONS, iconSize=Globals.ITEM_ICON_SIZE)
        self.itemSelection.selectionChanged.connect(lambda item: self.itemAddonSelection.filterAddons(
            lambda addon: isinstance(addon, ItemAddon) and addon.itemType == item.itemType if item is not None else False))
        self.survivorPerkSelection = PerkSelection([p for p in self.resources.perks if p.perkType == PerkType.Survivor])
        upperSurvivorWidget, upperSurvivorLayout = setQWidgetLayout(QWidget(), QHBoxLayout())
        upperSurvivorLayout.addWidget(self.survivorSelect)
        upperSurvivorLayout.addWidget(self.itemSelection)
        upperSurvivorLayout.addWidget(self.itemAddonSelection)
        survivorInfoLayout.addWidget(upperSurvivorWidget)
        survivorInfoLayout.addWidget(self.survivorPerkSelection)
        self.survivorMapSelection = MapSelect(self.resources.realms)
        self.survivorPointsTextBox = QLineEdit()
        self.survivorPointsTextBox.setValidator(nonNegativeIntValidator())
        self.survivorRankSpinner = QSpinBox()
        self.survivorRankSpinner.setRange(Globals.HIGHEST_RANK, Globals.LOWEST_RANK)
        self.survivorMatchDatePicker = QDateEdit(calendarPopup=True)
        self.survivorMatchDatePicker.setDate(QDate.currentDate())
        self.survivorMatchDatePicker.setDisplayFormat('dd-MM-yyyy')
        self.survivorMatchResultComboBox = QComboBox()
        self.partySizeSpinner = QSpinBox()
        self.partySizeSpinner.setRange(1, 4)  # minimum one person (you), maximum 4 people (max party size in DBD)
        otherMatchInfoWidget, otherMatchInfoLayout = setQWidgetLayout(QWidget(), QVBoxLayout())
        spinnersParentWidget, spinnersParentLayout = setQWidgetLayout(QWidget(), QHBoxLayout())
        for spinner, labelStr in zip([self.survivorRankSpinner, self.partySizeSpinner],
                                     ['Survivor rank', 'Party size']):
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
        for widget, labelStr in zip(widgets, ['Match date', 'Match result', '', 'Points']):
            cellWidget, cellLayout = setQWidgetLayout(QWidget(), QVBoxLayout())
            if labelStr:
                cellLayout.addWidget(QLabel(labelStr))
            cellLayout.addWidget(widget)
            otherMatchInfoLayout.addWidget(cellWidget)
        upperSurvivorMatchInfoWidget, upperSurvivorMatchInfoLayout = setQWidgetLayout(QWidget(), QHBoxLayout())
        upperSurvivorMatchInfoLayout.addWidget(otherMatchInfoWidget)
        upperSurvivorMatchInfoLayout.addSpacerItem(QSpacerItem(75, 1))
        upperSurvivorMatchInfoLayout.addWidget(self.survivorMapSelection)
        upperSurvivorMatchInfoLayout.addSpacerItem(QSpacerItem(35, 1))
        survivorMatchInfoLayout.addWidget(upperSurvivorMatchInfoWidget)
        self.survivorMatchResultComboBox.addItems(
            ' '.join(splitUpper(x.name)).lower().capitalize() for x in SurvivorMatchResult)
        self.facedKillerSelect = KillerSelect(self.resources.killers, icons=Globals.KILLER_ICONS, iconSize=Globals.CHARACTER_ICON_SIZE)
        lowerSurvivorMatchInfoWidget, lowerSurvivorMatchInfoLayout = setQWidgetLayout(QWidget(), QHBoxLayout())
        lowerSurvivorMatchInfoLayout.addWidget(self.facedKillerSelect)
        lowerSurvivorMatchInfoLayout.addSpacerItem(QSpacerItem(25, 1))
        lowerSurvivorMatchInfoLayout.addWidget(self.survivorOfferingSelect)
        survivorMatchInfoLayout.addWidget(lowerSurvivorMatchInfoWidget)
        self.addSurvivorMatchButton.setFixedWidth(150)
        survivorListLayout.setContentsMargins(5, 23, 5, 0)

    def __setupMenuBar(self):
        updateAction = QAction('Update game data and image database', self)
        updateAction.triggered.connect(self.__updateResources)
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
        menubar.setCornerWidget(self.unsavedChangesLabel, Qt.TopRightCorner)

    def __saveMatches(self):
        matchCount = len(self.currentlyAddedMatches)
        if matchCount <= 0:
            return

        def showSuccessMessageAndClearList():
            msgBox = QMessageBox()
            msgBox.setWindowTitle("Saving result")
            msgBox.setText("Matches saved successfully!")
            msgBox.exec_()
            self.statusBar().showMessage(f"Saved {matchCount} matches to database", 5000)
            self.currentlyAddedMatches.clear()
            self.__updateUnsavedChanges('')

        progressDialog = QProgressDialog()
        progressDialog.setWindowTitle("Saving data")
        progressDialog.setLabelText(f"Saving {matchCount} matches...")
        progressDialog.setRange(0,0)
        progressDialog.setFixedSize(500, 150)
        progressDialog.setCancelButton(None)
        progressDialog.setModal(True)

        self.saveWorker = DatabaseMatchListSaveWorker(self.currentlyAddedMatches)
        self.saveWorker.signals.finished.connect(showSuccessMessageAndClearList)
        self.threadPool.start(self.saveWorker)
        progressDialog.show()

    @confirmation(text='Resources update',informativeText='Do you really want to update resources? It might take a while.', title="Resources update")
    def __updateResources(self):
        progressDialog = QProgressDialog()
        progressDialog.setWindowTitle("Updating database")
        progressDialog.setModal(True)
        progressDialog.setCancelButton(None)
        progressDialog.setFixedSize(450, 75)
        progressDialog.setRange(0, 0)
        self.worker = DatabaseUpdateWorker()
        self.worker.signals.progressUpdated.connect(lambda s: progressDialog.setLabelText(s))
        self.worker.signals.finished.connect(progressDialog.close)
        self.threadPool.start(self.worker)
        progressDialog.show()


    def __loadMatchLogs(self):
        files, _ = QFileDialog.getOpenFileNames(self,"Select match log files",filter="Text files (*.txt)")
        if len(files) <= 0:
            return
        parser = DBDMatchParser(self.resources)
        loader = DBDMatchLogFileLoader(parser)
        progressDialog = QProgressDialog()
        progressDialog.setRange(0,0)
        progressDialog.setWindowTitle("Loading match log files")
        progressDialog.setCancelButton(None)
        progressDialog.setFixedSize(450, 100)
        progressDialog.setModal(True)
        self.loadWorker = LogFileLoadWorker(loader, files)
        self.loadWorker.signals.fileLoadStarted.connect(lambda fileName: progressDialog.setLabelText(f"Loading file: {fileName}"))
        self.loadWorker.signals.finished.connect(lambda l,e: progressDialog.close())
        self.loadWorker.signals.finished.connect(self.__showLoadedMatchData)
        self.threadPool.start(self.loadWorker)
        progressDialog.show()

    def __showLoadedMatchData(self, loadedGames: list[DBDMatch], errors: list[str]):
        dialog = LoadedGamesDisplayDialog(loadedGames, errors, title="Show loaded matches")
        result = dialog.exec_()
        if result == QDialog.Accepted:
            self.currentlyAddedMatches += loadedGames
            self.statusBar().showMessage(f"{len(loadedGames)}x matches loaded in", 7500)
            self.__updateUnsavedChanges("Unsaved changes!")

    def __showLogHelpWindow(self):
        pass

    def __exportDBAsLog(self):
        pass

    def __addMatchToList(self, _list: QListWidget, match: DBDMatch):
        matchWidget = DBDMatchListItem(match)
        listItem = QListWidgetItem()
        listItem.setSizeHint(matchWidget.sizeHint())
        _list.addItem(listItem)
        _list.setItemWidget(listItem, matchWidget)