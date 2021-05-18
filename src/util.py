import re
from typing import Optional

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
            layout.itemAt(i).widget().setParent(None)