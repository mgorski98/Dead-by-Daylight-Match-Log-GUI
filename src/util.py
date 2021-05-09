import requests
import os

from PyQt5.QtWidgets import QLayout, QWidget


def saveImageFromURL(url: str, dest: str):
    request = requests.get(url,stream=True)
    with open(dest,mode='wb') as f:
        f.write(request.content)


def clamp(value, minValue, maxValue):
    return minValue if value < minValue else maxValue if value > maxValue else value

def setQWidgetLayout(widget: QWidget, layout: QLayout) -> tuple:
    widget.setLayout(layout)
    return widget, layout