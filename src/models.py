from dataclasses import dataclass
from abc import abstractmethod, ABC
from sqlalchemy.orm import registry
from sqlalchemy import Table, Column, Integer, Text
from datetime import date
# from sqlalchemy.orm import Column, Integer, String, registry
from enum import Enum


mapperRegistry = registry()


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


@mapperRegistry.mapped
@dataclass
class Killer:
    __table__ = Table(
        "killers",
        mapperRegistry.metadata,
        Column("killer_id", Integer, primary_key=True, sqlite_autoincrement=True),
        Column("killer_name", Text, unique=True),
        Column("killer_alias", Text, unique=True)
    )
    killerID: int
    killerName: str
    killerAlias: str


@mapperRegistry.mapped
@dataclass
class Survivor:
    __table__ = Table(
        "survivors",
        mapperRegistry.metadata,
        Column("survivor_id", Integer, primary_key=True, sqlite_autoincrement=True),
        Column("survivor_name", Text, unique=True)
    )
    survivorID: int
    survivorName: str


@mapperRegistry.mapped
@dataclass
class FacedSurvivor:
    __table__ = Table("faced_survivors", mapperRegistry.metadata)
    facedSurvivorID: int
    facedSurvivorName: str


@mapperRegistry.mapped
@dataclass
class Item:
    __table__ = Table("items", mapperRegistry.metadata)
    itemID: int
    itemName: str
    itemType: ItemType


@mapperRegistry.mapped
@dataclass
class GameMap:
    __table__ = Table("maps", mapperRegistry.metadata)
    mapID: int
    mapName: str
    # foreign key here: realmID


@mapperRegistry.mapped
@dataclass
class Realm:
    __table__ = Table("realms", mapperRegistry.metadata)
    realmID: int
    realmName: str
    maps: list[GameMap]


@mapperRegistry.mapped
@dataclass
class ItemAddon:
    __table__ = Table("item_addons", mapperRegistry.metadata)
    addonID: int
    addonName: str
    itemType: ItemType


@mapperRegistry.mapped
@dataclass
class KillerAddon:
    __table__ = Table("killer_addons", mapperRegistry.metadata)
    addonID: int
    addonName: str
    killer: Killer


@mapperRegistry.mapped
@dataclass
class Perk:
    __table__ = Table("perks", mapperRegistry.metadata)
    perkID: int
    perkName: str
    perkType: PerkType
    perkTier: int


@mapperRegistry.mapped
@dataclass
class Offering:
    __table__ = Table("offerings", mapperRegistry.metadata)
    offeringID: int
    offeringName: str


@mapperRegistry.mapped
@dataclass
class DBDMatch(ABC):
    matchID: int
    points: int
    gameMap: str
    offering: str
    matchDate: date


@mapperRegistry.mapped
@dataclass
class SurvivorMatch(DBDMatch):
    __table__ = Table("survivor_matches", mapperRegistry.metadata)
    facedKiller: str
    item: Item
    matchResult: SurvivorMatchResult


@mapperRegistry.mapped
@dataclass
class KillerMatch(DBDMatch):
    __table__ = Table("killer_matches", mapperRegistry.metadata)
    facedSurvivors: list[FacedSurvivor]
    sacrifices: int
    kills: int
    disconnects: int
