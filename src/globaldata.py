from __future__ import annotations

import os
from typing import Optional
from concurrent.futures import ThreadPoolExecutor

from PyQt5.QtGui import QPixmap

from util import measureTime


class Globals:
    KILLER_ICONS: dict[str, QPixmap] = {}
    SURVIVOR_ICONS: dict[str, QPixmap] = {}
    ITEM_ICONS: dict[str, QPixmap] = {}
    ADDON_ICONS: dict[str, QPixmap] = {}
    OFFERING_ICONS: dict[str, QPixmap] = {}
    PERK_ICONS: dict[str, QPixmap] = {}
    MAP_ICONS: dict[str, QPixmap] = {}
    DEFAULT_ADDON_ICON: Optional[QPixmap] = None
    DEFAULT_PERK_ICON: Optional[QPixmap] = None
    DEFAULT_OFFERING_ICON: Optional[QPixmap] = None
    DEFAULT_ITEM_ICON: Optional[QPixmap] = None
    LOWEST_RANK = 20  # dbd ranks are going in reverse, 20 is the worst
    HIGHEST_RANK = 1  # and 1 is the best
    CHARACTER_ICON_SIZE = (150, 208)  # width, height
    PERK_ICON_SIZE = (128, 128)
    ADDON_ICON_SIZE = (96, 96)  # width, height
    OFFERING_ICON_SIZE = (96, 96)
    MAP_ICON_SIZE = (180, 90)
    ITEM_ICON_SIZE = (96, 96)

    @staticmethod
    def init():  # NOTE: this can only be called after creating QApplication object, otherwise it crashes the program
        Globals.DEFAULT_ADDON_ICON = QPixmap('../images/default-addon-icon.png')
        Globals.DEFAULT_PERK_ICON = QPixmap('../images/default-perk-icon.png')
        Globals.DEFAULT_OFFERING_ICON = QPixmap('../images/default-offering-icon.png').scaled(*Globals.OFFERING_ICON_SIZE)
        Globals.DEFAULT_ITEM_ICON = QPixmap('../images/default-item-icon.png').scaled(*Globals.ITEM_ICON_SIZE)
        killerIconsPath = '../images/killers/'
        survivorIconsPath = '../images/survivors/'
        addonsIconsPath = '../images/addons/'
        offeringsIconsPath = '../images/offerings/'
        perksIconsPath = '../images/perks/'
        itemsIconsPath = '../images/items/'
        mapIconsPath = '../images/maps/'
        paths = [killerIconsPath, survivorIconsPath, addonsIconsPath, offeringsIconsPath, perksIconsPath, itemsIconsPath, mapIconsPath]
        dicts = [Globals.KILLER_ICONS, Globals.SURVIVOR_ICONS, Globals.ADDON_ICONS, Globals.OFFERING_ICONS, Globals.PERK_ICONS, Globals.ITEM_ICONS, Globals.MAP_ICONS]
        pairs = zip(paths, dicts)

        def loadIconDir(pathDictPair: tuple[str, dict[str, QPixmap]]):
            dirPath, iconDict = pathDictPair
            for file in os.listdir(dirPath):
                pixmap = QPixmap(dirPath + file)
                fname, _ = os.path.splitext(file)
                iconDict[fname] = pixmap

        with ThreadPoolExecutor() as executor:
            executor.map(loadIconDir, pairs)