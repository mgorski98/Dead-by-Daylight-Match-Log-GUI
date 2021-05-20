import re
from typing import Optional
import numpy as np

import requests

from PyQt5.QtGui import QIntValidator
from PyQt5.QtWidgets import QLayout, QWidget


def saveImageFromURL(url: str, dest: str):
    request = requests.get(url,stream=True)
    with open(dest,mode='wb') as f:
        f.write(request.content)


def clamp(value, minValue, maxValue):
    return minValue if value < minValue else maxValue if value > maxValue else value

def clampReverse(value, minValue, maxValue):
    return minValue if value > maxValue else maxValue if value < minValue else value

def setQWidgetLayout(widget: QWidget, layout: QLayout) -> tuple:
    widget.setLayout(layout)
    return widget, layout

def nonNegativeIntValidator(upperBound: Optional[int]=None) -> QIntValidator:
    validator = QIntValidator()
    validator.setBottom(0)
    if upperBound is not None and upperBound > 0:
        validator.setTop(upperBound)
    return validator

def addWidgets(layout: QLayout, *widgets) -> None:
    for widget in widgets:
        layout.addWidget(widget)

def splitUpper(s: str) -> list[str]:
    return re.findall(r'[A-Z][^A-Z]*', s)

def clearLayout(layout: QLayout):
    if layout is not None:
        for i in reversed(range(layout.count())):
            layout.itemAt(i).widget().deleteLater()

def toResourceName(s: str) -> str:
    return re.sub(r'[:\'\"]', '', s).lower().replace(' ', '-')

def levenshteinDistance(s1: str, s2: str) -> int:
    l1, l2 = len(s1), len(s2)
    if l1 == 0:
        return l2
    if l2 == 0:
        return l1

    m, n = l1 + 1, l2 + 1
    matrix = np.zeros((m, n), dtype=int)
    nrange, mrange = np.arange(n), np.arange(m)
    matrix[mrange,0] = mrange
    matrix[0,nrange] = nrange

    for i in range(1, m):
        for j in range(1, n):
            cost = 1 if s1[i - 1] != s2[j - 1] else 0
            matrix[i][j] = min(matrix[i - 1][j] + 1, matrix[i][j - 1] + 1, matrix[i - 1][j - 1] + cost)

    return matrix[m - 1][n - 1]