from dataclasses import dataclass
from abc import abstractmethod, ABC
# from sqlalchemy.orm import Column, Integer, String, registry
from enum import Enum

class SurvivorMatchResult(Enum):
    Sacrificed = 0, 
    Killed = 1,
    Escaped = 2,
    HatchEscape = 3,
    Tunnelled = 4,
    Camped = 5,
    BledOut = 6

class ItemType(Enum):
    Medkit = 0,
    Key = 1, 
    Flashlight = 2,
    Toolbox = 3,
    Firecracker = 4,
    Map = 5

class PerkType(Enum):
    Killer = 0,
    Survivor = 1

@dataclass
class Killer:
    killerID: int
    killerName: str
    killerAlias: str

@dataclass
class Survivor:
    survivorID: int
    survivorName: str

@dataclass
class FacedSurvivor:
    facedSurvivorID: int
    facedSurvivorName: str

@dataclass
class FacedKiller:
    facedKillerID: int
    facedKillerName: str

@dataclass
class Item:
    itemID: int
    itemName: str
    itemType: ItemType

@dataclass
class GameMap:
    mapID: int
    mapName: str
    #foreign key here: realmID

@dataclass
class Realm:
    realmID: int
    realmName: str
    maps: list[GameMap]

@dataclass
class ItemAddon:
    addonID: int
    addonName: str
    itemType: ItemType

@dataclass
class KillerAddon:
    addonID: int
    addonName: str
    killer: Killer

@dataclass
class Perk:
    perkID: int
    perkName: str
    perkType: PerkType
    perkTier: int

@dataclass
class Offering:
    offeringID: int
    offeringName: str

@dataclass
class DBDMatch(ABC):
    matchID: int
    points: int 
    gameMap: str
    offering: str

@dataclass
class SurvivorMatch(DBDMatch):
    facedKiller: FacedKiller
    item: Item
    matchResult: SurvivorMatchResult

@dataclass
class KillerMatch(DBDMatch):
    facedSurvivors: list[FacedSurvivor]
    sacrifices: int
    kills: int
    disconnects: int