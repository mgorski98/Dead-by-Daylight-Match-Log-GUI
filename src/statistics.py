from __future__ import annotations
from dataclasses import dataclass
from abc import ABC
from typing import Callable, Iterable, Union, Optional
from collections import defaultdict

import pandas as pd
import numpy as np

from classutil import DBDResources
from models import DBDMatch, SurvivorMatch, KillerMatch, Survivor, Killer, Realm, GameMap, ItemType, \
    SurvivorMatchResult, FacedSurvivorState
from util import failQuietly


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
    totalEliminationsInfo: EliminationInfo
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

        flatSurvivorList = np.ravel(self.killerGamesDf['survivors'].tolist())

        totalSurvivorStatesDict = defaultdict(int)
        facedSurvivorStatesHistogram = defaultdict(lambda: defaultdict(int))

        for fs in flatSurvivorList:
            totalSurvivorStatesDict[fs.state] += 1
            facedSurvivorStatesHistogram[fs.facedSurvivor][fs.state] += 1

        eliminationsInfo = EliminationInfo(sacrifices=totalSacrifices, kills=totalMoris, disconnects=totalDcs)

        return GeneralKillerMatchStatistics(totalEliminationsInfo=eliminationsInfo, gamesPlayedWithKiller=totalGamesWithKiller,
                                            totalSurvivorStatesHistogram=totalSurvivorStatesDict, facedSurvivorStatesHistogram=facedSurvivorStatesHistogram)

    def calculateSurvivorGeneral(self) -> Optional[GeneralSurvivorMatchStatistics]:
        if self.survivorGamesDf.empty:
            return None
        facedKillerHistogram = self.survivorGamesDf.groupby('faced killer', sort=False).size()
        mostCommonKiller = facedKillerHistogram.idxmax()
        mostCommonItemType = self.survivorGamesDf.groupby('item', sort=False).size().notnull().idxmax().itemType
        mostLethalKiller = None
        matchResultsHistogram = self.survivorGamesDf.groupby('match result').size().to_dict()
        killerEliminations = defaultdict(int)
        for killer in facedKillerHistogram.index:
            print(killer)
        # return GeneralSurvivorMatchStatistics(mostLethalKiller=mostLethalKiller, mostCommonItemType=mostCommonItemType,
        #                                       mostCommonKiller=mostCommonKiller, matchResultsHistogram=matchResultsHistogram)


    def calculateForSurvivor(self, survivor: Survivor) -> TargetSurvivorStatistics:
        raise NotImplementedError()

    def calculateForKiller(self, killer: Killer) -> TargetKillerStatistics:
        raise NotImplementedError()

    def calculateGeneral(self) -> GeneralMatchStatistics:
        survivorPoints = self.survivorGamesDf['points'].sum() if not self.survivorGamesDf.empty else 0
        killerPoints = self.killerGamesDf['points'].sum() if not self.killerGamesDf.empty else 0
        totalPoints = survivorPoints + killerPoints
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

