from __future__ import annotations

from PyQt5.QtCore import QThread, Qt, pyqtSignal
from PyQt5.QtGui import QMovie
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QTabWidget, QGridLayout, QLabel, QSpacerItem, QWidget
from waitingspinnerwidget import QtWaitingSpinner

from statistics import StatisticsCalculator, GeneralMatchStatistics, SurvivorMatchStatistics, KillerMatchStatistics
from util import clearLayout, qtMakeBold


class StatisticsWorker(QThread):

    calculationFinished = pyqtSignal(GeneralMatchStatistics, KillerMatchStatistics, SurvivorMatchStatistics)

    def __init__(self, calc: StatisticsCalculator):
        super().__init__()
        self.calculator = calc

    def run(self) -> None:
        general = self.calculator.calculateGeneral()
        killer = self.calculator.calculateKillerGeneral()
        survivor = self.calculator.calculateSurvivorGeneral()
        self.calculationFinished.emit(general, killer, survivor)


class StatisticsWindow(QDialog):


    def __init__(self, calc: StatisticsCalculator, parent=None):
        super().__init__(parent=parent)
        self.resize(800, 600)
        self.setWindowTitle("Match statistics")
        self.setWindowFlags(self.windowFlags() | Qt.CustomizeWindowHint)
        self.worker = StatisticsWorker(calc)
        self.worker.calculationFinished.connect(self.__setupUIForStatistics)
        self.worker.finished.connect(self.enableCloseButton)
        layout = QVBoxLayout()
        self.setLayout(layout)
        self.spinner = QtWaitingSpinner(None, centerOnParent=True)
        self.spinner.setInnerRadius(25)
        self.spinner.setLineLength(20)
        textLabel = QLabel("Calculating...")
        textLabel.setAlignment(Qt.AlignCenter)
        textLabel.setStyleSheet("""
            font-weight: bold;
            font-size: 24px;
        """)
        layout.addWidget(self.spinner)
        layout.addSpacerItem(QSpacerItem(0, 50))
        layout.addWidget(textLabel)

    def exec_(self) -> int:
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowCloseButtonHint)
        self.spinner.start()
        self.worker.start()
        return super().exec_()


    def enableCloseButton(self):
        self.setWindowFlags(self.windowFlags() | Qt.WindowCloseButtonHint)
        self.show() #we need this call because, apparently, setting window flags changes the parent. because of that, the window becomes hidden and we must show it again

    def __setupUIForStatistics(self, generalStats: GeneralMatchStatistics, killerStats: KillerMatchStatistics, survivorStats: SurvivorMatchStatistics):
        self.spinner.stop()
        clearLayout(self.layout())
        self.layout().deleteLater()
        mainLayout = QGridLayout() #create a box for general stats, and below it - a tab widget with survivor and killer stats
        self.layout().destroyed.connect(lambda: self.setLayout(mainLayout))
        generalStatsLayout = QVBoxLayout()
        mainLayout.addLayout(generalStatsLayout, 0, 0, 1, 1)
        killerAndSurvivorStatsLayout = QVBoxLayout()
        mainLayout.addLayout(killerAndSurvivorStatsLayout, 1, 0, 3, 1)
        statsTabWidget = QTabWidget()
        killerStatsWidget = QWidget()
        survivorStatsWidget = QWidget()
        statsTabWidget.addTab(killerStatsWidget, "Killer statistics")
        statsTabWidget.addTab(survivorStatsWidget, "Survivor statistics")
        killerAndSurvivorStatsLayout.addWidget(statsTabWidget)
        generalStatsLabel = QLabel(qtMakeBold("General match statistics"))
        generalStatsLabel.setAlignment(Qt.AlignCenter)
        generalStatsLayout.addWidget(generalStatsLabel)
        generalStatsLayout.setAlignment(generalStatsLabel, Qt.AlignCenter | Qt.AlignTop)
