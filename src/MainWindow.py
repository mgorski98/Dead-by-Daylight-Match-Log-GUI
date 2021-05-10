from PyQt5.QtCore import *
from PyQt5.QtGui import QIntValidator
from PyQt5.QtWidgets import QMainWindow, QWidget, QGridLayout, QHBoxLayout, QVBoxLayout, QLineEdit, QLabel, QSpinBox, \
    QDateEdit, QCalendarWidget
import sys
from guicontrols import ItemSelect, KillerSelect, AddonPopupSelect
import struct
from util import setQWidgetLayout, nonNegativeIntValidator, addWidgets
from globaldata import CHARACTER_ICON_SIZE


class MainWindow(QMainWindow):
    def __init__(self, parent=None, title='PyQt5 Application', windowSize=(800,600)):
        super(MainWindow, self).__init__(parent=parent)
        self.setWindowTitle(title)
        self.resize(windowSize[0], windowSize[1])
        centralWidget = QWidget()
        centralLayout = QVBoxLayout()
        centralWidget.setLayout(centralLayout)
        self.setCentralWidget(centralWidget)
        self.killerSelection = KillerSelect([], iconSize=CHARACTER_ICON_SIZE)
        upperLayout = QHBoxLayout()
        centralLayout.addLayout(upperLayout)
        upperLayout.addWidget(self.killerSelection)

        eliminationsInfoWidget, eliminationsInfoLayout = setQWidgetLayout(QWidget(), QGridLayout())
        labels = ['Sacrifices', 'Kills (moris)', 'Disconnects']
        self.killsTextBox = QLineEdit()
        self.sacrificesTextBox = QLineEdit()
        self.disconnectsTextBox = QLineEdit()
        for label, textbox in zip(labels, [self.sacrificesTextBox, self.killsTextBox, self.disconnectsTextBox]):
            textbox.setValidator(nonNegativeIntValidator())
            cellWidget, cellLayout = setQWidgetLayout(QWidget(), QVBoxLayout())
            addWidgets(cellLayout, QLabel(label), textbox)
            eliminationsInfoLayout.addWidget(cellWidget)
        upperLayout.addWidget(eliminationsInfoWidget)

        self.pointsTextBox = QLineEdit()
        self.pointsTextBox.setValidator(nonNegativeIntValidator())
        self.killerMatchDatePicker = QDateEdit(calendarPopup=True)
        self.killerMatchDatePicker.setDate(QDate.currentDate())
        self.killerRankSpinner = QSpinBox()
        otherInfoWidget, otherInfoLayout = setQWidgetLayout(QWidget(),QGridLayout())
        labels = ['Match date','Points','Killer rank']
        for label, obj in zip(labels, [self.killerMatchDatePicker, self.pointsTextBox, self.killerRankSpinner]):
            cellWidget, cellLayout = setQWidgetLayout(QWidget(),QVBoxLayout())
            addWidgets(cellLayout, QLabel(label), obj)
            otherInfoLayout.addWidget(cellWidget)
        upperLayout.addWidget(otherInfoWidget)

        # centralLayout.addWidget(upperLayoutWidget)
        middleLayoutWidget, middleLayout = setQWidgetLayout(QWidget(), QHBoxLayout())
        centralLayout.addWidget(middleLayoutWidget)
        killerAddonsWidget, killerAddonsSelectLayout = setQWidgetLayout(QWidget(),QHBoxLayout())
        middleLayout.addWidget(killerAddonsWidget)

        lowerLayoutWidget, lowerLayout = setQWidgetLayout(QWidget(), QHBoxLayout())
        centralLayout.addWidget(lowerLayoutWidget)

        self.killerAddonSelection = None
        self.itemAddonSelection = None
        self.addonItemsSelectPopup = AddonPopupSelect([])
