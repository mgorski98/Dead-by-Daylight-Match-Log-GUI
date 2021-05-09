from __future__ import annotations
import os
from collections import defaultdict

from PyQt5.QtGui import QPixmap

KILLER_ICONS = {}
SURVIVOR_ICONS = {}
ITEM_ICONS = {}
ADDON_ICONS = {}
OFFERING_ICONS = {}
PERK_ICONS = {}

def load_icons():
    killerIconsPath = '../images/killers/'
    survivorIconsPath = '../images/survivors/'
    addonsIconsPath = '../images/addons/'
    offeringsIconsPath = '../images/offerings/'
    perksIconsPath = '../images/perks/'
    itemsIconsPath = '../images/items/'
    paths = [killerIconsPath, survivorIconsPath, addonsIconsPath, offeringsIconsPath, perksIconsPath, itemsIconsPath]
    dicts = [KILLER_ICONS, SURVIVOR_ICONS, ITEM_ICONS, ADDON_ICONS, OFFERING_ICONS, PERK_ICONS]
    for path, iconDict in zip(paths, dicts):
        files = os.listdir(path)
        for file in files:
            pixmap = QPixmap(file)
            filename, _ = os.path.splitext(file)
            iconDict[filename] = pixmap


load_icons()