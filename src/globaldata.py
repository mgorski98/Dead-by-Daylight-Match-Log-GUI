from __future__ import annotations

import os

from PyQt5.QtGui import QPixmap

KILLER_ICONS = {}
SURVIVOR_ICONS = {}
ITEM_ICONS = {}
ADDON_ICONS = {}
OFFERING_ICONS = {}
PERK_ICONS = {}

def loadIcons(): #NOTE: this can only be called after creating QApplication object, otherwise it crashes the program
    killerIconsPath = '../images/killers/'
    survivorIconsPath = '../images/survivors/'
    addonsIconsPath = '../images/addons/'
    offeringsIconsPath = '../images/offerings/'
    perksIconsPath = '../images/perks/'
    itemsIconsPath = '../images/items/'
    paths = [killerIconsPath, survivorIconsPath, addonsIconsPath, offeringsIconsPath, perksIconsPath, itemsIconsPath]
    dicts = [KILLER_ICONS, SURVIVOR_ICONS, ADDON_ICONS, OFFERING_ICONS, PERK_ICONS, ITEM_ICONS]
    for path, iconDict in zip(paths, dicts):
        for file in os.listdir(path):
            pixmap = QPixmap(path + file)
            filename, _ = os.path.splitext(file)
            KILLER_ICONS[filename] = pixmap