from dataclasses import dataclass
from abc import ABC

import pandas as pd

from models import DBDMatch, SurvivorMatch, KillerMatch, Survivor, Killer, Realm, GameMap, ItemType, SurvivorMatchResult


#todo: add export method so you can export statistics to external file (json, xml, some other formats like yaml)

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

@dataclass(frozen=True)
class GeneralSurvivorMatchStatistics(MatchStatistics):
    gamesPlayedWithSurvivor: dict[Survivor, int]
    matchResultsHistogram: dict[SurvivorMatchResult, int]
    mostCommonItemType: ItemType

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

    def __init__(self, games: list[DBDMatch]):
        self.survivorGames = list(filter(lambda g: isinstance(g, SurvivorMatch), games))
        self.killerGames = list(filter(lambda g: isinstance(g, KillerMatch), games))
        dictMapper = lambda g: g.asDict()
        self.survivorGamesDf = pd.DataFrame(data=map(dictMapper, self.survivorGames))
        self.killerGamesDf = pd.DataFrame(data=map(dictMapper, self.killerGames))

    def calculateKillerGeneral(self) -> GeneralKillerMatchStatistics:
        raise NotImplementedError()

    def calculateSurvivorGeneral(self) -> GeneralSurvivorMatchStatistics:
        raise NotImplementedError()

    def calculateForSurvivor(self, survivor: Survivor) -> TargetSurvivorStatistics:
        raise NotImplementedError()

    def calculateForKiller(self, killer: Killer) -> TargetKillerStatistics:
        raise NotImplementedError()

    def calculateGeneral(self) -> GeneralMatchStatistics:
        raise NotImplementedError()


class StatisticsExporter(object):

    __export_types__ = {
        "xml": None,
        "json": None,
        "yaml": None
    }

    def __init__(self, exportType: str):
        self.exportHandler = StatisticsExporter.__export_types__.get(exportType)
        if self.exportHandler is None:
            validOptions = ', '.join(StatisticsExporter.__export_types__.keys())
            raise ValueError(f"Unknown export type: {exportType}. Valid options are: {validOptions}")

    def export(self, statistics: MatchStatistics, destinationPath: str) -> None:
        pass