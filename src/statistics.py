from dataclasses import dataclass

from models import DBDMatch, SurvivorMatch, KillerMatch


@dataclass
class MatchStatistics:
    pass

class KillerMatchStatistics(MatchStatistics):
    pass

class SurvivorMatchStatistics(MatchStatistics):
    pass

class StatisticsCalculator(object):

    def __init__(self, games: list[DBDMatch]):
        self.survivorGames = list(filter(lambda g: isinstance(g, SurvivorMatch), games))
        self.killerGames = list(filter(lambda g: isinstance(g, KillerMatch), games))

    def calculateKiller(self) -> KillerMatchStatistics:
        raise NotImplementedError()

    def calculateSurvivor(self) -> SurvivorMatchStatistics:
        raise NotImplementedError()