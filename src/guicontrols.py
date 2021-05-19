import operator
from abc import abstractmethod
from functools import partial
from typing import Union, Callable

from PyQt5.QtCore import *
from PyQt5.QtGui import QIcon, QPaintEvent, QPalette
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QPushButton, QLabel, QHBoxLayout, QComboBox, QDialog, QScrollArea, \
    QGridLayout, QSizePolicy, QSpacerItem, QButtonGroup, QRadioButton, QStylePainter, QStyleOptionComboBox, QStyle, \
    QStyledItemDelegate, QStyleOptionViewItem, QLineEdit

from globaldata import *
from models import Killer, Survivor, KillerAddon, ItemAddon, Perk, Item, ItemType, FacedSurvivorState, Offering, \
    GameMap, Realm, FacedSurvivor
from util import clampReverse, splitUpper, setQWidgetLayout, addWidgets, clearLayout, toResourceName

AddonSelectionResult = Optional[Union[KillerAddon, ItemAddon]]

#todo: change access to Globals to passing certain parameters in a set function or a constructor

class IconDropDownComboBox(QComboBox):#combobox with icons in dropdown but without them on currently selected item

    def paintEvent(self, e: QPaintEvent) -> None:
        painter = QStylePainter(self)
        painter.setPen(self.palette().color(QPalette.Text))
        opt = QStyleOptionComboBox()
        self.initStyleOption(opt)
        opt.currentIcon = QIcon()
        opt.iconSize = QSize()
        painter.drawComplexControl(QStyle.CC_ComboBox, opt)
        painter.drawControl(QStyle.CE_ComboBoxLabel, opt)


class ItemSelect(QWidget):

    selectionChanged = pyqtSignal(object)

    def __init__(self, items: list, iconSize=(100,100), parent=None):
        super().__init__(parent=parent)
        self.items = items
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
        self.nameDisplayLabel = QLabel('Select an item')
        self.itemSelectionComboBox = IconDropDownComboBox()
        self.itemSelectionComboBox.view().setIconSize(QSize(iconSize[0]//4,iconSize[1]//4))
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
        self.imageLabel.setFixedSize(*iconSize)
        self.currentIndex = 0
        self.selectedItem = None

    def _itemsPresent(self):
        return len(self.items) > 0

    def _updateIndex(self, index: int):
        if not self._itemsPresent():
            return
        self.currentIndex = clampReverse(index, 0, len(self.items) - 1)
        self.selectFromIndex(self.currentIndex)
        self.updateSelected()

    @abstractmethod
    def updateSelected(self):
        pass

    def next(self):
        self._updateIndex(self.currentIndex + 1)

    def prev(self):
        self._updateIndex(self.currentIndex - 1)

    def getSelectedItem(self):
        return self.selectedItem

    def selectFromIndex(self, index: int):
        self.selectedItem = self.items[index]
        self.selectionChanged.emit(self.selectedItem)
        self.currentIndex = index
        self.updateSelected()

class KillerSelect(ItemSelect):

    def __init__(self, killers: list[Killer], iconSize=(100,100), parent=None):
        super().__init__(items=killers, parent=parent, iconSize=iconSize)
        killerItems = map(str, self.items)
        killerIconsCombo = map(lambda killer: QIcon(Globals.KILLER_ICONS[toResourceName(killer.killerAlias)]), self.items)
        for killerStr, icon in zip(killerItems, killerIconsCombo):
            self.itemSelectionComboBox.addItem(icon, killerStr)
        self.itemSelectionComboBox.activated.connect(self.selectFromIndex)
        self.selectFromIndex(0)

    def updateSelected(self):
        if self.selectedItem is None:
            return
        self.nameDisplayLabel.setText(str(self.selectedItem))
        icon = Globals.KILLER_ICONS[toResourceName(self.selectedItem.killerAlias)]
        self.imageLabel.setFixedSize(icon.width(),icon.height())
        self.imageLabel.setPixmap(icon)


class SurvivorSelect(ItemSelect):


    def __init__(self, survivors: list[Survivor], iconSize=(100,100), parent=None):
        super().__init__(parent=parent,items=survivors, iconSize=iconSize)
        survivorItems = map(lambda survivor: survivor.survivorName, self.items)
        survivorIconsCombo = map(lambda survivor: QIcon(Globals.SURVIVOR_ICONS[toResourceName(survivor.survivorName)]),
                               self.items)
        for survivorStr, icon in zip(survivorItems, survivorIconsCombo):
            self.itemSelectionComboBox.addItem(icon, survivorStr)
        self.itemSelectionComboBox.activated.connect(self.selectFromIndex)
        self.selectFromIndex(0)

    def updateSelected(self):
        if self.selectedItem is None:
            return
        self.nameDisplayLabel.setText(self.selectedItem.survivorName)
        icon = Globals.SURVIVOR_ICONS[toResourceName(self.selectedItem.survivorName)]
        self.imageLabel.setFixedSize(icon.width(), icon.height())
        self.imageLabel.setPixmap(icon)



class GridViewSelectionPopup(QDialog):
    def __init__(self, columns: int, parent=None):
        super().__init__(parent, Qt.Popup | Qt.FramelessWindowHint)
        self.items = []
        layout = QVBoxLayout()
        self.setLayout(layout)
        self.columns = columns
        self.itemsLayout = QGridLayout()
        self.selectedItem = None
        mainWidget = QWidget()
        mainWidget.setLayout(self.itemsLayout)
        mainWidget.setAutoFillBackground(True)
        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setWidget(mainWidget)
        layout.addWidget(scroll)

    def initPopupGrid(self):
        clearLayout(self.itemsLayout)

    def selectItem(self, item):
        self.selectedItem = item
        self.accept()

class SearchableGridViewSelectionPopup(GridViewSelectionPopup):

    def __init__(self, placeholderText: str, columns: int, filterFunction: Callable = lambda x: True, parent=None):
        super().__init__(columns, parent)
        self.searchBar = QLineEdit()
        self.filterFunction = filterFunction
        self.currentItems = self.items
        self.searchBar.setPlaceholderText(placeholderText)
        self.searchBar.textChanged.connect(self.filterItems)
        self.layout().addWidget(self.searchBar)

    def filterItems(self, searchText: str):
        self.currentItems = self.items if not searchText.strip() else [i for i in self.items if self.filterFunction(i,searchText)]
        self.initPopupGrid()

class AddonSelectPopup(GridViewSelectionPopup):


    def __init__(self, addons: list[Union[ItemAddon, KillerAddon]], iconSize=(100,100), parent=None):
        super().__init__(5, parent=parent)
        self.resize(self.columns * iconSize[0], self.columns * iconSize[1])
        self.iconSize = iconSize
        self.addons = addons
        self.currentAddons = []
        self.initPopupGrid()


    def initPopupGrid(self):
        super().initPopupGrid()
        for index, addon in enumerate(self.currentAddons):
            columnIndex = index % self.columns
            rowIndex = index // self.columns
            addonButton = QPushButton()
            addonButton.setFixedSize(Globals.ADDON_ICON_SIZE[0], Globals.ADDON_ICON_SIZE[1])
            addonButton.setIconSize(QSize(Globals.ADDON_ICON_SIZE[0], Globals.ADDON_ICON_SIZE[1]))
            addonButton.clicked.connect(partial(self.selectItem, addon))
            addonButton.setFlat(True)
            iconName = toResourceName(addon.addonName)
            addonIcon = QIcon(Globals.ADDON_ICONS[iconName])
            addonButton.setIcon(addonIcon)
            addonButton.setToolTip(addon.addonName)
            self.itemsLayout.addWidget(addonButton, rowIndex, columnIndex)

    def selectAddon(self) -> AddonSelectionResult:
        return self.selectedItem if self.exec_() == QDialog.Accepted else None

    def filterAddons(self, filterFunc: Callable):
        self.currentAddons = list(filter(filterFunc, self.addons))
        print(self.currentAddons)
        self.initPopupGrid()

#todo: add filtering by perk tier
class PerkPopupSelect(SearchableGridViewSelectionPopup):

    def __init__(self, perks: list[Perk], parent=None):
        super().__init__(parent=parent, placeholderText="Input perk name to search for", columns=3, filterFunction=lambda p,s: p.perkName.startswith(s))
        self.items = perks
        self.currentItems = perks
        self.initPopupGrid()

    def initPopupGrid(self):
        super().initPopupGrid()
        for index, perk in enumerate(self.currentItems):
            columnIndex = index % self.columns
            rowIndex = index // self.columns
            perkButton = QPushButton()
            perkButton.setFixedSize(*Globals.PERK_ICON_SIZE)
            perkButton.setIconSize(QSize(*Globals.PERK_ICON_SIZE))
            perkButton.clicked.connect(partial(self.selectItem, perk))
            perkButton.setFlat(True)
            iconName = toResourceName(perk.perkName) + f'-{"i" * perk.perkTier}'
            perkIcon = QIcon(Globals.PERK_ICONS[iconName])
            perkButton.setIcon(perkIcon)
            perkButton.setToolTip(perk.perkName + f' {"I" * perk.perkTier}')
            self.itemsLayout.addWidget(perkButton, rowIndex, columnIndex)

    def selectPerk(self) -> Optional[Perk]:
        return self.selectedItem if self.exec_() == QDialog.Accepted else None

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
        addonsLabel = QLabel('Addons')
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
        leftLayout.addSpacerItem(QSpacerItem(5, 65))
        rightLayout.addSpacerItem(QSpacerItem(5, 65))

    def __createLabel(self):
        lbl = QLabel('No addon')
        lbl.setAlignment(Qt.AlignCenter)
        lbl.setFixedHeight(45)
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
        if addon is not None:
            addonAlreadySelected = self.__validateIfAddonSelected(addon)
            if not addonAlreadySelected:
                pixmap = Globals.ADDON_ICONS[toResourceName(addon.addonName)]
                btnToUpdate.setIcon(QIcon(pixmap))
                lblToUpdate.setText(addon.addonName)
                self.selectedAddons[index] = addon
            else:
                pass #todo: show information that its selected already

    def __validateIfAddonSelected(self, addon: Union[KillerAddon, ItemAddon]) -> bool:
        return any(a.addonName == addon.addonName for a in self.selectedAddons.values() if a is not None)

    def clearSelected(self):
        self.addon1Button.setIcon(self.defaultIcon)
        self.addon2Button.setIcon(self.defaultIcon)
        for key in self.selectedAddons.keys():
            self.selectedAddons[key] = None
        self.addon2NameLabel.setText('No addon')
        self.addon1NameLabel.setText('No addon')

    def filterAddons(self, filterFunc: Callable):
        self.popupSelect.filterAddons(filterFunc)
        self.clearSelected()

class PerkSelection(QWidget):

    def __init__(self, perks: list[Perk], parent=None):
        super().__init__(parent)
        self.perks = perks
        self.popupSelection = PerkPopupSelect(self.perks)
        self.selectedPerks: dict[int, Optional[Perk]] = {n:None for n in range(4)}
        self.defaultPerkIcon = QIcon(Globals.DEFAULT_PERK_ICON)
        self.setLayout(QVBoxLayout())
        l = QLabel("Character perks")
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
        point = btn.rect().topRight()
        globalPoint = btn.mapToGlobal(point)
        self.popupSelection.move(globalPoint - QPoint(0, self.height() / 2))
        perk = self.popupSelection.selectPerk()
        if perk is not None:
            perkAlreadySelected = self.__validateIfPerkSelected(perk)
            if not perkAlreadySelected or (self.selectedPerks[index] is not None and perk.perkName == self.selectedPerks[index].perkName):
                label.setText(f'{perk.perkName} {"I" * perk.perkTier}')
                self.selectedPerks[index] = perk
                iconName = toResourceName(perk.perkName) + f'-{"i" * perk.perkTier}'
                pixmap = Globals.PERK_ICONS[iconName]
                btn.setIcon(QIcon(pixmap))
            else:
                pass #todo: show message window with information

    def __validateIfPerkSelected(self, perk: Perk) -> bool:
        return any(p.perkName == perk.perkName for p in self.selectedPerks.values() if p is not None)




class FacedSurvivorSelect(ItemSelect):

    def __init__(self, survivors: list[Survivor], iconSize=(112,156), parent=None):
        super().__init__(parent=parent, iconSize=iconSize, items=survivors)
        self.survivorState: Optional[FacedSurvivorState] = None
        self.survivorStateComboBox = QComboBox()
        self.layout().addWidget(self.survivorStateComboBox)
        for state in FacedSurvivorState:
            text = ' '.join(splitUpper(state.name)).lower().capitalize()
            self.survivorStateComboBox.addItem(text)
        self.survivorStateComboBox.activated.connect(self.selectState)
        comboItems = map(str, self.items)
        iconsCombo = map(lambda survivor: QIcon(Globals.SURVIVOR_ICONS[toResourceName(survivor.survivorName)]),
                               self.items)
        for survivor, icon in zip(comboItems, iconsCombo):
            self.itemSelectionComboBox.addItem(icon, survivor)
        self.itemSelectionComboBox.activated.connect(self.selectFromIndex)
        self.itemSelectionComboBox.view().setIconSize(QSize(iconSize[0]//2,iconSize[1]//2))
        self.selectFromIndex(0)

    def selectState(self, index: int=0):
        self.survivorState = FacedSurvivorState(index)

    def updateSelected(self):
        if self.selectedItem is None:
            return
        self.nameDisplayLabel.setText(self.selectedItem.survivorName)
        icon = Globals.SURVIVOR_ICONS[toResourceName(self.selectedItem.survivorName)]
        self.imageLabel.setPixmap(icon)

    def getFacedSurvivor(self):
        return FacedSurvivor(state=self.survivorState,facedSurvivor=self.selectedItem)

class FacedSurvivorSelectionWindow(QWidget):

    def __init__(self, survivors: list[Survivor], size=(1,4), parent=None):
        super().__init__(parent)
        acceptableSizes = ((1,4), (4, 1), (2,2))
        if size not in acceptableSizes:
            raise ValueError(f"Value of rows can only be one of these values: [{','.join(map(str, acceptableSizes))}]")
        self.survivors = survivors
        self.selections = {n: FacedSurvivorSelect(survivors=self.survivors, iconSize=(Globals.CHARACTER_ICON_SIZE[0] // 2, Globals.CHARACTER_ICON_SIZE[1] // 2)) for n in range(4)}
        mainLayout = QGridLayout()
        self.setLayout(mainLayout)
        rows, cols = size
        index = 0
        for i in range(rows):
            for j in range(cols):
                selection = self.selections[index]
                mainLayout.addWidget(selection, i, j)
                index += 1


class OfferingSelectPopup(SearchableGridViewSelectionPopup):

    def __init__(self, offerings: list[Offering], parent=None):
        super().__init__(columns=5, parent=parent,placeholderText="Search for offerings...", filterFunction=lambda o,s: o.offeringName.startswith(s))
        self.items = offerings
        self.currentItems = offerings
        self.initPopupGrid()

    def initPopupGrid(self):
        super().initPopupGrid()
        for index, offering in enumerate(self.currentItems):
            columnIndex = index % self.columns
            rowIndex = index // self.columns
            btn = QPushButton()
            btn.setFixedSize(Globals.OFFERING_ICON_SIZE[0], Globals.OFFERING_ICON_SIZE[1])
            btn.setIconSize(QSize(Globals.OFFERING_ICON_SIZE[0], Globals.OFFERING_ICON_SIZE[1]))
            btn.clicked.connect(partial(self.selectItem, offering))
            btn.setFlat(True)
            iconName = toResourceName(offering.offeringName)
            icon = QIcon(Globals.OFFERING_ICONS[iconName])
            btn.setIcon(icon)
            self.itemsLayout.addWidget(btn, rowIndex, columnIndex)

    def selectOffering(self):
        return self.selectedItem if self.exec_() == QDialog.Accepted else None

class OfferingSelection(QWidget):

    def __init__(self, offerings: list[Offering], parent=None):
        super().__init__(parent)
        self.offerings = offerings
        self.popupSelection = OfferingSelectPopup(offerings=self.offerings)
        self.defaultIcon = QIcon(Globals.DEFAULT_OFFERING_ICON)
        self.selectedItem = None
        offeringLabel = QLabel('No offering')
        label = QLabel('Offering')
        label.setAlignment(Qt.AlignCenter)
        label.setStyleSheet("font-weight: bold")
        label.setFixedHeight(20)
        offeringLabel.setAlignment(Qt.AlignCenter)
        offeringLabel.setFixedHeight(40)
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
        self.layout().addSpacerItem(QSpacerItem(1, 65))
        self.layout().setAlignment(selectionButton, Qt.AlignCenter)

    def __showOfferingPopup(self, btn: QPushButton, label: QLabel):
        point = btn.rect().bottomLeft()
        globalPoint = btn.mapToGlobal(point)
        self.popupSelection.move(globalPoint)
        offering = self.popupSelection.selectOffering()
        if offering is not None:
            pixmap: QPixmap = Globals.OFFERING_ICONS[toResourceName(offering.offeringName)]
            btn.setIcon(QIcon(pixmap))
            label.setText(offering.offeringName)


class MapSelect(QWidget):

    def __init__(self, realms: list[Realm], parent=None):
        super().__init__(parent=parent)
        self.selectedMap: Optional[GameMap] = None
        self.realms = realms
        self.currentMaps = realms[0].maps
        self.realmSelectionComboBox = QComboBox()
        self.currentIndex = 0
        for realm in realms:
            self.realmSelectionComboBox.addItem(realm.realmName)
        self.realmSelectionComboBox.activated.connect(self.__switchRealmMaps)
        self.mapImageLabel = QLabel()
        self.mapImageLabel.setFixedSize(QSize(Globals.MAP_ICON_SIZE[0], Globals.MAP_ICON_SIZE[1]))
        self.mapNameLabel = QLabel('No map selected')
        buttonWidth = 25
        self.leftMapSelectButton = QPushButton('<')
        self.leftMapSelectButton.clicked.connect(lambda: self.switchMap(operator.sub))
        self.leftMapSelectButton.setFixedWidth(buttonWidth)
        self.rightMapSelectButton = QPushButton('>')
        self.rightMapSelectButton.clicked.connect(lambda: self.switchMap(operator.add))
        self.rightMapSelectButton.setFixedWidth(buttonWidth)
        mainLayout = QVBoxLayout()
        self.setLayout(mainLayout)
        realmSubLayout = QVBoxLayout()
        mapSubLayout = QVBoxLayout()
        mainLayout.addLayout(realmSubLayout)
        mainLayout.addLayout(mapSubLayout)
        realmSelectionLayout = QHBoxLayout()
        mapSelectionLayout = QHBoxLayout()
        realmSubLayout.addLayout(realmSelectionLayout)
        realmHeaderLabel = QLabel("Realm name")
        realmHeaderLabel.setAlignment(Qt.AlignTop)
        realmSubLayout.addSpacerItem(QSpacerItem(1, 15))
        realmSubLayout.addWidget(realmHeaderLabel)
        realmSubLayout.addWidget(self.realmSelectionComboBox)
        realmSubLayout.addSpacerItem(QSpacerItem(1, 50))
        mapSubLayout.addLayout(mapSelectionLayout)
        mapSelectionLayout.addWidget(self.leftMapSelectButton)
        mapSelectionLayout.addWidget(self.mapImageLabel)
        mapSelectionLayout.addWidget(self.rightMapSelectButton)
        mapSubLayout.addWidget(self.mapNameLabel)
        self.mapNameLabel.setAlignment(Qt.AlignHCenter)
        self.selectedMap = self.currentMaps[self.currentIndex]
        self.__updateUI()

    def switchMap(self, op):
        if len(self.currentMaps) == 0:
            return
        self.currentIndex = clampReverse(op(self.currentIndex, 1), 0, len(self.currentMaps) - 1)
        self.selectedMap = self.currentMaps[self.currentIndex]
        self.__updateUI()

    def __switchRealmMaps(self, index: int):
        realm = self.realms[index]
        self.currentMaps = realm.maps
        if len(self.currentMaps) > 0:
            self.selectedMap = self.currentMaps[0]
            self.currentIndex = 0
            self.__updateUI()

    def __updateUI(self):
        if self.selectedMap is not None:
            self.mapNameLabel.setText(self.selectedMap.mapName)
            pixmap = Globals.MAP_ICONS[toResourceName(self.selectedMap.mapName)]
            self.mapImageLabel.setPixmap(pixmap)


class SurvivorItemSelect(ItemSelect):


    def __init__(self, items: list[Item], iconSize=(100,100), parent=None):
        super().__init__(items=items, parent=parent)
        self.currentItems = []
        self.itemTypeFilterComboBox = self.itemSelectionComboBox
        delattr(self, "itemSelectionComboBox")
        for item in ItemType:
            self.itemTypeFilterComboBox.addItem(item.name)
        buttonSize = (25,35)
        self.rightButton.setFixedSize(*buttonSize)
        self.leftButton.setFixedSize(*buttonSize)
        self.itemTypeFilterComboBox.activated.connect(self.selectFromIndex)
        self.selectFromIndex(0)

    def selectFromIndex(self, index: int):
        itemType = ItemType(index)
        self.currentItems = [i for i in self.items if i.itemType == itemType]
        self.selectedItem = self.currentItems[0]
        self.currentIndex = 0
        self.selectionChanged.emit(self.selectedItem)
        self.updateSelected()

    def updateSelected(self):
        if self.selectedItem is None:
            return

        self.nameDisplayLabel.setText(self.selectedItem.itemName)
        icon = Globals.ITEM_ICONS[toResourceName(self.selectedItem.itemName)]
        self.imageLabel.setFixedSize(icon.width(), icon.height())
        self.imageLabel.setPixmap(icon)

    def next(self):
        self._updateIndex(self.currentIndex + 1)

    def prev(self):
        self._updateIndex(self.currentIndex - 1)

    def _updateIndex(self, index: int):
        if not self._itemsPresent():
            return
        self.currentIndex = clampReverse(index, 0, len(self.currentItems) - 1)
        self.selectedItem = self.currentItems[self.currentIndex]
        self.updateSelected()

    def _itemsPresent(self):
        return len(self.currentItems) > 0