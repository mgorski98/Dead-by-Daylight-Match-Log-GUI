from dataclasses import dataclass

import pandas as pd

from models import DBDMatch, SurvivorMatch, KillerMatch, Survivor, Killer, Realm, GameMap


@dataclass
class GeneralMatchStatistics:
    totalPoints: int
    mostCommonMap: GameMap
    mostCommonMapRealm: Realm

@dataclass
class GeneralKillerMatchStatistics(object):
    totalSacrifices: int
    totalKills: int
    totalDisconnects: int

@dataclass
class GeneralSurvivorMatchStatistics(object):
    pass

@dataclass
class TargetStatistics(object):
    pass

@dataclass
class TargetKillerStatistics(object):
    pass

@dataclass
class TargetSurvivorStatistics(object):
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