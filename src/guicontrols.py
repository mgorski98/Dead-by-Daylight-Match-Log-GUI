from abc import abstractmethod
from functools import partial
from typing import Optional, Union

from PyQt5.QtCore import *
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QPushButton, QLabel, QHBoxLayout, QComboBox, QDialog, QScrollArea, \
    QGridLayout, QSizePolicy, QSpacerItem

from globaldata import *
from models import Killer, Survivor, KillerAddon, ItemAddon, Perk, Item, ItemType
from util import clampReverse, setQWidgetLayout


class ItemSelect(QWidget):

    def __init__(self, iconSize=(100,100), parent=None):
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
        # self.nameDisplayLabel.setFixedSize(self.nameDisplayLabel.width(), self.nameDisplayLabel.height())
        self.itemSelectionComboBox = QComboBox(parent=self)
        self.itemSelectionComboBox.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        layout.addWidget(self.nameDisplayLabel)
        layout.addWidget(self.itemSelectionComboBox)
        width = 25
        self.leftButton.setFixedWidth(width)
        self.rightButton.setFixedWidth(width)
        layout.addWidget(self.nameDisplayLabel)
        layout.addWidget(self.itemSelectionComboBox)
        self.nameDisplayLabel.setAlignment(Qt.AlignCenter)
        self.nameDisplayLabel.setFixedHeight(35)
        self.nameDisplayLabel.setStyleSheet("font-weight: bold;")
        self.imageLabel.setScaledContents(True)
        self.imageLabel.setFixedSize(iconSize[0],iconSize[1])
        self.currentIndex = 0
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

    def __init__(self, killers: list[Killer], iconSize=(100,100), parent=None):
        super().__init__(parent=parent, iconSize=iconSize)
        self.killers = killers
        self.itemSelectionComboBox.setFixedHeight(60)
        self.itemSelectionComboBox.setIconSize(QSize(iconSize[0] / 4,iconSize[1] / 4))
        self.killers.append(Killer(killerName='Evan Macmillan', killerAlias='The Trapper'))
        killerItems = map(str, self.killers)
        killerIconsCombo = map(lambda killer: QIcon(Globals.KILLER_ICONS[killer.killerAlias.lower().replace(' ', '-')]), self.killers)
        for killerStr, icon in zip(killerItems, killerIconsCombo):
            self.itemSelectionComboBox.addItem(icon, killerStr)
        self.itemSelectionComboBox.activated.connect(self.selectFromIndex)
        self.selectFromIndex(0)

    def selectFromIndex(self, index):
        self.selectedItem = self.killers[index]
        self.currentIndex = index
        self.updateSelected()

    def _itemsPresent(self) -> bool:
        return len(self.killers) > 0

    def next(self):
        self.__updateIndex(self.currentIndex + 1)
        # selectPopup = AddonSelectPopup([KillerAddon(killer=self.killers[0],addonName='Party Bottle')])
        # point = self.rightButton.rect().bottomRight()
        # globalPoint = self.mapToGlobal(point)
        # offsetPoint = QPoint(self.rightButton.width() * 3.5, self.rightButton.height() * 3)
        # selectPopup.move(globalPoint + offsetPoint)
        # result = selectPopup.selectAddon()
        # print(result)

    def prev(self):
        self.__updateIndex(self.currentIndex - 1)

    def __updateIndex(self, value: int):
        if not self._itemsPresent():
            return
        self.currentIndex = clampReverse(value, 0, len(self.killers) - 1)
        self.updateSelected()

    def updateSelected(self):
        if self.selectedItem is None:
            return
        self.selectedItem = self.killers[self.currentIndex]
        self.nameDisplayLabel.setText(str(self.selectedItem))
        icon = Globals.KILLER_ICONS[self.selectedItem.killerAlias.lower().replace(' ', '-')]
        self.imageLabel.setFixedSize(icon.width(),icon.height())
        self.imageLabel.setPixmap(icon) #load icons and import them here

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


class GridViewSelectionPopup(QDialog):
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
        scroll.setWidgetResizable(True)
        scroll.setWidget(mainWidget)
        layout.addWidget(scroll)

    @abstractmethod
    def initPopupGrid(self):
        pass

    def selectItem(self, item):
        self.selectedItem = item
        self.accept()


class AddonSelectPopup(GridViewSelectionPopup):


    def __init__(self, addons: list[Union[ItemAddon, KillerAddon]], parent=None):
        super().__init__(5, parent=parent)
        self.addons = addons
        self.initPopupGrid()


    def initPopupGrid(self):
        for index, addon in enumerate(self.addons):
            columnIndex = index % self.columns
            rowIndex = index // self.columns
            addonButton = QPushButton()
            addonButton.setFixedSize(OTHER_ICONS_SIZE[0], OTHER_ICONS_SIZE[1])
            addonButton.setIconSize(QSize(OTHER_ICONS_SIZE[0], OTHER_ICONS_SIZE[1]))
            addonButton.clicked.connect(partial(self.selectItem, addon))
            addonButton.setFlat(True)
            iconName = addon.addonName.lower().replace(' ', '-').replace('"','').replace(':', '')
            addonIcon = QIcon(ADDON_ICONS[iconName])
            addonButton.setIcon(addonIcon)
            self.itemsLayout.addWidget(addonButton, rowIndex, columnIndex)

    def selectAddon(self) -> Optional[Union[KillerAddon, ItemAddon]]:
        return self.selectedItem if self.exec_() == QDialog.Accepted else None


class PerkPopupSelect(GridViewSelectionPopup):

    def __init__(self, perks: list[Perk], parent=None):
        super().__init__(5, parent)
        self.perks = perks
        self.initPopupGrid()

    def initPopupGrid(self):
        pass


class AddonSelect(QWidget):

    def __init__(self, addons: list[Union[ItemAddon, KillerAddon]], parent=None):
        super().__init__(parent)
        self.addons = addons
        self.popupSelect = AddonSelectPopup(self.addons)
        self.addon1Button = QPushButton()
        self.addon2Button = QPushButton()
        self.defaultIcon = QIcon(Globals.DEFAULT_ICON_OTHER)
        self.addon1Button.setIcon(self.defaultIcon)
        self.addon2Button.setIcon(self.defaultIcon)
        self.addon1Button.setIconSize(QSize(Globals.OTHER_ICONS_SIZE[0], Globals.OTHER_ICONS_SIZE[1]))
        self.addon2Button.setIconSize(QSize(Globals.OTHER_ICONS_SIZE[0], Globals.OTHER_ICONS_SIZE[1]))
        self.addon1Button.setFixedSize(Globals.OTHER_ICONS_SIZE[0], Globals.OTHER_ICONS_SIZE[1])
        self.addon2Button.setFixedSize(Globals.OTHER_ICONS_SIZE[0], Globals.OTHER_ICONS_SIZE[1])
        self.addon1Button.setFlat(True)
        self.addon2Button.setFlat(True)
        self.addon1Button.clicked.connect(lambda: print())
        self.addon2Button.clicked.connect(lambda: print())
        mainLayout = QVBoxLayout()
        self.setLayout(mainLayout)
        layout = QHBoxLayout()
        addonsLabel = QLabel('Killer addons')
        addonsLabel.setFixedHeight(25)
        addonsLabel.setAlignment(Qt.AlignCenter)
        mainLayout.addWidget(addonsLabel)
        mainLayout.addLayout(layout)
        leftLayout = QVBoxLayout()
        rightLayout = QVBoxLayout()
        self.addon1NameLabel = QLabel('')
        self.addon1NameLabel.setAlignment(Qt.AlignCenter)
        self.addon2NameLabel = QLabel('')
        self.addon2NameLabel.setAlignment(Qt.AlignCenter)
        self.addon1NameLabel.setFixedHeight(25)
        self.addon2NameLabel.setFixedHeight(25)
        self.addon1NameLabel.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        self.addon2NameLabel.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        layout.addLayout(leftLayout)
        layout.addLayout(rightLayout)
        leftLayout.addWidget(self.addon1Button)
        rightLayout.addWidget(self.addon2Button)
        leftLayout.addWidget(self.addon1NameLabel)
        rightLayout.addWidget(self.addon2NameLabel)
        leftLayout.setAlignment(self.addon1Button, Qt.AlignCenter)
        rightLayout.setAlignment(self.addon2Button, Qt.AlignCenter)
        leftLayout.addSpacerItem(QSpacerItem(5, 125))
        rightLayout.addSpacerItem(QSpacerItem(5, 125))


class PerkSelect(QWidget):

    def __init__(self, perks: list[Perk], parent=None):
        super().__init__(parent)
        self.perks = perks

