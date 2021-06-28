from __future__ import annotations

import sys

from PyQt5.QtChart import QBarSet, QBarSeries, QChart, QBarCategoryAxis, QValueAxis, QChartView
from PyQt5.QtCore import QThread, Qt, pyqtSignal
from PyQt5.QtGui import QPainter, QPixmap
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QTabWidget, QGridLayout, QLabel, QSpacerItem, QWidget, QHBoxLayout, \
    QScrollArea, QFrame, QLineEdit, QSizePolicy, QLayout, QPushButton

from globaldata import Globals
from models import FacedSurvivorState
from waitingspinnerwidget import QtWaitingSpinner

from statistics import StatisticsCalculator, GeneralMatchStatistics, SurvivorMatchStatistics, KillerMatchStatistics, \
    EliminationInfo, CommonSurvivorInfo
from util import clearLayout, qtMakeBold, addSubLayouts, splitUpper, addWidgets, toResourceName, singleOrPlural


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
        self.resources = calc.resources
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

        minChartHeight = 600

        generalStatsLayout = self.__setupGeneralStatsLayout(generalStats)
        mainLayout.addLayout(generalStatsLayout, 0, 0, 1, 1)
        killerAndSurvivorStatsLayout = QVBoxLayout()
        mainLayout.addLayout(killerAndSurvivorStatsLayout, 1, 0, 3, 1)
        statsTabWidget = QTabWidget()

        killerStatsScroll = QScrollArea()
        killerStatsScroll.setWidgetResizable(True)
        killerStatsScroll.setAutoFillBackground(True)

        survivorStatsScroll = QScrollArea()
        survivorStatsScroll.setWidgetResizable(True)
        survivorStatsScroll.setAutoFillBackground(True)

        killerStatsWidget = QWidget()
        survivorStatsWidget = QWidget()
        killerStatsScroll.setWidget(killerStatsWidget)
        survivorStatsScroll.setWidget(survivorStatsWidget)

        killerStatsScroll.setStyleSheet("background-color: white; border: 0px black;")
        survivorStatsScroll.setStyleSheet("background-color: white; border: 0px black;")

        killerAndSurvivorStatsLayout.setContentsMargins(0, 20, 0, 0)
        statsTabWidget.addTab(killerStatsScroll, "Killer statistics")
        statsTabWidget.addTab(survivorStatsScroll, "Survivor statistics")

        killerAndSurvivorStatsLayout.addWidget(statsTabWidget)

        def characterSubLayout(info, infoStrings, characterExtractorFunc, nameExtractorFunc, iconsDict) -> QHBoxLayout:
            character = characterExtractorFunc(info)
            characterLayout = QHBoxLayout()
            textLayout = QVBoxLayout()
            iconLabel = QLabel()
            icon = iconsDict[toResourceName(nameExtractorFunc(character))]
            icon = icon.scaled(icon.width() // 2, icon.height() // 2)
            iconLabel.setPixmap(icon)
            for s in infoStrings:
                infoLabel = QLabel(qtMakeBold(s))
                infoLabel.setWordWrap(True)
                infoLabel.setAlignment(Qt.AlignCenter)
                textLayout.addWidget(infoLabel)
            characterLayout.addLayout(textLayout)
            characterLayout.addWidget(iconLabel)
            characterLayout.setAlignment(iconLabel, Qt.AlignCenter)
            return characterLayout

        #extractor functions
        killerInfoExtractor = lambda i: i.killer
        killerNameExtractor = lambda k: k.killerAlias

        #killer stats setup
        if killerStats is None:
            l = QLabel(qtMakeBold("Nothing to see here. No killer matches present."))
            layout = QVBoxLayout()
            killerStatsWidget.setLayout(layout)
            layout.addWidget(l)
            layout.setAlignment(l, Qt.AlignCenter)
        else:
            generalKillerStatsLabel = QLabel(qtMakeBold("General killer match statistics"))
            generalKillerStatsLabel.setStyleSheet("font-size: 18px;")

            killerStatsLayout = QVBoxLayout()
            killerStatsLayout.addWidget(generalKillerStatsLabel)
            killerStatsLayout.addSpacerItem(QSpacerItem(0, 15))
            killerStatsLayout.setAlignment(generalKillerStatsLabel, Qt.AlignCenter | Qt.AlignTop)
            killerStatsWidget.setLayout(killerStatsLayout)

            generalKillerStatsLayout = QHBoxLayout()
            favouriteKillerLayout = QVBoxLayout()
            mostCommonSurvivorLayout = QVBoxLayout()
            leastCommonSurvivorLayout = QVBoxLayout()
            eliminationInfoLayout = QVBoxLayout()
            layouts = [favouriteKillerLayout, mostCommonSurvivorLayout, leastCommonSurvivorLayout, eliminationInfoLayout]
            widgets = [QWidget() for _ in layouts]
            for l, w in zip(layouts, widgets):
                w.setLayout(l)
                w.setStyleSheet(".QWidget{border: 1px solid black;border-radius: 10px}")
            addWidgets(generalKillerStatsLayout, *widgets)
            killerStatsLayout.addLayout(generalKillerStatsLayout)

            labels = [
                QLabel(qtMakeBold("Favourite killer")),
                QLabel(qtMakeBold("Most common survivor")),
                QLabel(qtMakeBold("Least common survivor")),
                QLabel(qtMakeBold("Total eliminations"))
            ]

            for layout, label in zip(layouts, labels):
                layout.addWidget(label)
                layout.setAlignment(label, Qt.AlignCenter | Qt.AlignTop)
                label.setStyleSheet("font-size: 18px")

            favouriteKillerInfo = killerStats.favouriteKillerInfo
            favouriteKillerSubLayout = characterSubLayout(favouriteKillerInfo, [f"{favouriteKillerInfo.gamesWithKiller:,} out of {favouriteKillerInfo.totalGames} {singleOrPlural(favouriteKillerInfo.totalGames, 'game')}"],
                                                          killerInfoExtractor, killerNameExtractor, Globals.KILLER_ICONS)
            favouriteKillerLayout.addLayout(favouriteKillerSubLayout)

            survExtractor, survNameExtractor = lambda i: i.survivor, lambda s: s.survivorName
            mostCommonInfo = killerStats.mostCommonSurvivorData
            mostCommonSurvivorInfoStr = f"{mostCommonInfo.encounters:,} {singleOrPlural(mostCommonInfo.encounters, 'encounter')} across {mostCommonInfo.totalGames:,} {singleOrPlural(mostCommonInfo.totalGames, 'game')}"
            mostCommonSurvivorSubLayout = characterSubLayout(mostCommonInfo, [mostCommonSurvivorInfoStr],
                                                             survExtractor, survNameExtractor, Globals.SURVIVOR_ICONS)
            mostCommonSurvivorLayout.addLayout(mostCommonSurvivorSubLayout)

            leastCommonInfo = killerStats.leastCommonSurvivorData
            leastCommonSurvivorInfoStr = f"{leastCommonInfo.encounters:,} {singleOrPlural(leastCommonInfo.encounters, 'encounter')} across {leastCommonInfo.totalGames:,} {singleOrPlural(leastCommonInfo.totalGames, 'game')}"
            leastCommonSurvivorSubLayout = characterSubLayout(killerStats.leastCommonSurvivorData, [leastCommonSurvivorInfoStr],
                                                              survExtractor, survNameExtractor, Globals.SURVIVOR_ICONS)
            leastCommonSurvivorLayout.addLayout(leastCommonSurvivorSubLayout)

            sacrificesLabel = QLabel(qtMakeBold(f"Sacrifices: {killerStats.totalEliminationsInfo.sacrifices:,}"))
            killsLabel = QLabel(qtMakeBold(f"Kills: {killerStats.totalEliminationsInfo.kills:,}"))
            disconnectsLabel = QLabel(qtMakeBold(f"Disconnects: {killerStats.totalEliminationsInfo.disconnects:,}"))
            eliminationInfoLayout.addSpacerItem(QSpacerItem(0, 15))
            addWidgets(eliminationInfoLayout, sacrificesLabel, killsLabel, disconnectsLabel)

            facedSurvivorsChartView = self.__setupFacedSurvivorStatesChart(killerStats)
            killerStatsLayout.addWidget(facedSurvivorsChartView)
            facedSurvivorsChartView.setMinimumHeight(minChartHeight)

            killerGamesChartView = self.__setupKillerGamesChart(killerStats)
            killerStatsLayout.addWidget(killerGamesChartView)
            killerGamesChartView.setMinimumHeight(minChartHeight)

            totalStatesChartView = self.__setupTotalStatesChart(killerStats)
            killerStatsLayout.addWidget(totalStatesChartView)
            totalStatesChartView.setMinimumHeight(minChartHeight)

            totalKillerEliminationsChartView = self.__setupEliminationsChart(killerStats)
            killerStatsLayout.addWidget(totalKillerEliminationsChartView)
            totalKillerEliminationsChartView.setMinimumHeight(minChartHeight)

            averageKillsChart = self.__setupAverageKillsChart(killerStats)
            killerStatsLayout.addWidget(averageKillsChart)
            averageKillsChart.setMinimumHeight(minChartHeight)

        #survivor stats setup
        if survivorStats is None:
            l = QLabel(qtMakeBold("Nothing to see here. No survivor matches present."))
            layout = QVBoxLayout()
            survivorStatsWidget.setLayout(layout)
            layout.addWidget(l)
            layout.setAlignment(l, Qt.AlignCenter)
        else:
            generalSurvivorStatsLabel = QLabel(qtMakeBold("General survivor match statistics"))
            generalSurvivorStatsLabel.setStyleSheet("font-size: 18px;")

            survivorStatsLayout = QVBoxLayout()
            survivorStatsLayout.addWidget(generalSurvivorStatsLabel)
            survivorStatsLayout.addSpacerItem(QSpacerItem(0, 15))
            survivorStatsLayout.setAlignment(generalSurvivorStatsLabel, Qt.AlignCenter | Qt.AlignTop)
            survivorStatsWidget.setLayout(survivorStatsLayout)

            generalSurvivorStatsLayout = QHBoxLayout()
            survivorStatsLayout.addLayout(generalSurvivorStatsLayout)

            mostCommonKillerLayout = QVBoxLayout()
            mostLethalKillerLayout = QVBoxLayout()
            leastCommonKillerLayout = QVBoxLayout()
            leastLethalKillerLayout = QVBoxLayout()
            mostCommonItemTypeLayout = QVBoxLayout()

            layouts = [mostCommonKillerLayout, leastCommonKillerLayout, mostLethalKillerLayout, leastLethalKillerLayout, mostCommonItemTypeLayout]
            widgets = [QWidget() for _ in layouts]
            for l, w in zip(layouts, widgets):
                w.setLayout(l)
                w.setStyleSheet(".QWidget{border: 1px solid black;border-radius: 10px}")

            addWidgets(generalSurvivorStatsLayout, *widgets)

            labels = [
                QLabel(qtMakeBold("Most common killer")),
                QLabel(qtMakeBold("Least common killer")),
                QLabel(qtMakeBold("Most lethal killer")),
                QLabel(qtMakeBold("Least lethal killer")),
                QLabel(qtMakeBold("Most common item type"))
            ]

            for _layout, label in zip(layouts, labels):
                _layout.addWidget(label)
                _layout.setAlignment(label, Qt.AlignTop | Qt.AlignCenter)
                label.setStyleSheet("font-size: 18px")

            mostCommonInfo = survivorStats.mostCommonKillerData
            mostCommonKillerInfoStr = f"{mostCommonInfo.encounters} {singleOrPlural(mostCommonInfo.encounters, 'encounter')} across {mostCommonInfo.totalGames} {singleOrPlural(mostCommonInfo.totalGames, 'game')}"
            mostCommonKillerSubLayout = characterSubLayout(mostCommonInfo, [mostCommonKillerInfoStr],
                                                           killerInfoExtractor, killerNameExtractor, Globals.KILLER_ICONS)
            mostCommonKillerLayout.addLayout(mostCommonKillerSubLayout)

            leastCommonInfo = survivorStats.leastCommonKillerData
            leastCommonKillerInfoStr = f"{leastCommonInfo.encounters} {singleOrPlural(leastCommonInfo.encounters, 'encounter')} across {leastCommonInfo.totalGames} {singleOrPlural(leastCommonInfo.totalGames, 'game')}"
            leastCommonKillerSubLayout = characterSubLayout(leastCommonInfo, [leastCommonKillerInfoStr],
                                                            killerInfoExtractor, killerNameExtractor, Globals.KILLER_ICONS)
            leastCommonKillerLayout.addLayout(leastCommonKillerSubLayout)

            mostLethalInfo = survivorStats.mostLethalKillerData
            mostLethalKillerInfoStrings = (
                f"{mostLethalInfo.deathsCount} {singleOrPlural(mostLethalInfo.deathsCount, 'death')} out of {mostLethalInfo.totalGames} {singleOrPlural(mostLethalInfo.totalGames, 'game')}",
                f"Kill ratio: {mostLethalInfo.killRatio:.2}"
            )
            mostLethalKillerSubLayout = characterSubLayout(mostLethalInfo, mostLethalKillerInfoStrings,
                                                           killerInfoExtractor, killerNameExtractor, Globals.KILLER_ICONS)
            mostLethalKillerLayout.addLayout(mostLethalKillerSubLayout)

            leastLethalInfo = survivorStats.leastLethalKillerData
            leastLethalKillerInfoStrings = (
                f"{leastLethalInfo.deathsCount} {singleOrPlural(leastLethalInfo.deathsCount, 'death')} out of {leastLethalInfo.totalGames} {singleOrPlural(leastLethalInfo.totalGames, 'game')}",
                f"Kill ratio: {leastLethalInfo.killRatio:.2}"
            )
            leastLethalKillerSubLayout = characterSubLayout(leastLethalInfo, leastLethalKillerInfoStrings,
                                                            killerInfoExtractor, killerNameExtractor, Globals.KILLER_ICONS)
            leastLethalKillerLayout.addLayout(leastLethalKillerSubLayout)

            itemTypeSubLayout = QHBoxLayout()
            itemTypeInfo = survivorStats.mostCommonItemTypeData
            mostCommonItemTypeLabel = QLabel(qtMakeBold(str(itemTypeInfo)))
            mostCommonItemTypeLabel.setWordWrap(True)
            mostCommonItemTypeIconLabel = QLabel()
            itemTypeSubLayout.addWidget(mostCommonItemTypeLabel)
            itemTypeSubLayout.addWidget(mostCommonItemTypeIconLabel)
            item = next(x for x in self.resources.items if x.itemType == itemTypeInfo.itemType)
            mostCommonItemTypeIconLabel.setPixmap(Globals.ITEM_ICONS[toResourceName(item.itemName)])
            mostCommonItemTypeLayout.addLayout(itemTypeSubLayout)

    def __setStatSubLayout(self, layout: QHBoxLayout, leftLabel: QLabel, rightLabel: QLabel, margins: tuple[int, int, int, int]):
        layout.addWidget(leftLabel)
        layout.addWidget(rightLabel)
        layout.setContentsMargins(*margins)
        layout.setAlignment(leftLabel, Qt.AlignLeft)
        layout.setAlignment(rightLabel, Qt.AlignRight)

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
        chart.setTitle(qtMakeBold("Faced survivors' fates"))
        chart.setAnimationOptions(QChart.SeriesAnimations)
        chart.legend().setVisible(True)
        chart.legend().setAlignment(Qt.AlignRight)
        chartView = QChartView(chart)
        chartView.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        chartView.setRenderHint(QPainter.Antialiasing)
        return chartView

    def __setupFacedKillerHistogramChart(self, survivorStats: SurvivorMatchStatistics) -> QChartView:
        facedKillerHist = survivorStats.facedKillerHistogram
        categoryAxis, valueAxis = QBarCategoryAxis(), QValueAxis()
        categories = [k.killerAlias for k in facedKillerHist.keys()]
        categoryAxis.append(categories)
        categoryAxis.setLabelsAngle(-90)
        valueAxis.setRange(0, max(facedKillerHist.values()))
        barset = QBarSet("Faced killers")
        for k in facedKillerHist.keys():
            barset.append(facedKillerHist[k])
        barSeries = QBarSeries()
        barSeries.attachAxis(categoryAxis)
        barSeries.attachAxis(valueAxis)
        barSeries.append(barset)
        chart = QChart()
        chart.addSeries(barSeries)
        chart.addAxis(categoryAxis, Qt.AlignBottom)
        chart.addAxis(valueAxis, Qt.AlignLeft)
        chart.setTitle(qtMakeBold('Faced killers frequency'))
        chart.setAnimationOptions(QChart.SeriesAnimations)
        chart.legend().setVisible(True)
        chart.legend().setAlignment(Qt.AlignRight)
        chartView = QChartView(chart)
        chartView.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        chartView.setRenderHint(QPainter.Antialiasing)
        return chartView

    def __setupTotalStatesChart(self, killerStats: KillerMatchStatistics) -> QChartView:
        categoryAxis, valueAxis = QBarCategoryAxis(), QValueAxis()
        categories = [' '.join(splitUpper(state.name)) for state in FacedSurvivorState]
        categoryAxis.append(categories)
        categoryAxis.setLabelsAngle(-90)
        barset = QBarSet("Survivor state")
        valueAxis.setRange(0, max(killerStats.totalSurvivorStatesHistogram.values()))
        for k in FacedSurvivorState:
            barset.append(killerStats.totalSurvivorStatesHistogram[k])
        barSeries = QBarSeries()
        barSeries.append(barset)
        barSeries.attachAxis(categoryAxis)
        barSeries.attachAxis(valueAxis)
        chart = QChart()
        chart.addAxis(categoryAxis, Qt.AlignBottom)
        chart.addAxis(valueAxis, Qt.AlignLeft)
        chart.addSeries(barSeries)
        chart.setTitle(qtMakeBold("Total survivor states"))
        chart.setAnimationOptions(QChart.SeriesAnimations)
        chart.legend().setVisible(True)
        chart.legend().setAlignment(Qt.AlignRight)
        chartView = QChartView(chart)
        chartView.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        chartView.setRenderHint(QPainter.Antialiasing)
        return chartView


    def __setupEliminationsChart(self, killerStats: KillerMatchStatistics) -> QChartView:
        categoryAxis, valueAxis = QBarCategoryAxis(), QValueAxis()
        barSets = [QBarSet("Sacrifices"), QBarSet("Kills"), QBarSet("Disconnects")]
        categories = [k.killerAlias for k in killerStats.totalKillerEliminations.keys()]
        categoryAxis.append(categories)
        categoryAxis.setLabelsAngle(-90)
        maxVal = 0
        for k in killerStats.totalKillerEliminations.keys():
            eliminationInfo = killerStats.totalKillerEliminations[k]
            sacrifices, kills, dcs = eliminationInfo.sacrifices, eliminationInfo.kills, eliminationInfo.disconnects
            for _set, value in zip(barSets, (sacrifices, kills, dcs)):
                _set.append(value)
                if value > maxVal:
                    maxVal = value
        valueAxis.setRange(0, maxVal)
        barSeries = QBarSeries()
        barSeries.attachAxis(categoryAxis)
        barSeries.attachAxis(valueAxis)
        for _set in barSets:
            barSeries.append(_set)
        chart = QChart()
        chart.addAxis(categoryAxis, Qt.AlignBottom)
        chart.addAxis(valueAxis, Qt.AlignLeft)
        chart.addSeries(barSeries)
        chart.setTitle(qtMakeBold("Total killer eliminations"))
        chart.legend().setVisible(True)
        chart.legend().setAlignment(Qt.AlignRight)
        chartView = QChartView(chart)
        chartView.setRenderHint(QPainter.Antialiasing)
        return chartView

    def __setupGeneralStatsLayout(self, stats: GeneralMatchStatistics) -> QLayout:
        generalStatsLayout = QVBoxLayout()

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
        mostCommonMapInfoLabel, mostCommonMapLabel = QLabel(qtMakeBold("Most common map")), QLabel(
            qtMakeBold(str(stats.mostCommonMapData)))
        mostCommonRealmInfoLabel, mostCommonRealmLabel = QLabel(qtMakeBold("Most common map realm")), QLabel(
            qtMakeBold(str(stats.mostCommonMapRealmData)))
        leastCommonMapInfoLabel, leastCommonMapLabel = QLabel(qtMakeBold("Least common map")), QLabel(
            qtMakeBold(str(stats.leastCommonMapData)))
        leastCommonRealmInfoLabel, leastCommonRealmLabel = QLabel(qtMakeBold("Least common map realm")), QLabel(
            qtMakeBold(str(stats.leastCommonMapRealmData)))
        pointsLabel, totalPointsInfoLabel = QLabel(qtMakeBold(f"{stats.totalPoints:,}")), QLabel(
            qtMakeBold("Total points"))
        avgPointsLabel, avgPointsInfoLabel = QLabel(qtMakeBold(f"{stats.averagePointsPerMatch:,}")), QLabel(
            qtMakeBold("Average points per match"))
        gamesLabel, gamesInfoLabel = QLabel(qtMakeBold(f"{stats.totalGames:,}")), QLabel(
            qtMakeBold("Total matches played"))

        self.__setStatSubLayout(mostCommonMapLayout, mostCommonMapInfoLabel, mostCommonMapLabel, margins)
        self.__setStatSubLayout(mostCommonRealmLayout, mostCommonRealmInfoLabel, mostCommonRealmLabel, margins)
        self.__setStatSubLayout(leastCommonMapLayout, leastCommonMapInfoLabel, leastCommonMapLabel, margins)
        self.__setStatSubLayout(leastCommonRealmLayout, leastCommonRealmInfoLabel, leastCommonRealmLabel, margins)

        self.__setStatSubLayout(totalPointsLayout, totalPointsInfoLabel, pointsLabel, margins)
        self.__setStatSubLayout(averagePointsLayout, avgPointsInfoLabel, avgPointsLabel, margins)
        self.__setStatSubLayout(gamesLayout, gamesInfoLabel, gamesLabel, margins)

        sublayouts = [gamesLayout, totalPointsLayout, averagePointsLayout,
                      mostCommonMapLayout, mostCommonRealmLayout, leastCommonMapLayout, leastCommonRealmLayout]
        addSubLayouts(generalStatsLayout, *sublayouts)
        return generalStatsLayout

    def __setupKillerGamesChart(self, killerStats: KillerMatchStatistics) -> QChartView:
        gamesHistogram = killerStats.gamesPlayedWithKiller
        categoryAxis, valueAxis = QBarCategoryAxis(), QValueAxis()
        valueAxis.setRange(0, max(gamesHistogram.values()))
        barset = QBarSet("Games with certain killer")
        for k in gamesHistogram.keys():
            barset.append(gamesHistogram[k])
        barSeries = QBarSeries()
        barSeries.append(barset)
        categories = [killer.killerAlias for killer in gamesHistogram.keys()]
        categoryAxis.append(categories)
        categoryAxis.setLabelsAngle(-90)
        chart = QChart()
        chart.addAxis(categoryAxis, Qt.AlignBottom)
        chart.addAxis(valueAxis, Qt.AlignLeft)
        barSeries.attachAxis(categoryAxis)
        barSeries.attachAxis(valueAxis)
        chart.addSeries(barSeries)
        chart.setTitle(qtMakeBold("Games played with each killer"))
        chart.setAnimationOptions(QChart.SeriesAnimations)
        chart.legend().setVisible(True)
        chart.legend().setAlignment(Qt.AlignRight)
        chartView = QChartView(chart)
        chartView.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        chartView.setRenderHint(QPainter.Antialiasing)
        return chartView

    def __setupTotalEliminationsInfo(self, eliminationInfo: EliminationInfo) -> QVBoxLayout:
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 10, 0, 0)
        label = QLabel(qtMakeBold("Total elimination info:"))
        margins = (50, 0, 0, 0)
        sacrificesLayout, killsLayout, dcsLayout = QHBoxLayout(), QHBoxLayout(), QHBoxLayout()
        sacrificesInfoLabel, sacrificesLabel = QLabel(qtMakeBold("Sacrifices")), QLabel(qtMakeBold(f"{eliminationInfo.sacrifices:,}"))
        killsInfoLabel, killsLabel = QLabel(qtMakeBold("Kills")), QLabel(qtMakeBold(f"{eliminationInfo.kills:,}"))
        dcsInfoLabel, dcsLabel = QLabel(qtMakeBold("Disconnects")), QLabel(qtMakeBold(f"{eliminationInfo.disconnects:,}"))
        layout.addWidget(label)
        self.__setStatSubLayout(sacrificesLayout, sacrificesInfoLabel, sacrificesLabel, margins)
        self.__setStatSubLayout(killsLayout, killsInfoLabel, killsLabel, margins)
        self.__setStatSubLayout(dcsLayout, dcsInfoLabel, dcsLabel, margins)
        addSubLayouts(layout, sacrificesLayout, killsLayout, dcsLayout)
        return layout

    def __setupAverageKillsChart(self, killerStats: KillerMatchStatistics):
        histogram = killerStats.averageKillerKillsPerMatch
        categoryAxis, valueAxis = QBarCategoryAxis(), QValueAxis()
        categories = [k.killerAlias for k in histogram.keys()]
        categoryAxis.append(categories)
        categoryAxis.setLabelsAngle(-90)
        valueAxis.setRange(0, max(histogram.values()))
        barset = QBarSet("Average kills per match")
        for k in histogram.keys():
            barset.append(histogram[k])
        barSeries = QBarSeries()
        barSeries.attachAxis(categoryAxis)
        barSeries.attachAxis(valueAxis)
        barSeries.append(barset)
        chart = QChart()
        chart.addAxis(categoryAxis, Qt.AlignBottom)
        chart.addAxis(valueAxis, Qt.AlignLeft)
        chart.addSeries(barSeries)
        chart.setTitle(qtMakeBold("Average kills per match by killer"))
        chart.setAnimationOptions(QChart.SeriesAnimations)
        chart.legend().setVisible(True)
        chart.legend().setAlignment(Qt.AlignRight)
        chartView = QChartView(chart)
        chartView.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        chartView.setRenderHint(QPainter.Antialiasing)
        return chartView
