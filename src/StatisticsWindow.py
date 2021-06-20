from __future__ import annotations

from PyQt5.QtCore import QThread, QObject, pyqtSignal, Qt
from PyQt5.QtGui import QWindow
from PyQt5.QtWidgets import QDialog

from statistics import StatisticsCalculator


class StatisticsWorker(QThread):

    def __init__(self, calc: StatisticsCalculator):
        super().__init__()
        self.calculator = calc

    def run(self) -> None:
        print("working")



class StatisticsWindow(QDialog):


    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setWindowFlags(self.windowFlags() | Qt.CustomizeWindowHint)
        self.worker = StatisticsWorker(None)
        self.worker.finished.connect(self.enableCloseButton)

    def exec_(self) -> int:
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowCloseButtonHint)
        self.worker.start()
        return super().exec_()

    def enableCloseButton(self):
        self.setWindowFlags(self.windowFlags() | Qt.WindowCloseButtonHint)
        self.show() #we need this call because, apparently, setting window flags changes the parent. because of that, the window becomes hidden and we must show it again
