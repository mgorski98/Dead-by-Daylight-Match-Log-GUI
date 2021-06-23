from __future__ import annotations

from abc import ABC
from collections import defaultdict
from dataclasses import dataclass
from functools import reduce
from typing import Callable, Iterable, Optional

import numpy as np
import pandas as pd

from classutil import DBDResources
from models import SurvivorMatch, KillerMatch, Survivor, Killer, Realm, GameMap, ItemType, \
    SurvivorMatchResult, FacedSurvivorState

from util import singleOrPlural

@dataclass(frozen=True)
class EliminationInfo(object):
    sacrifices: int
    kills: int
    disconnects: int

    def __add__(self, other):
        if not isinstance(other, EliminationInfo):
            raise TypeError("'add' operation not supported between instances of EliminationInfo and " + str(type(other)))
        return EliminationInfo(self.sacrifices + other.sacrifices, self.kills + other.kills, self.disconnects + other.disconnects)

    def __str__(self):
        return f'Sacrifices: {self.sacrifices:,}\nKills: {self.kills:,}\nDisconnects: {self.disconnects:,}'

    def __repr__(self):
        return self.__str__()

@dataclass(frozen=True)
class FavouriteKillerInfo(object):
    killer: Killer
    gamesWithKiller: int
    totalGames: int

    def __str__(self):
        return f'Favourite killer: {self.killer.killerAlias} ({self.gamesWithKiller:,} {singleOrPlural(self.gamesWithKiller, "game")} out of {self.totalGames:,})'

    def __repr__(self):
        return self.__str__()

@dataclass(frozen=True)
class CommonKillerInfo(object):
    killer: Killer
    encounters: int
    totalGames: int

    def __str__(self):
        return f'{self.killer.killerAlias} ({self.encounters:,} {singleOrPlural(self.encounters, "game")} out of {self.totalGames:,})'

    def __repr__(self):
        return self.__str__()

@dataclass(frozen=True)
class LethalKillerInfo(object):
    killer: Killer
    deathsCount: int
    totalGames: int
    killRatio: float

    def __str__(self):
        return f'Killed by {self.killer.killerAlias} {self.deathsCount:,} {singleOrPlural(self.deathsCount, "time")} out of {self.totalGames:,} with kill ratio of {self.killRatio:.2}'

    def __repr__(self):
        return self.__str__()

@dataclass(frozen=True)
class CommonSurvivorInfo(object):
    survivor: Survivor
    encounters: int
    totalGames: int

    def __str__(self):
        return f'{self.survivor.survivorName} ({self.encounters:,} {singleOrPlural(self.encounters, "game")} out of {self.totalGames:,})'

    def __repr__(self):
        return self.__str__()

@dataclass(frozen=True)
class MapInfo(object):
    map: GameMap
    mapGames: int
    totalGames: int

    def __str__(self):
        return f'{self.map.mapName} ({self.mapGames:,} {singleOrPlural(self.mapGames, "game")} out of {self.totalGames:,})'

    def __repr__(self):
        return self.__str__()

@dataclass(frozen=True)
class MapRealmInfo(object):
    realm: Realm
    realmGames: int
    totalGames: int

    def __str__(self):
        return f'{self.realm.realmName} ({self.realmGames:,} {singleOrPlural(self.realmGames, "game")} out of {self.totalGames:,})'

    def __repr__(self):
        return self.__str__()

@dataclass(frozen=True)
class MatchStatistics(ABC):
    averagePointsPerMatch: int
    totalGames: int

@dataclass(frozen=True)
class GeneralMatchStatistics(MatchStatistics):
    totalPoints: int
    mostCommonMapData: MapInfo
    mostCommonMapRealmData: MapRealmInfo
    leastCommonMapData: MapInfo
    leastCommonMapRealmData: MapRealmInfo

@dataclass(frozen=True)
class KillerMatchStatistics(MatchStatistics):
    totalEliminationsInfo: EliminationInfo
    gamesPlayedWithKiller: dict[Killer, int]
    totalSurvivorStatesHistogram: dict[FacedSurvivorState, int]
    facedSurvivorStatesHistogram: dict[Survivor, dict[FacedSurvivorState, int]] #amount of times certain survivor escaped, was killed, etc.
    favouriteKillerInfo: FavouriteKillerInfo #killer, games with him, total games
    totalKillerEliminations: dict[Killer, EliminationInfo]
    averageKillerKillsPerMatch: dict[Killer, float]
    mostCommonSurvivorData: CommonSurvivorInfo
    leastCommonSurvivorData: CommonSurvivorInfo

@dataclass(frozen=True)
class SurvivorMatchStatistics(MatchStatistics):
    gamesPlayedWithSurvivor: dict[Survivor, int]
    matchResultsHistogram: dict[SurvivorMatchResult, int]
    mostCommonItemType: ItemType
    mostCommonKillerData: CommonKillerInfo
    mostLethalKillerData: LethalKillerInfo
    leastCommonKillerData: CommonKillerInfo
    leastLethalKillerData: LethalKillerInfo


class StatisticsCalculator(object):

    def __init__(self, killerGames: Iterable[KillerMatch], survivorGames: Iterable[SurvivorMatch], resources: DBDResources):
        self.resources = resources
        dictMapper = lambda g: g.asDict()
        generalColumns = ["points", "map", "offering", "date", "rank"]
        killerColumns = ["killer", "perks", "survivors", "addons", "sacrifices", "kills", "disconnects"]
        survivorColumns = ["survivor", "faced killer", "item", "match result", "party size", "perks", "addons"]
        self.survivorGamesDf = pd.DataFrame(data=map(dictMapper, survivorGames), columns=generalColumns + survivorColumns)
        self.killerGamesDf = pd.DataFrame(data=map(dictMapper, killerGames), columns=generalColumns + killerColumns)

    def calculateKillerGeneral(self) -> Optional[KillerMatchStatistics]:
        if self.killerGamesDf.empty:
            return None
        totalMoris = self.killerGamesDf['kills'].sum()
        totalSacrifices = self.killerGamesDf['sacrifices'].sum()
        totalDcs = self.killerGamesDf['disconnects'].sum()
        totalGamesWithKiller = self.killerGamesDf.groupby('killer', sort=False).size().to_dict()

        favouriteKiller = max(totalGamesWithKiller, key=totalGamesWithKiller.get)
        favouriteKillerInfo = FavouriteKillerInfo(killer=favouriteKiller, gamesWithKiller=totalGamesWithKiller[favouriteKiller],
                                                  totalGames=self.killerGamesDf.shape[0])

        averagePoints = self.killerGamesDf['points'].sum() // self.killerGamesDf.shape[0]

        flatSurvivorList = reduce(lambda x, y: x + y, self.killerGamesDf['survivors'].tolist(), [])

        totalSurvivorStatesDict = defaultdict(int)
        facedSurvivorStatesHistogram = defaultdict(lambda: defaultdict(int))

        for fs in flatSurvivorList:
            totalSurvivorStatesDict[fs.state] += 1
            facedSurvivorStatesHistogram[fs.facedSurvivor][fs.state] += 1

        totalEliminationsInfo = EliminationInfo(sacrifices=totalSacrifices, kills=totalMoris, disconnects=totalDcs)

        uniquePlayedKillers = self.killerGamesDf["killer"].unique()

        totalKillerEliminations = {k: EliminationInfo(0,0,0) for k in uniquePlayedKillers}
        for killer in totalKillerEliminations.keys():
            df = self.killerGamesDf[self.killerGamesDf["killer"] == killer]
            totalKillerEliminations[killer] += EliminationInfo(df["sacrifices"].sum(), df["kills"].sum(), df["disconnects"].sum())

        killerAverageKillsPerMatch = {k: 0 for k in uniquePlayedKillers}
        for killer in killerAverageKillsPerMatch.keys():
            df = self.killerGamesDf[self.killerGamesDf["killer"] == killer]
            totalEliminations = df["kills"].sum() + df["sacrifices"].sum() + df["disconnects"].sum()
            killerAverageKillsPerMatch[killer] = totalEliminations / totalGamesWithKiller[killer]

        facedSurvivorsDf = pd.DataFrame(data=map(lambda _fs: _fs.facedSurvivor, flatSurvivorList))
        facedSurvivorHistogram = facedSurvivorsDf["survivorName"].value_counts()
        mostCommonSurvivor = next(s for s in self.resources.survivors if s.survivorName == facedSurvivorHistogram.idxmax())
        leastCommonSurvivor = next(s for s in self.resources.survivors if s.survivorName == facedSurvivorHistogram.idxmin())
        facedSurvivorsDict = facedSurvivorHistogram.to_dict()

        def survivorGamesCount(surv: Survivor):
            mask = self.killerGamesDf["survivors"].apply(lambda x: any(y.facedSurvivor == surv for y in x))
            return self.killerGamesDf[mask].shape[0]

        mostCommonSurvivorGames = survivorGamesCount(mostCommonSurvivor)
        leastCommonSurvivorGames = survivorGamesCount(leastCommonSurvivor)
        mostCommonSurvivorInfo = CommonSurvivorInfo(survivor=mostCommonSurvivor, encounters=facedSurvivorsDict[mostCommonSurvivor.survivorName], totalGames=mostCommonSurvivorGames)
        leastCommonSurvivorInfo = CommonSurvivorInfo(survivor=leastCommonSurvivor, encounters=facedSurvivorsDict[leastCommonSurvivor.survivorName], totalGames=leastCommonSurvivorGames)

        return KillerMatchStatistics(totalEliminationsInfo=totalEliminationsInfo, gamesPlayedWithKiller=totalGamesWithKiller,
                                            totalSurvivorStatesHistogram=totalSurvivorStatesDict, facedSurvivorStatesHistogram=facedSurvivorStatesHistogram,
                                            averagePointsPerMatch=averagePoints, totalKillerEliminations=totalKillerEliminations,
                                            favouriteKillerInfo=favouriteKillerInfo, averageKillerKillsPerMatch=killerAverageKillsPerMatch,
                                            mostCommonSurvivorData=mostCommonSurvivorInfo, leastCommonSurvivorData=leastCommonSurvivorInfo,
                                            totalGames=self.killerGamesDf.shape[0])

    def calculateSurvivorGeneral(self) -> Optional[SurvivorMatchStatistics]:
        if self.survivorGamesDf.empty:
            return None
        survivorGamesHistogram = self.survivorGamesDf.groupby('survivor', sort=False).size().to_dict()
        facedKillerHistogram = self.survivorGamesDf.groupby('faced killer', sort=False).size()
        facedKillerHistogramDict = facedKillerHistogram.to_dict()
        averagePoints = self.survivorGamesDf['points'].sum() // self.survivorGamesDf.shape[0]
        mostCommonKiller = facedKillerHistogram.idxmax()
        leastCommonKiller = facedKillerHistogram.idxmin()
        mostCommonItemType = self.survivorGamesDf.groupby('item', sort=False).size().notnull().idxmax().itemType
        facedKillerMatchResults = self.survivorGamesDf.groupby(["faced killer", "match result"], sort=False).size()
        lossResults = (SurvivorMatchResult.Sacrificed, SurvivorMatchResult.Killed, SurvivorMatchResult.Camped,
                       SurvivorMatchResult.Dead, SurvivorMatchResult.Tunnelled)
        killerEliminations = defaultdict(int)
        for index, count in facedKillerMatchResults.iteritems():
            killer, result = index
            killerEliminations[killer] += int(result in lossResults)
        lethalityMapper = lambda k: killerEliminations[k] / facedKillerHistogramDict[k] #that name, lmao
        mostLethalKiller = max(killerEliminations, key=lethalityMapper)
        leastLethalKiller = min(killerEliminations, key=lethalityMapper)
        matchResultsHistogram = self.survivorGamesDf.groupby('match result', sort=False).size().to_dict()
        mostLethalKillerInfo = LethalKillerInfo(killer=mostLethalKiller, deathsCount=killerEliminations[mostLethalKiller],
                                                    totalGames=facedKillerHistogramDict[mostLethalKiller],
                                                    killRatio=killerEliminations[mostLethalKiller] / facedKillerHistogramDict[mostLethalKiller])
        mostCommonKillerInfo = CommonKillerInfo(killer=mostCommonKiller,
                                                    encounters=facedKillerHistogramDict[mostCommonKiller],
                                                    totalGames=self.survivorGamesDf.shape[0])
        leastLethalKillerInfo = LethalKillerInfo(killer=leastLethalKiller, deathsCount=killerEliminations[leastLethalKiller],
                                                 totalGames=facedKillerHistogramDict[leastLethalKiller],
                                                 killRatio=killerEliminations[leastLethalKiller] / facedKillerHistogramDict[leastLethalKiller])
        leastCommonKillerInfo = CommonKillerInfo(killer=leastCommonKiller,
                                                 encounters=facedKillerHistogramDict[leastCommonKiller],
                                                 totalGames=self.survivorGamesDf.shape[0])
        return SurvivorMatchStatistics(gamesPlayedWithSurvivor=survivorGamesHistogram, averagePointsPerMatch=averagePoints,
                                              matchResultsHistogram=matchResultsHistogram, mostCommonItemType=mostCommonItemType,
                                              mostCommonKillerData=mostCommonKillerInfo, mostLethalKillerData=mostLethalKillerInfo,
                                              leastCommonKillerData=leastCommonKillerInfo, leastLethalKillerData=leastLethalKillerInfo,
                                              totalGames=self.survivorGamesDf.shape[0])


    def calculateGeneral(self) -> GeneralMatchStatistics:
        totalGames = self.survivorGamesDf.shape[0] + self.killerGamesDf.shape[0]

        survivorPoints = self.survivorGamesDf['points'].sum() if not self.survivorGamesDf.empty else 0
        killerPoints = self.killerGamesDf['points'].sum() if not self.killerGamesDf.empty else 0
        totalPoints = survivorPoints + killerPoints
        x = self.survivorGamesDf.shape[0] + self.killerGamesDf.shape[0]
        averagePoints = totalPoints // (1 if x == 0 else x)

        survivorMapHistogram = self.survivorGamesDf.groupby('map',sort=False).size()
        killerMapHistogram = self.killerGamesDf.groupby('map',sort=False).size()

        totalMapHistogram = pd.concat([survivorMapHistogram,killerMapHistogram],axis=1).fillna(value=0)
        totalMapHistogram = pd.DataFrame(data=(totalMapHistogram[0] + totalMapHistogram[1]).astype(int), columns=['count'])

        totalGamesWithMapPresent = totalMapHistogram['count'].sum()

        mostCommonMap: GameMap = totalMapHistogram.idxmax()[0] if not totalMapHistogram.empty else None
        leastCommonMap: GameMap = totalMapHistogram.idxmin()[0] if not totalMapHistogram.empty else None

        realmsDict = defaultdict(int)
        for row in totalMapHistogram.itertuples():
            realmsDict[row.Index.realm] += row.count

        mostCommonRealm = max(realmsDict, key=realmsDict.get) if len(realmsDict) > 0 else None
        leastCommonRealm = min(realmsDict, key=realmsDict.get) if len(realmsDict) > 0 else None

        mostCommonMapGames = totalMapHistogram[totalMapHistogram.index == mostCommonMap]['count'][0] if not totalMapHistogram.empty else 0
        leastCommonMapGames = totalMapHistogram[totalMapHistogram.index == leastCommonMap]['count'][0] if not totalMapHistogram.empty else 0

        mostCommonRealmGames = realmsDict[mostCommonRealm] if len(realmsDict) > 0 else 0
        leastCommonRealmGames = realmsDict[leastCommonRealm] if len(realmsDict) > 0 else 0

        mostCommonMapInfo = MapInfo(totalGames=totalGamesWithMapPresent, map=mostCommonMap, mapGames=mostCommonMapGames)
        leastCommonMapInfo = MapInfo(totalGames=totalGamesWithMapPresent, map=leastCommonMap, mapGames=leastCommonMapGames)
        mostCommonRealmInfo = MapRealmInfo(totalGames=totalGamesWithMapPresent, realm=mostCommonRealm, realmGames=mostCommonRealmGames)
        leastCommonRealmInfo = MapRealmInfo(totalGames=totalGamesWithMapPresent, realm=leastCommonRealm, realmGames=leastCommonRealmGames)

        return GeneralMatchStatistics(averagePointsPerMatch=averagePoints, totalGames=totalGames, totalPoints=totalPoints,
                                      mostCommonMapData=mostCommonMapInfo, mostCommonMapRealmData=mostCommonRealmInfo,
                                      leastCommonMapData=leastCommonMapInfo, leastCommonMapRealmData=leastCommonRealmInfo)



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

