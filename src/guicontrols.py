from abc import abstractmethod
from functools import partial
from typing import Union

from PyQt5.QtCore import *
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QPushButton, QLabel, QHBoxLayout, QComboBox, QDialog, QScrollArea, \
    QGridLayout, QSizePolicy, QSpacerItem, QButtonGroup, QRadioButton

from globaldata import *
from models import Killer, Survivor, KillerAddon, ItemAddon, Perk, Item, ItemType, FacedSurvivorState, Offering
from util import clampReverse, splitUpper, setQWidgetLayout, addWidgets

AddonSelectionResult = Optional[Union[KillerAddon, ItemAddon]]


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
        width, height = 35, 50
        self.leftButton.setFixedSize(width, height)
        self.rightButton.setFixedSize(width, height)
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
        self.itemSelectionComboBox.setIconSize(QSize(iconSize[0] // 4,iconSize[1] // 4))
        # self.killers.append(Killer(killerName='Evan Macmillan', killerAlias='The Trapper'))
        killerItems = map(str, self.killers)
        killerIconsCombo = map(lambda killer: QIcon(Globals.KILLER_ICONS[killer.killerAlias.lower().replace(' ', '-')]), self.killers)
        for killerStr, icon in zip(killerItems, killerIconsCombo):
            self.itemSelectionComboBox.addItem(icon, killerStr)
        self.itemSelectionComboBox.activated.connect(self.selectFromIndex)
        # self.selectFromIndex(0)

    def selectFromIndex(self, index):
        self.selectedItem = self.killers[index]
        self.currentIndex = index
        self.updateSelected()

    def _itemsPresent(self) -> bool:
        return len(self.killers) > 0

    def next(self):
        self.__updateIndex(self.currentIndex + 1)

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

    def next(self):
        pass

    def prev(self):
        pass

    def getSelectedItem(self):
        pass


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
            addonButton.setFixedSize(Globals.ADDON_ICON_SIZE[0], Globals.ADDON_ICON_SIZE[1])
            addonButton.setIconSize(QSize(Globals.ADDON_ICON_SIZE[0], Globals.ADDON_ICON_SIZE[1]))
            addonButton.clicked.connect(partial(self.selectItem, addon))
            addonButton.setFlat(True)
            iconName = addon.addonName.lower().replace(' ', '-').replace('"','').replace(':', '')
            addonIcon = QIcon(Globals.ADDON_ICONS[iconName])
            addonButton.setIcon(addonIcon)
            self.itemsLayout.addWidget(addonButton, rowIndex, columnIndex)

    def selectAddon(self) -> AddonSelectionResult:
        return self.selectedItem if self.exec_() == QDialog.Accepted else None


class PerkPopupSelect(GridViewSelectionPopup):

    def __init__(self, perks: list[Perk], parent=None):
        super().__init__(5, parent)
        self.perks = perks
        self.initPopupGrid()

    def initPopupGrid(self):
        pass

    def selectPerk(self) -> Optional[Perk]:
        return self.selectedItem if self.exec_() == QDialog.accepted else None

class AddonSelection(QWidget):

    def __init__(self, addons: list[Union[ItemAddon, KillerAddon]], parent=None):
        super().__init__(parent)
        self.addons = addons
        self.selectedAddons: dict[int, AddonSelectionResult] = {0: None, 1: None}
        self.popupSelect = AddonSelectPopup(self.addons)
        self.defaultIcon = QIcon(Globals.DEFAULT_ADDON_ICON)
        mainLayout = QVBoxLayout()
        self.setLayout(mainLayout)
        layout = QHBoxLayout()
        addonsLabel = QLabel('Killer addons')
        addonsLabel.setStyleSheet("font-weight: bold")
        addonsLabel.setFixedHeight(25)
        addonsLabel.setAlignment(Qt.AlignCenter)
        mainLayout.addSpacerItem(QSpacerItem(5, 25))
        mainLayout.addWidget(addonsLabel)
        mainLayout.addLayout(layout)
        leftLayout = QVBoxLayout()
        rightLayout = QVBoxLayout()
        self.addon1NameLabel = self.__createLabel()
        self.addon2NameLabel = self.__createLabel()
        self.addon1Button = self.__createIconButton(self.addon1NameLabel, self.defaultIcon, index = 0)
        self.addon2Button = self.__createIconButton(self.addon2NameLabel, self.defaultIcon, index = 1)
        layout.addLayout(leftLayout)
        layout.addLayout(rightLayout)
        leftLayout.addWidget(self.addon1Button)
        rightLayout.addWidget(self.addon2Button)
        leftLayout.addWidget(self.addon1NameLabel)
        rightLayout.addWidget(self.addon2NameLabel)
        leftLayout.setAlignment(self.addon1Button, Qt.AlignCenter)
        rightLayout.setAlignment(self.addon2Button, Qt.AlignCenter)
        leftLayout.addSpacerItem(QSpacerItem(5, 75))
        rightLayout.addSpacerItem(QSpacerItem(5, 75))

    def __createLabel(self):
        lbl = QLabel('No addon')
        lbl.setAlignment(Qt.AlignCenter)
        lbl.setFixedHeight(25)
        lbl.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        lbl.setWordWrap(True)
        return lbl

    def __createIconButton(self, label: QLabel, icon=None, index: int=0):
        btn = QPushButton()
        if icon is not None:
            btn.setIcon(icon)
        btn.setIconSize(QSize(Globals.ADDON_ICON_SIZE[0], Globals.ADDON_ICON_SIZE[1]))
        btn.setFixedSize(Globals.ADDON_ICON_SIZE[0], Globals.ADDON_ICON_SIZE[1])
        btn.setFlat(True)
        btn.clicked.connect(partial(self.__showAddonPopup, btn, label, index))
        return btn

    def __showAddonPopup(self, btnToUpdate: QPushButton, lblToUpdate: QLabel, index: int):
        point = btnToUpdate.rect().bottomLeft()
        globalPoint = btnToUpdate.mapToGlobal(point)
        self.popupSelect.move(globalPoint)
        addon = self.popupSelect.selectAddon()
        self.selectedAddons[index] = addon
        #todo: if addon is not none then set icon on button
        if addon is not None:
            pixmap = Globals.ADDON_ICONS[addon.addonName.lower().replace('"', '').replace(" ", '-')]
            btnToUpdate.setIcon(QIcon(pixmap))
            lblToUpdate.setText(addon.addonName)


class PerkSelection(QWidget):

    def __init__(self, perks: list[Perk], parent=None):
        super().__init__(parent)
        self.perks = perks
        self.popupSelection = PerkPopupSelect(self.perks)
        self.selectedPerks: dict[int, Optional[Perk]] = {n:None for n in range(4)}
        self.defaultPerkIcon = QIcon(Globals.DEFAULT_PERK_ICON)
        self.setLayout(QVBoxLayout())
        l = QLabel("Killer perks")
        l.setStyleSheet("font-weight: bold")
        l.setAlignment(Qt.AlignCenter)
        self.layout().addWidget(l)
        perksWidget, perksLayout = setQWidgetLayout(QWidget(), QHBoxLayout())
        self.layout().addWidget(perksWidget)
        for i in range(4):
            sublayout = QVBoxLayout()
            sublayout.addSpacerItem(QSpacerItem(1,50))
            perksLayout.addLayout(sublayout)
            button = QPushButton()
            button.setFlat(True)
            button.setFixedSize(Globals.PERK_ICON_SIZE[0], Globals.PERK_ICON_SIZE[1])
            button.setIconSize(QSize(Globals.PERK_ICON_SIZE[0], Globals.PERK_ICON_SIZE[1]))
            button.setIcon(self.defaultPerkIcon)
            sublayout.addWidget(button)
            label = QLabel('No perk')
            label.setAlignment(Qt.AlignCenter)
            label.setWordWrap(True)
            sublayout.addSpacerItem(QSpacerItem(1, 50))
            sublayout.addWidget(label)
            sublayout.setAlignment(button, Qt.AlignCenter)
            button.clicked.connect(partial(self.__selectPerkAndUpdateUI, button, label, i))

    def __selectPerkAndUpdateUI(self, btn: QPushButton, label: QLabel, index: int=0):
        point = btn.rect().bottomLeft()
        globalPoint = btn.mapToGlobal(point)
        self.popupSelection.move(globalPoint)
        perk = self.popupSelection.selectPerk()
        if perk is not None:
            label.setText(f'{perk.perkName} {"I" * perk.perkTier}')
            self.selectedPerks[index] = perk
            #todo: set perk icon




class FacedSurvivorSelect(ItemSelect):

    def __init__(self, survivors: list[Survivor], iconSize=(112,156), parent=None):
        super().__init__(parent=parent, iconSize=iconSize)
        self.survivors = survivors
        self.statusButtonGroup = QButtonGroup()
        self.survivorState: Optional[FacedSurvivorState] = None
        for state in FacedSurvivorState:
            buttonText = ' '.join(splitUpper(state.name)).lower().capitalize()
            selectButton = QRadioButton(buttonText)
            selectButton.clicked.connect(partial(self.setState, state))
            self.layout().addWidget(selectButton)

    def getSelectedItem(self):
        pass

    def next(self):
        pass

    def prev(self):
        pass

    def setState(self, state: FacedSurvivorState):
        self.survivorState = state

class FacedSurvivorSelectionWindow(QWidget):

    def __init__(self, survivors: list[Survivor], parent=None):
        super().__init__(parent)
        self.survivors = survivors
        self.selections = {n: FacedSurvivorSelect(self.survivors) for n in range(4)}
        mainLayout = QHBoxLayout()
        self.setLayout(mainLayout)
        for key, value in self.selections.items():
            mainLayout.addWidget(value)


class OfferingSelectPopup(GridViewSelectionPopup):

    def __init__(self, offerings: list[Offering], parent=None):
        super().__init__(5, parent)
        self.offerings = offerings
        self.selectedItem = None
        self.initPopupGrid()

    def initPopupGrid(self):
        for index, offering in enumerate(self.offerings):
            columnIndex = index % self.columns
            rowIndex = index // self.columns
            btn = QPushButton()
            btn.setFixedSize(Globals.OFFERING_ICON_SIZE[0], Globals.OFFERING_ICON_SIZE[1])
            btn.setIconSize(QSize(Globals.OFFERING_ICON_SIZE[0], Globals.OFFERING_ICON_SIZE[1]))
            btn.clicked.connect(partial(self.selectItem, offering))
            btn.setFlat(True)
            iconName = offering.offeringName.lower().replace(' ', '-').replace('"', '').replace(':', '')
            icon = QIcon(Globals.OFFERING_ICONS[iconName])
            btn.setIcon(icon)
            self.itemsLayout.addWidget(btn, rowIndex, columnIndex)

    def selectOffering(self):
        return self.selectedItem if self.exec_() == QDialog.Accepted else None

    def selectItem(self, item):
        self.selectedItem = item
        self.accept()

class OfferingSelection(QWidget):

    def __init__(self, offerings: list[Offering], parent=None):
        super().__init__(parent)
        self.offerings = offerings
        self.popupSelection = OfferingSelectPopup(self.offerings)
        self.defaultIcon = QIcon(Globals.DEFAULT_OFFERING_ICON)
        self.selectedItem = None
        offeringLabel = QLabel('No offering')
        label = QLabel('Offering')
        label.setAlignment(Qt.AlignCenter)
        label.setStyleSheet("font-weight: bold")
        label.setFixedHeight(20)
        offeringLabel.setAlignment(Qt.AlignCenter)
        offeringLabel.setFixedHeight(20)
        offeringLabel.setWordWrap(True)
        selectionButton = QPushButton()
        selectionButton.setFlat(True)
        size = QSize(Globals.OFFERING_ICON_SIZE[0], Globals.OFFERING_ICON_SIZE[1])
        selectionButton.setIconSize(size)
        selectionButton.setFixedSize(size)
        selectionButton.setIcon(self.defaultIcon)
        selectionButton.clicked.connect(partial(self.__showOfferingPopup, selectionButton, offeringLabel))
        self.setLayout(QVBoxLayout())
        self.layout().addSpacerItem(QSpacerItem(1, 30))
        self.layout().addWidget(label)
        self.layout().addWidget(selectionButton)
        self.layout().addWidget(offeringLabel)
        self.layout().addSpacerItem(QSpacerItem(1, 77.5))
        self.layout().setAlignment(selectionButton, Qt.AlignCenter)

    def __showOfferingPopup(self, btn: QPushButton, label: QLabel):
        point = btn.rect().bottomLeft()
        globalPoint = btn.mapToGlobal(point)
        self.popupSelection.move(globalPoint)
        offering = self.popupSelection.selectOffering()
        if offering is not None:
            pixmap: QPixmap = Globals.OFFERING_ICONS[offering.offeringName.lower().replace(':','').replace(' ', '-').replace('"', '')]
            btn.setIcon(QIcon(pixmap))
            label.setText(offering.offeringName)
