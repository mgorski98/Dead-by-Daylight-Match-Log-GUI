from dataclasses import dataclass

from models import DBDMatch, SurvivorMatch, KillerMatch


@dataclass
class GeneralMatchStatistics:
    pass

@dataclass
class GeneralKillerMatchStatistics(GeneralMatchStatistics):
    totalSacrifices: int
    totalKills: int
    totalDisconnects: int

@dataclass
class GeneralSurvivorMatchStatistics(GeneralMatchStatistics):
    pass

@dataclass
class TargetStatistics(object):
    pass

@dataclass
class TargetKillerStatistics(TargetStatistics):
    pass

@dataclass
class TargetSurvivorStatistics(TargetStatistics):
    pass

class StatisticsCalculator(object):

    def __init__(self, games: list[DBDMatch]):
        self.survivorGames = list(filter(lambda g: isinstance(g, SurvivorMatch), games))
        self.killerGames = list(filter(lambda g: isinstance(g, KillerMatch), games))

    def calculateKiller(self) -> GeneralKillerMatchStatistics:
        raise NotImplementedError()

    def calculateSurvivor(self) -> GeneralSurvivorMatchStatistics:
        raise NotImplementedError()