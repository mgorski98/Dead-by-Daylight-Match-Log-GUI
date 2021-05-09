from PyQt5.QtCore import *
from PyQt5.QtGui import QIntValidator
from PyQt5.QtWidgets import QMainWindow, QWidget, QGridLayout, QHBoxLayout, QVBoxLayout, QLineEdit, QLabel, QSpinBox, \
    QDateEdit, QCalendarWidget
import sys
from guicontrols import ItemSelect, KillerSelect, AddonPopupSelect
import struct
from util import setQWidgetLayout

class MainWindow(QMainWindow):
    def __init__(self, parent=None, title='PyQt5 Application', windowSize=(800,600)):
        super(MainWindow, self).__init__(parent=parent)
        self.setWindowTitle(title)
        self.resize(windowSize[0], windowSize[1])
        centralWidget = QWidget()
        centralLayout = QVBoxLayout()
        centralWidget.setLayout(centralLayout)
        self.setCentralWidget(centralWidget)
        self.killerSelection = KillerSelect([])

        upperLayoutWidget, upperLayout = setQWidgetLayout(QWidget(), QHBoxLayout())
        upperLayoutWidget.setLayout(upperLayout)
        upperLayout.addWidget(self.killerSelection)

        eliminationsInfoWidget, eliminationsInfoLayout = setQWidgetLayout(QWidget(), QGridLayout())
        labels = ['Sacrifices', 'Kills (moris)', 'Disconnects']
        self.killsTextBox = QLineEdit()
        self.sacrificesTextBox = QLineEdit()
        self.disconnectsTextBox = QLineEdit()
        for label, textbox in zip(labels, [self.sacrificesTextBox, self.killsTextBox, self.disconnectsTextBox]):
            validator = QIntValidator()
            validator.setBottom(0)
            textbox.setValidator(validator)
            cellWidget = QWidget()
            cellLayout = QVBoxLayout()
            cellWidget.setLayout(cellLayout)
            cellLayout.addWidget(QLabel(label))
            cellLayout.addWidget(textbox)
            eliminationsInfoLayout.addWidget(cellWidget)
        upperLayout.addWidget(eliminationsInfoWidget)

        self.pointsTextBox = QLineEdit()
        validator = QIntValidator()
        validator.setBottom(0)
        self.pointsTextBox.setValidator(validator)
        self.killerMatchDatePicker = QDateEdit(calendarPopup=True)
        self.killerRankSpinner = QSpinBox()
        otherInfoWidget = QWidget()
        otherInfoLayout = QGridLayout()
        otherInfoWidget.setLayout(otherInfoLayout)
        labels = ['Match date','Points','Killer rank']
        for label, obj in zip(labels, [self.killerMatchDatePicker, self.pointsTextBox, self.killerRankSpinner]):
            cellWidget = QWidget()
            cellLayout = QVBoxLayout()
            cellWidget.setLayout(cellLayout)
            cellLayout.addWidget(QLabel(label))
            cellLayout.addWidget(obj)
            otherInfoLayout.addWidget(cellWidget)
        upperLayout.addWidget(otherInfoWidget)

        centralLayout.addWidget(upperLayoutWidget)
        middleLayoutWidget = QWidget()
        middleLayout = QHBoxLayout()
        middleLayoutWidget.setLayout(middleLayout)
        centralLayout.addWidget(middleLayoutWidget)

        killerAddonsWidget = QWidget()
        killerAddonsSelectLayout = QHBoxLayout()
        killerAddonsWidget.setLayout(killerAddonsSelectLayout)
        middleLayout.addWidget(killerAddonsWidget)
        lowerLayoutWidget = QWidget()
        lowerLayout = QHBoxLayout()
        lowerLayoutWidget.setLayout(lowerLayout)
        centralLayout.addWidget(lowerLayoutWidget)

        self.killerAddonSelection = None
        self.itemAddonSelection = None
        self.addonItemsSelectPopup = AddonPopupSelect([])
