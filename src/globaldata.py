from __future__ import annotations

import os
from typing import Optional

from PyQt5.QtGui import QPixmap



class Globals:
    KILLER_ICONS = {}
    SURVIVOR_ICONS = {}
    ITEM_ICONS = {}
    ADDON_ICONS = {}
    OFFERING_ICONS = {}
    PERK_ICONS = {}
    DEFAULT_ICON_OTHER: Optional[QPixmap] = None
    LOWEST_RANK = 20  # dbd ranks are going in reverse, 20 is the wors
    HIGHEST_RANK = 1  # and 1 is the best
    CHARACTER_ICON_SIZE = (150, 208)  # width, height
    PERK_ICON_SIZE = (128, 128)
    OTHER_ICONS_SIZE = (128, 128)  # width, height

    @staticmethod
    def init():  # NOTE: this can only be called after creating QApplication object, otherwise it crashes the program
        Globals.DEFAULT_ICON_OTHER = QPixmap('../images/default-icon-other.png')
        killerIconsPath = '../images/killers/'
        survivorIconsPath = '../images/survivors/'
        addonsIconsPath = '../images/addons/'
        offeringsIconsPath = '../images/offerings/'
        perksIconsPath = '../images/perks/'
        itemsIconsPath = '../images/items/'
        paths = [killerIconsPath, survivorIconsPath, addonsIconsPath, offeringsIconsPath, perksIconsPath,
                 itemsIconsPath]
        dicts = [Globals.KILLER_ICONS, Globals.SURVIVOR_ICONS, Globals.ADDON_ICONS, Globals.OFFERING_ICONS, Globals.PERK_ICONS, Globals.ITEM_ICONS]
        for path, iconDict in zip(paths, dicts):
            for file in os.listdir(path):
                pixmap = QPixmap(path + file)
                filename, _ = os.path.splitext(file)
                iconDict[filename] = pixmap