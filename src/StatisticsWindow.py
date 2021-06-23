from __future__ import annotations

from PyQt5.QtChart import QBarSet, QBarSeries, QChart, QBarCategoryAxis, QValueAxis, QChartView
from PyQt5.QtCore import QThread, Qt, pyqtSignal
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QTabWidget, QGridLayout, QLabel, QSpacerItem, QWidget, QHBoxLayout

from models import FacedSurvivorState
from waitingspinnerwidget import QtWaitingSpinner

from statistics import StatisticsCalculator, GeneralMatchStatistics, SurvivorMatchStatistics, KillerMatchStatistics
from util import clearLayout, qtMakeBold, addSubLayouts, splitUpper



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
        self.resize(1200, 840)
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
        killerAndSurvivorStatsLayout.setContentsMargins(0, 20, 0, 0)
        statsTabWidget.addTab(killerStatsWidget, "Killer statistics")
        statsTabWidget.addTab(survivorStatsWidget, "Survivor statistics")
        killerAndSurvivorStatsLayout.addWidget(statsTabWidget)
        generalStatsLabel = QLabel(qtMakeBold("General match statistics"))
        generalStatsLabel.setStyleSheet("font-size: 20px;")
        generalStatsLabel.setAlignment(Qt.AlignCenter)
        generalStatsLayout.addWidget(generalStatsLabel)
        generalStatsLayout.setAlignment(generalStatsLabel, Qt.AlignCenter | Qt.AlignTop)
        generalStatsLayout.addSpacerItem(QSpacerItem(0, 15))
        margins = (25, 0, 25, 0)
        mostCommonMapLayout, mostCommonRealmLayout = QHBoxLayout(), QHBoxLayout()
        leastCommonMapLayout, leastCommonRealmLayout = QHBoxLayout(), QHBoxLayout()
        totalPointsLayout = QHBoxLayout()
        averagePointsLayout = QHBoxLayout()
        gamesLayout = QHBoxLayout()
        mostCommonMapInfoLabel, mostCommonMapLabel = QLabel(qtMakeBold("Most common map")), QLabel(qtMakeBold(str(generalStats.mostCommonMapData)))
        mostCommonRealmInfoLabel, mostCommonRealmLabel = QLabel(qtMakeBold("Most common map realm")), QLabel(qtMakeBold(str(generalStats.mostCommonMapRealmData)))
        leastCommonMapInfoLabel, leastCommonMapLabel = QLabel(qtMakeBold("Least common map")), QLabel(qtMakeBold(str(generalStats.leastCommonMapData)))
        leastCommonRealmInfoLabel, leastCommonRealmLabel = QLabel(qtMakeBold("Least common map realm")), QLabel(qtMakeBold(str(generalStats.leastCommonMapRealmData)))
        pointsLabel, totalPointsInfoLabel = QLabel(qtMakeBold(f"{generalStats.totalPoints:,}")), QLabel(qtMakeBold("Total points"))
        avgPointsLabel, avgPointsInfoLabel = QLabel(qtMakeBold(f"{generalStats.averagePointsPerMatch:,}")), QLabel(qtMakeBold("Average points per match"))
        gamesLabel, gamesInfoLabel = QLabel(qtMakeBold(f"{generalStats.totalGames:,}")), QLabel(qtMakeBold("Total matches played"))

        def setStatSublayout(layout, leftLabel, rightLabel, contentMargins):
            layout.addWidget(leftLabel)
            layout.addWidget(rightLabel)
            layout.setContentsMargins(*contentMargins)
            layout.setAlignment(leftLabel, Qt.AlignLeft)
            layout.setAlignment(rightLabel, Qt.AlignRight)

        setStatSublayout(mostCommonMapLayout, mostCommonMapInfoLabel, mostCommonMapLabel, margins)
        setStatSublayout(mostCommonRealmLayout, mostCommonRealmInfoLabel, mostCommonRealmLabel, margins)
        setStatSublayout(leastCommonMapLayout, leastCommonMapInfoLabel, leastCommonMapLabel, margins)
        setStatSublayout(leastCommonRealmLayout, leastCommonRealmInfoLabel, leastCommonRealmLabel, margins)

        setStatSublayout(totalPointsLayout, totalPointsInfoLabel, pointsLabel, margins)
        setStatSublayout(averagePointsLayout, avgPointsInfoLabel, avgPointsLabel, margins)
        setStatSublayout(gamesLayout, gamesInfoLabel, gamesLabel, margins)

        sublayouts = [gamesLayout, totalPointsLayout, averagePointsLayout,
                      mostCommonMapLayout, mostCommonRealmLayout, leastCommonMapLayout, leastCommonRealmLayout]
        addSubLayouts(generalStatsLayout, *sublayouts)

        #killer stats setup
        if killerStats is None:
            l = QLabel(qtMakeBold("Nothing to see here. No killer matches present."))
            layout = QVBoxLayout()
            killerStatsWidget.setLayout(layout)
            layout.addWidget(l)
            layout.setAlignment(l, Qt.AlignCenter)
        else:
            killerStatsLayout = QVBoxLayout()
            generalKillerStatsLabel = QLabel(qtMakeBold("General killer match statistics"))
            generalKillerStatsLabel.setStyleSheet("font-size: 18px;")
            killerStatsLayout.addWidget(generalKillerStatsLabel)
            killerStatsLayout.addSpacerItem(QSpacerItem(0, 15))
            killerStatsLayout.setAlignment(generalKillerStatsLabel, Qt.AlignCenter | Qt.AlignTop)
            killerStatsWidget.setLayout(killerStatsLayout)
            margins = (0,0,0,0)
            favouriteKillerLayout = QHBoxLayout()
            favouriteKillerInfoLabel, favouriteKillerLabel = QLabel(qtMakeBold("Favourite killer")), QLabel(qtMakeBold(str(killerStats.favouriteKillerInfo)))
            setStatSublayout(favouriteKillerLayout, favouriteKillerInfoLabel, favouriteKillerLabel, margins)
            mostCommonSurvivorLayout = QHBoxLayout()
            mostCommonSurvivorInfoLabel, mostCommonSurvivorLabel = QLabel(qtMakeBold("Most common survivor")), QLabel(qtMakeBold(str(killerStats.mostCommonSurvivorData)))
            setStatSublayout(mostCommonSurvivorLayout, mostCommonSurvivorInfoLabel, mostCommonSurvivorLabel, margins)
            leastCommonSurvivorLayout = QHBoxLayout()
            leastCommonSurvivorInfoLabel, leastCommonSurvivorLabel = QLabel(qtMakeBold("Least common survivor")), QLabel(qtMakeBold(str(killerStats.leastCommonSurvivorData)))
            setStatSublayout(leastCommonSurvivorLayout, leastCommonSurvivorInfoLabel, leastCommonSurvivorLabel, margins)
            facedSurvivorsChartView = self.__setupFacedSurvivorStatesChart(killerStats)
            killerStatsLayout.addLayout(favouriteKillerLayout)
            killerStatsLayout.addLayout(mostCommonSurvivorLayout)
            killerStatsLayout.addLayout(leastCommonSurvivorLayout)
            killerStatsLayout.addSpacerItem(QSpacerItem(0, 15))
            killerStatsLayout.addWidget(facedSurvivorsChartView)

        #survivor stats setup
        if survivorStats is None:
            l = QLabel(qtMakeBold("Nothing to see here. No survivor matches present."))
            layout = QVBoxLayout()
            survivorStatsWidget.setLayout(layout)
            layout.addWidget(l)
            layout.setAlignment(l, Qt.AlignCenter)
        else:
            pass

    def __setupFacedSurvivorStatesChart(self, killerStats: KillerMatchStatistics) -> QChartView:
        categoryAxis = QBarCategoryAxis()
        valueAxis = QValueAxis()
        barSetPairs = [(QBarSet(' '.join(splitUpper(state.name))), state) for state in FacedSurvivorState]
        maxVal = 0
        for barset, state in barSetPairs:
            for survivor in killerStats.facedSurvivorStatesHistogram.keys():
                states = killerStats.facedSurvivorStatesHistogram[survivor]
                count = states[state]
                barset.append(count)
                if count > maxVal:
                    maxVal = count
        categories = [survivor.survivorName for survivor in killerStats.facedSurvivorStatesHistogram.keys()]
        categoryAxis.append(categories)
        categoryAxis.setLabelsAngle(-90)
        valueAxis.setRange(0, maxVal)
        barSeries = QBarSeries()
        for _set, _ in barSetPairs:
            barSeries.append(_set)
        chart = QChart()
        chart.addAxis(categoryAxis, Qt.AlignBottom)
        chart.addAxis(valueAxis, Qt.AlignLeft)
        chart.addSeries(barSeries)
        barSeries.attachAxis(categoryAxis)
        barSeries.attachAxis(valueAxis)
        chart.setTitle("Faced survivors' fates")
        chart.setAnimationOptions(QChart.SeriesAnimations)
        chart.legend().setVisible(True)
        chart.legend().setAlignment(Qt.AlignRight)
        chartView = QChartView(chart)
        return chartView