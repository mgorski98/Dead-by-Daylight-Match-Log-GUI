from functools import partial
from typing import Optional, Union

from PyQt5 import QtCore, QtGui
from PyQt5.QtCore import Qt, QPoint
from PyQt5.QtGui import QPixmap, QIcon
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QPushButton, QLabel, QHBoxLayout, QComboBox, QAbstractItemView, \
    QDialog, QScrollArea, QGridLayout

from models import Killer, Survivor, KillerAddon, ItemAddon, Perk, PerkType, Offering, Item, ItemType

from abc import ABC, abstractmethod

#todo: create a control that displays a popup with all of the items (like perks, addons, etc.)

#control allowing selection by using arrow pushbuttons or a combobox
from util import clamp
from globaldata import *


class ItemSelect(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        layout = QVBoxLayout()
        self.setLayout(layout)
        self.leftButton, self.rightButton = QPushButton('<'), QPushButton('>')
        for button, func in zip([self.leftButton, self.rightButton], [self.prev, self.next]):
            button.clicked.connect(func)
        self.imageLabel = QLabel(self)
        imageSelectLayout = QHBoxLayout()
        imageSelectWidget = QWidget()
        imageSelectWidget.setLayout(imageSelectLayout)
        for i in [self.leftButton, self.imageLabel, self.rightButton]:
            imageSelectLayout.addWidget(i)
        layout.addWidget(imageSelectWidget)
        self.nameDisplayLabel = QLabel('<Select with arrows or from combobox>')
        self.itemSelectionComboBox = QComboBox(parent=self)
        layout.addWidget(self.nameDisplayLabel)
        layout.addWidget(self.itemSelectionComboBox)
        width = 25
        self.leftButton.setFixedWidth(width)
        self.rightButton.setFixedWidth(width)
        layout.addWidget(self.nameDisplayLabel)
        layout.addWidget(self.itemSelectionComboBox)
        self.nameDisplayLabel.setAlignment(Qt.AlignCenter)
        self.nameDisplayLabel.setFixedHeight(35)
        self.currentIndex = -1
        self.selectedItem = None

    @abstractmethod
    def next(self):
        pass

    @abstractmethod
    def prev(self):
        pass

    @abstractmethod
    def getSelectedItem(self):
        pass


class KillerSelect(ItemSelect):

    def __init__(self, killers: list[Killer], parent=None):
        super().__init__(parent=parent)
        self.killers = killers

    def _itemsPresent(self) -> bool:
        return len(self.killers) > 0

    def next(self):
        if not self._itemsPresent():
            return
        # selectPopup = AddonPopupSelect([str(i) for i in range(32)])
        # point = self.rightButton.rect().bottomRight()
        # globalPoint = self.mapToGlobal(point)
        # offsetPoint = QPoint(self.rightButton.width() * 3.5, self.rightButton.height() * 3)
        # selectPopup.move(globalPoint + offsetPoint)
        # result = selectPopup.selectAddon()
        self.currentIndex = clamp(self.currentIndex + 1, 0, len(self.killers) - 1)
        self.updateSelected()

    def prev(self):
        if not self._itemsPresent():
            return
        self.currentIndex = clamp(self.currentIndex - 1, 0, len(self.killers) - 1)
        self.updateSelected()

    def updateSelected(self):
        if self.selectedItem is None:
            return
        self.selectedItem = self.killers[self.currentIndex]
        self.nameDisplayLabel.setText(f'{self.selectedItem.killerName} - {self.selectedItem.killerAlias}')
        # self.imageLabel.setPixmap() #load icons and import them here

    def getSelectedItem(self):
        return self.selectedItem

class SurvivorSelect(ItemSelect):
    def __init__(self, survivors: list[Survivor], parent=None):
        super().__init__(parent)
        self.survivors = survivors

class SurvivorItemSelect(ItemSelect):
    def __init__(self, items: list[Item], itemFilter: Optional[ItemType], parent=None):
        super().__init__(parent)
        self.items = items
        self.filter = itemFilter


class PopupGridViewSelection(QDialog):
    def __init__(self, columns: int, parent=None):
        super().__init__(parent, Qt.Popup | Qt.FramelessWindowHint)
        layout = QGridLayout()
        self.setLayout(layout)
        self.columns = columns
        self.itemsLayout = QGridLayout()
        self.selectedItem = None
        mainWidget = QWidget()
        mainWidget.setLayout(self.itemsLayout)
        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)#okurwachybawiem
        scroll.setWidget(mainWidget)
        layout.addWidget(scroll)

    @abstractmethod
    def initPopupGrid(self):
        pass

    def selectItem(self, item):
        self.selectedItem = item
        self.accept()


class AddonPopupSelect(PopupGridViewSelection):


    def __init__(self, addons: list, parent=None):
        super().__init__(5, parent=parent)
        self.addons = addons
        self.initPopupGrid()


    def initPopupGrid(self):
        layout: QGridLayout = self.itemsLayout
        for index, addon in enumerate(self.addons):
            columnIndex = index % self.columns
            rowIndex = index // self.columns
            addonButton = QPushButton(addon)
            addonButton.setFixedSize(30, 30)
            addonButton.clicked.connect(partial(self.selectItem, addon))
            iconName = addon.addonName.lower().replace(' ', '-').replace('"','').replace(':', '')
            addonButton.setIcon(QIcon(ADDON_ICONS[iconName]))
            layout.addWidget(addonButton, rowIndex, columnIndex)

    def selectAddon(self) -> Optional[Union[KillerAddon, ItemAddon]]:
        return self.selectedItem if self.exec_() == QDialog.Accepted else None


class PerkPopupSelect(PopupGridViewSelection):

    def __init__(self, perks: list[Perk], parent=None):
        super().__init__(5, parent)
        self.initPopupGrid()

    def initPopupGrid(self):
        pass


class AddonSelect(QWidget):
    pass

class PerkSelect(QWidget):
    pass