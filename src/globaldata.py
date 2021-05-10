from __future__ import annotations
import os
from collections import defaultdict

from PyQt5.QtGui import QPixmap, QImage

KILLER_ICONS = {}
SURVIVOR_ICONS = {}
ITEM_ICONS = {}
ADDON_ICONS = {}
OFFERING_ICONS = {}
PERK_ICONS = {}

CHARACTER_ICON_SIZE = (150, 208) #width, height

def load_icons(): #NOTE: this can only be called after creating QApplication object, otherwise it crashes the program
    killerIconsPath = '../images/killers/'
    survivorIconsPath = '../images/survivors/'
    addonsIconsPath = '../images/addons/'
    offeringsIconsPath = '../images/offerings/'
    perksIconsPath = '../images/perks/'
    itemsIconsPath = '../images/items/'
    paths = [killerIconsPath, survivorIconsPath, addonsIconsPath, offeringsIconsPath, perksIconsPath, itemsIconsPath]
    dicts = [KILLER_ICONS, SURVIVOR_ICONS, ADDON_ICONS, OFFERING_ICONS, PERK_ICONS, ITEM_ICONS]
    for path, iconDict in zip(paths, dicts):
        files = os.listdir(path)
        for file in files:
            filepath = path + file
            pixmap = QPixmap(filepath)
            filename, _ = os.path.splitext(file)
            KILLER_ICONS[filename] = pixmap