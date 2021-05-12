from PyQt5.QtCore import *
from PyQt5.QtGui import QRegularExpressionValidator
from PyQt5.QtWidgets import QMainWindow, QWidget, QGridLayout, QHBoxLayout, QVBoxLayout, QLineEdit, QLabel, QSpinBox, \
    QDateEdit, QTabWidget, QAction, QMessageBox, QDialogButtonBox, QSpacerItem

from database import Database
from guicontrols import KillerSelect, AddonSelectPopup, AddonSelect
from util import setQWidgetLayout, nonNegativeIntValidator, addWidgets
from globaldata import Globals


#todo: remove textboxes for eliminations (we will have eliminations info from the actual list of faced survivors)
class MainWindow(QMainWindow):
    def __init__(self, parent=None, title='PyQt5 Application', windowSize=(800,600)):
        super(MainWindow, self).__init__(parent=parent)
        self.setWindowTitle(title)
        self.setContentsMargins(5, 5, 5, 5)
        self.resize(windowSize[0], windowSize[1])
        self.setCentralWidget(QTabWidget())
        killerWidget, centralLayout = setQWidgetLayout(QWidget(), QVBoxLayout())
        self.centralWidget().addTab(killerWidget, "Killers")
        self.killerSelection = KillerSelect([], iconSize=Globals.CHARACTER_ICON_SIZE)
        upperLayout = QHBoxLayout()
        centralLayout.addLayout(upperLayout)
        upperLayout.addWidget(self.killerSelection)

        self.__setupMenuBar()

        # eliminationsInfoWidget, eliminationsInfoLayout = setQWidgetLayout(QWidget(), QGridLayout())
        # self.killsTextBox, self.sacrificesTextBox, self.disconnectsTextBox = QLineEdit(), QLineEdit(), QLineEdit()
        # validator = QRegularExpressionValidator(QRegularExpression('[0-4]{1}'))
        # for label, textbox in zip(['Sacrifices', 'Kills (moris)', 'Disconnects'], [self.sacrificesTextBox, self.killsTextBox, self.disconnectsTextBox]):
        #     textbox.setValidator(validator)
        #     cellWidget, cellLayout = setQWidgetLayout(QWidget(), QVBoxLayout())
        #     addWidgets(cellLayout, QLabel(label), textbox)
        #     eliminationsInfoLayout.addWidget(cellWidget)
        # upperLayout.addWidget(eliminationsInfoWidget)

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
        upperLayout.addSpacerItem(QSpacerItem(75,1))
        upperLayout.addWidget(otherInfoWidget)
        upperLayout.addSpacerItem(QSpacerItem(75,1))

        lowerLayoutWidget, lowerLayout = setQWidgetLayout(QWidget(), QHBoxLayout())
        centralLayout.addWidget(lowerLayoutWidget)

        self.killerAddonSelection = AddonSelect([])
        upperLayout.addWidget(self.killerAddonSelection)
        self.itemAddonSelection = None
        self.addonItemsSelectPopup = AddonSelectPopup([])
        centralLayout.addSpacerItem(QSpacerItem(1, 150))


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