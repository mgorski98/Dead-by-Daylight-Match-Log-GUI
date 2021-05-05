from dataclasses import dataclass
from abc import abstractmethod, ABC
from sqlalchemy.orm import Column, Integer, String, registry
from enum import Enum

class SurvivorMatchResult(Enum):
    Sacrificed = 0, 
    Killed = 1,
    Escaped = 2,
    HatchEscape = 3,
    Tunnelled = 4,
    Camped = 5,
    BledOut = 6

@dataclass
class FacedKiller:
    killerID: int
    killerName: str

@dataclass
class FacedSurvivor:
    survivorID: int
    survivorName: str

@dataclass
class DBDMatch(ABC):
    matchID: int
    points: int 
    character: str
    addons: list[str]
    perks: list[str]
    gameMap: str
    offering: str

@dataclass
class SurvivorMatch(DBDMatch):
    facedKiller: FacedKiller
    sacrifices: int
    kills: int
    disconnects: int


@dataclass
class KillerMatch(DBDMatch):
    facedSurvivors: list[FacedSurvivor]

@dataclass
class Realm:
    pass