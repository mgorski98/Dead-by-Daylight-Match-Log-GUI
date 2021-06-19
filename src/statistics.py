from __future__ import annotations

from abc import ABC
from collections import defaultdict
from dataclasses import dataclass
from typing import Callable, Iterable, Optional

import numpy as np
import pandas as pd

from classutil import DBDResources
from models import SurvivorMatch, KillerMatch, Survivor, Killer, Realm, GameMap, ItemType, \
    SurvivorMatchResult, FacedSurvivorState


@dataclass(frozen=True)
class EliminationInfo(object):
    sacrifices: int
    kills: int
    disconnects: int

@dataclass(frozen=True)
class CommonKillerInfo(object):
    killer: Killer
    encounters: int
    totalGames: int

@dataclass(frozen=True)
class LethalKillerInfo(object):
    killer: Killer
    deathsCount: int
    totalGames: int
    killRatio: float

@dataclass(frozen=True)
class MatchStatistics(ABC):
    averagePointsPerMatch: float

@dataclass(frozen=True)
class GeneralMatchStatistics(MatchStatistics):
    totalPoints: int
    mostCommonMap: GameMap
    mostCommonMapRealm: Realm

@dataclass(frozen=True)
class GeneralKillerMatchStatistics(MatchStatistics):
    totalEliminationsInfo: EliminationInfo
    gamesPlayedWithKiller: dict[Killer, int]
    totalSurvivorStatesHistogram: dict[FacedSurvivorState, int]
    facedSurvivorStatesHistogram: dict[Survivor, dict[FacedSurvivorState, int]] #amount of times certain survivor escaped, was killed, etc.

@dataclass(frozen=True)
class GeneralSurvivorMatchStatistics(MatchStatistics):
    gamesPlayedWithSurvivor: dict[Survivor, int]
    matchResultsHistogram: dict[SurvivorMatchResult, int]
    mostCommonItemType: ItemType
    mostCommonKillerData: CommonKillerInfo
    mostLethalKillerData: LethalKillerInfo
    leastCommonKillerData: object
    leastLethalKillerData: object


class StatisticsCalculator(object):

    def __init__(self, killerGames: Iterable[KillerMatch], survivorGames: Iterable[SurvivorMatch], resources: DBDResources):
        self.resources = resources
        dictMapper = lambda g: g.asDict()
        generalColumns = ["points", "map", "offering", "date", "rank"]
        killerColumns = ["killer", "perks", "survivors", "addons", "sacrifices", "kills", "disconnects"]
        survivorColumns = ["survivor", "faced killer", "item", "match result", "party size", "perks", "addons"]
        self.survivorGamesDf = pd.DataFrame(data=map(dictMapper, survivorGames), columns=generalColumns + survivorColumns)
        self.killerGamesDf = pd.DataFrame(data=map(dictMapper, killerGames), columns=generalColumns + killerColumns)

    def calculateKillerGeneral(self) -> Optional[GeneralKillerMatchStatistics]:
        if self.killerGamesDf.empty:
            return None
        totalMoris = self.killerGamesDf['kills'].sum()
        totalSacrifices = self.killerGamesDf['sacrifices'].sum()
        totalDcs = self.killerGamesDf['disconnects'].sum()
        totalGamesWithKiller = self.killerGamesDf.groupby('killer', sort=False).size().to_dict()
        averagePoints = self.killerGamesDf['points'].sum() / self.killerGamesDf.shape[0]

        flatSurvivorList = np.ravel(self.killerGamesDf['survivors'].tolist())

        totalSurvivorStatesDict = defaultdict(int)
        facedSurvivorStatesHistogram = defaultdict(lambda: defaultdict(int))

        for fs in flatSurvivorList:
            totalSurvivorStatesDict[fs.state] += 1
            facedSurvivorStatesHistogram[fs.facedSurvivor][fs.state] += 1

        eliminationsInfo = EliminationInfo(sacrifices=totalSacrifices, kills=totalMoris, disconnects=totalDcs)

        return GeneralKillerMatchStatistics(totalEliminationsInfo=eliminationsInfo, gamesPlayedWithKiller=totalGamesWithKiller,
                                            totalSurvivorStatesHistogram=totalSurvivorStatesDict, facedSurvivorStatesHistogram=facedSurvivorStatesHistogram,
                                            averagePointsPerMatch=averagePoints)

    def calculateSurvivorGeneral(self) -> Optional[GeneralSurvivorMatchStatistics]:
        if self.survivorGamesDf.empty:
            return None
        survivorGamesHistogram = self.survivorGamesDf.groupby('survivor', sort=False).size().to_dict()
        facedKillerHistogram = self.survivorGamesDf.groupby('faced killer', sort=False).size()
        facedKillerHistogramDict = facedKillerHistogram.to_dict()
        averagePoints = self.survivorGamesDf['points'].sum() / self.survivorGamesDf.shape[0]
        mostCommonKiller = facedKillerHistogram.idxmax()
        mostCommonItemType = self.survivorGamesDf.groupby('item', sort=False).size().notnull().idxmax().itemType
        facedKillerMatchResults = self.survivorGamesDf.groupby(["faced killer", "match result"], sort=False).size()
        lossResults = (SurvivorMatchResult.Sacrificed, SurvivorMatchResult.Killed, SurvivorMatchResult.Camped,
                       SurvivorMatchResult.Dead, SurvivorMatchResult.Tunnelled)
        killerEliminations = defaultdict(int)
        for index, count in facedKillerMatchResults.iteritems():
            killer, result = index
            killerEliminations[killer] += int(result in lossResults)
        mostLethalKiller = max(killerEliminations, key=lambda k: killerEliminations[k] / facedKillerHistogramDict[k])
        matchResultsHistogram = self.survivorGamesDf.groupby('match result', sort=False).size().to_dict()
        mostLethalKillerInfo = LethalKillerInfo(killer=mostLethalKiller, deathsCount=killerEliminations[mostLethalKiller],
                                                    totalGames=facedKillerHistogramDict[mostLethalKiller],
                                                    killRatio=killerEliminations[mostLethalKiller] / facedKillerHistogramDict[mostLethalKiller])
        mostCommonKillerInfo = CommonKillerInfo(killer=mostCommonKiller,
                                                    encounters=facedKillerHistogramDict[mostCommonKiller],
                                                    totalGames=self.survivorGamesDf.shape[0])
        return GeneralSurvivorMatchStatistics(gamesPlayedWithSurvivor=survivorGamesHistogram, averagePointsPerMatch=averagePoints,
                                              matchResultsHistogram=matchResultsHistogram, mostCommonItemType=mostCommonItemType,
                                              mostCommonKillerData=mostCommonKillerInfo, mostLethalKillerData=mostLethalKillerInfo)


    def calculateGeneral(self) -> GeneralMatchStatistics:
        survivorPoints = self.survivorGamesDf['points'].sum() if not self.survivorGamesDf.empty else 0
        killerPoints = self.killerGamesDf['points'].sum() if not self.killerGamesDf.empty else 0
        totalPoints = survivorPoints + killerPoints
        x = self.survivorGamesDf.shape[0] + self.killerGamesDf.shape[0]
        averagePoints = totalPoints / (1 if x == 0 else x)
        survivorMapHistogram = self.survivorGamesDf.groupby('map',sort=False).size()
        killerMapHistogram = self.killerGamesDf.groupby('map',sort=False).size()
        totalMapHistogram = pd.concat([survivorMapHistogram,killerMapHistogram],axis=1).fillna(value=0)
        totalMapHistogram = pd.DataFrame(data=(totalMapHistogram[0] + totalMapHistogram[1]).astype(int), columns=['count'])
        mostCommonMap: GameMap = totalMapHistogram.idxmax()[0] if not totalMapHistogram.empty else None
        realmsDict = defaultdict(int)
        for row in totalMapHistogram.itertuples():
            realmsDict[row.Index.realm] += row.count
        mostCommonRealm = max(realmsDict, key=realmsDict.get) if len(realmsDict) > 0 else None
        return GeneralMatchStatistics(averagePointsPerMatch=averagePoints, totalPoints=totalPoints,
                                      mostCommonMap=mostCommonMap, mostCommonMapRealm=mostCommonRealm)


def exportAsJson(statistics: MatchStatistics, destinationPath: str):
    pass

def exportAsXML(statistics: MatchStatistics, destinationPath: str):
    pass

def exportAsYAML(statistics: MatchStatistics, destinationPath: str):
    pass

class StatisticsExporter(object):

    __export_types__ : dict[str, Callable[[object, str], None]] = {
        "xml": exportAsXML,
        "json": exportAsJson,
        "yaml": exportAsYAML
    }

    def __init__(self, exportType: str):
        self.exportHandler = StatisticsExporter.__export_types__.get(exportType)
        if self.exportHandler is None:
            validOptions = ', '.join(StatisticsExporter.__export_types__.keys())
            raise ValueError(f"Unknown export type: {exportType}. Valid options are: {validOptions}")

    def export(self, statistics: MatchStatistics, destinationPath: str) -> None:
        if self.exportHandler is None:
            raise ValueError("Export function handler is None")
        self.exportHandler(statistics, destinationPath)

