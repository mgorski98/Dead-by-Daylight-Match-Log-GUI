from collections import namedtuple

from PyQt5.QtCore import *
from PyQt5.QtGui import QRegularExpressionValidator
from PyQt5.QtWidgets import QMainWindow, QWidget, QGridLayout, QHBoxLayout, QVBoxLayout, QLineEdit, QLabel, QSpinBox, \
    QDateEdit, QTabWidget, QAction, QMessageBox, QDialogButtonBox, QSpacerItem, QSizePolicy

from database import Database
from guicontrols import KillerSelect, AddonSelectPopup, AddonSelection, FacedSurvivorSelectionWindow, PerkSelection
from models import KillerAddon, Killer
from util import setQWidgetLayout, nonNegativeIntValidator, addWidgets
from globaldata import Globals


class MainWindow(QMainWindow):
    def __init__(self, parent=None, title='PyQt5 Application', windowSize=(800,600)):
        super(MainWindow, self).__init__(parent=parent)
        self.setWindowTitle(title)
        self.setContentsMargins(5, 5, 5, 5)
        self.resize(windowSize[0], windowSize[1])
        self.setCentralWidget(QTabWidget())
        killerWidget, killerLayout = setQWidgetLayout(QWidget(), QGridLayout())
        survivorWidget, survivorLayout = setQWidgetLayout(QWidget(), QVBoxLayout())
        self.centralWidget().addTab(killerWidget, "Killers")
        self.centralWidget().addTab(survivorWidget, "Survivors")
        killerMatchInfoTabWidget = QTabWidget()
        killerInfoWidget, killerInfoLayout = setQWidgetLayout(QWidget(), QVBoxLayout())
        killerMatchInfoWidget, killerMatchInfoLayout = setQWidgetLayout(QWidget(), QVBoxLayout())
        killerMatchInfoTabWidget.addTab(killerInfoWidget, "Killer info")
        killerMatchInfoTabWidget.addTab(killerMatchInfoWidget, "Match info")
        killerLayout.addWidget(killerMatchInfoTabWidget, 0, 0, 1, 3)
        killerListWidget, killerListLayout = setQWidgetLayout(QWidget(), QVBoxLayout())
        killerLayout.addWidget(killerListWidget, 0, 4, 1, 2)
        testKiller = Killer(killerAlias='The Trapper', killerName='Evan Macmillan')
        self.killerSelection = KillerSelect([testKiller], iconSize=Globals.CHARACTER_ICON_SIZE)
        #todo: first tab: killer info (killer, perks, add ons, etc.), second tab: match info (points, date, faced survivors, etc.)
        self.__setupMenuBar()

        self.pointsTextBox = QLineEdit()
        self.pointsTextBox.setValidator(nonNegativeIntValidator())
        self.killerMatchDatePicker = QDateEdit(calendarPopup=True)
        self.killerMatchDatePicker.setDate(QDate.currentDate())
        self.killerRankSpinner = QSpinBox()
        self.killerRankSpinner.setRange(Globals.HIGHEST_RANK, Globals.LOWEST_RANK)#lowest rank is 20, DBD ranks are going down the better they are, so rank 1 is the best
        otherInfoWidget, otherInfoLayout = setQWidgetLayout(QWidget(),QGridLayout())
        for label, obj in zip(['Match date','Points','Killer rank'], [self.killerMatchDatePicker, self.pointsTextBox, self.killerRankSpinner]):
            cellWidget, cellLayout = setQWidgetLayout(QWidget(),QVBoxLayout())
            addWidgets(cellLayout, QLabel(label), obj)
            otherInfoLayout.addWidget(cellWidget)


        self.facedSurvivorSelection = FacedSurvivorSelectionWindow([])
        self.killerPerkSelection = PerkSelection([])
        self.killerAddonSelection = AddonSelection([KillerAddon(addonName='Bloody Coil', killer=testKiller)])
        self.itemAddonSelection = None
        self.addonItemsSelectPopup = AddonSelectPopup([])

        killerInfoUpperRowWidget, killerInfoUpperRowLayout = setQWidgetLayout(QWidget(), QHBoxLayout())
        killerInfoUpperRowLayout.addWidget(self.killerSelection)
        killerInfoUpperRowLayout.addWidget(self.killerAddonSelection)
        killerInfoLayout.addWidget(killerInfoUpperRowWidget)
        killerInfoLowerRowWidget, killerInfoLowerRowLayout = setQWidgetLayout(QWidget(), QHBoxLayout())
        killerInfoLowerRowLayout.addWidget(self.killerPerkSelection)
        killerInfoLayout.addWidget(killerInfoLowerRowWidget)


    def setupKillerForm(self) -> QWidget:
        pass

    def setupSurvivorForm(self):
        pass

    def __setupMenuBar(self):
        updateAction = QAction('Update game data and image database', self)
        updateAction.triggered.connect(self.__confirmUpdate)
        loadLogAction = QAction('Load match log data', self)
        loadLogAction.triggered.connect(self.__loadMatchLogs)
        logHelpAction = QAction('Show match log file help', self)
        logHelpAction.triggered.connect(self.__showLogHelpWindow)
        menubar = self.menuBar()
        fileMenu = menubar.addMenu('&File')
        optionsMenu = menubar.addMenu('&Options')
        helpMenu = menubar.addMenu('&Help')
        optionsMenu.addAction(updateAction)
        fileMenu.addAction(loadLogAction)
        helpMenu.addAction(logHelpAction)

    def __confirmUpdate(self):
        msgBox = QMessageBox()
        msgBox.setIcon(QMessageBox.Question)
        msgBox.setText('Resources update')
        msgBox.setInformativeText('Do you really want to update resources? It might take a while.')
        msgBox.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        result = msgBox.exec_()
        if result == QMessageBox.Yes:
            Database.update() #update here

    def __loadMatchLogs(self):
        pass

    def __showLogHelpWindow(self):
        pass