from __future__ import annotations
from dataclasses import dataclass
from abc import ABC
from typing import Callable
from collections import defaultdict

import pandas as pd

from classutil import DBDResources
from models import DBDMatch, SurvivorMatch, KillerMatch, Survivor, Killer, Realm, GameMap, ItemType, \
    SurvivorMatchResult, FacedSurvivorState


@dataclass(frozen=True)
class EliminationInfo(object):
    sacrifices: int
    kills: int
    disconnects: int

class MatchStatistics(ABC):
    pass

@dataclass(frozen=True)
class GeneralMatchStatistics(MatchStatistics):
    totalPoints: int
    mostCommonMap: GameMap
    mostCommonMapRealm: Realm

@dataclass(frozen=True)
class GeneralKillerMatchStatistics(MatchStatistics):
    totalSacrifices: int
    totalKills: int
    totalDisconnects: int
    gamesPlayedWithKiller: dict[Killer, int]
    totalSurvivorStatesHistogram: dict[FacedSurvivorState, int]
    facedSurvivorStatesHistogram: dict[Survivor, dict[FacedSurvivorState, int]] #amount of times certain survivor escaped, was killed, etc.

@dataclass(frozen=True)
class GeneralSurvivorMatchStatistics(MatchStatistics):
    gamesPlayedWithSurvivor: dict[Survivor, int]
    matchResultsHistogram: dict[SurvivorMatchResult, int]
    mostCommonItemType: ItemType
    mostCommonKiller: Killer
    mostLethalKiller: Killer

@dataclass(frozen=True)
class TargetStatistics(MatchStatistics):
    pass

@dataclass(frozen=True)
class TargetKillerStatistics(MatchStatistics):
    pass

@dataclass(frozen=True)
class TargetSurvivorStatistics(MatchStatistics):
    pass

class StatisticsCalculator(object):

    def __init__(self, games: list[DBDMatch], resources: DBDResources):
        self.survivorGames = list(filter(lambda g: isinstance(g, SurvivorMatch), games))
        self.killerGames = list(filter(lambda g: isinstance(g, KillerMatch), games))
        self.resources = resources
        dictMapper = lambda g: g.asDict()
        self.survivorGamesDf = pd.DataFrame(data=map(dictMapper, self.survivorGames))
        self.killerGamesDf = pd.DataFrame(data=map(dictMapper, self.killerGames))

    def calculateKillerGeneral(self) -> GeneralKillerMatchStatistics:
        totalMoris = self.killerGamesDf['kills'].sum()
        totalSacrifices = self.killerGamesDf['sacrifices'].sum()
        totalDcs = self.killerGamesDf['disconnects'].sum()
        totalGamesWithKiller = self.killerGamesDf.groupby('killer', sort=False).size()

        totalSurvivorStatesDict = defaultdict(int)
        for facedSurvivorList in self.killerGamesDf['survivors']:
            for fs in facedSurvivorList:
                totalSurvivorStatesDict[fs.state] += 1

        facedSurvivorStatesHistogram = defaultdict(lambda: defaultdict(int))
        for facedSurvivorList in self.killerGamesDf['survivors']:
            for fs in facedSurvivorList:
                facedSurvivorStatesHistogram[fs.facedSurvivor][fs.state] += 1


    def calculateSurvivorGeneral(self) -> GeneralSurvivorMatchStatistics:
        mostCommonKiller = self.survivorGamesDf.groupby('faced killer', sort=False).size().idxmax()
        mostCommonItemType = None
        mostLethalKiller = None
        matchResultsHistogram = None

    def calculateForSurvivor(self, survivor: Survivor) -> TargetSurvivorStatistics:
        raise NotImplementedError()

    def calculateForKiller(self, killer: Killer) -> TargetKillerStatistics:
        raise NotImplementedError()

    def calculateGeneral(self) -> GeneralMatchStatistics:
        totalPoints = self.survivorGamesDf['points'].sum() + self.killerGamesDf['points'].sum()
        survivorMapHistogram = self.survivorGamesDf.groupby('map',sort=False).size()
        killerMapHistogram = self.killerGamesDf.groupby('map',sort=False).size()
        totalMapHistogram = pd.concat([survivorMapHistogram,killerMapHistogram],axis=1).fillna(value=0)
        totalMapHistogram = pd.DataFrame(data=(totalMapHistogram[0] + totalMapHistogram[1]).astype(int), columns=['count'])
        mostCommonMap: GameMap = totalMapHistogram.idxmax()[0]
        realmsDict = defaultdict(int)
        for row in totalMapHistogram.itertuples():
            realmsDict[row.Index.realm] += row.count
        mostCommonRealm = max(realmsDict, key=realmsDict.get)
        return GeneralMatchStatistics(totalPoints=totalPoints, mostCommonMap=mostCommonMap, mostCommonMapRealm=mostCommonRealm)


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

