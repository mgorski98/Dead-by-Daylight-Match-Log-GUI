from __future__ import annotations
from dataclasses import dataclass, field
from abc import abstractmethod, ABC

import sqlalchemy
from sqlalchemy.orm import registry, relationship, backref
from sqlalchemy import Table, Column, Integer, Text, ForeignKey, Date
from datetime import date
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
        Column("killerID", Integer, primary_key=True),
        Column("killerName", Text, unique=True, nullable=False),
        Column("killerAlias", Text, unique=True, nullable=False)
    )
    killerID: int = field(init=False)
    killerName: str
    killerAlias: str


@mapperRegistry.mapped
@dataclass
class Survivor:
    __table__ = Table(
        "survivors",
        mapperRegistry.metadata,
        Column("survivorID", Integer, primary_key=True),
        Column("survivorName", Text, unique=True, nullable=False)
    )
    survivorID: int = field(init=False)
    survivorName: str


@mapperRegistry.mapped
@dataclass
class FacedSurvivor:
    __table__ = Table(
        "faced_survivors",
        mapperRegistry.metadata,
        Column("facedSurvivorID", Integer, primary_key=True),
        Column("facedSurvivorName", )
    )
    facedSurvivorID: int = field(init=False)
    facedSurvivorName: str
    killerMatchID: int = field(init=False)


@mapperRegistry.mapped
@dataclass
class Item:
    __table__ = Table(
        "items",
        mapperRegistry.metadata,
        Column("itemID", Integer, primary_key=True),
        Column("itemName", Text, nullable=False, unique=True),
        Column("itemType", sqlalchemy.Enum(ItemType), nullable=False)
    )
    itemID: int = field(init=False)
    itemName: str
    itemType: ItemType


@mapperRegistry.mapped
@dataclass
class GameMap:
    __table__ = Table(
        "maps",
        mapperRegistry.metadata,
        Column("mapID", Integer, primary_key=True),
        Column("mapName", Text, nullable=False, unique=True),
        Column("realmID", Integer, ForeignKey("realms.realmID"), nullable=False)
    )
    mapID: int = field(init=False)
    mapName: str
    realmID: int = field(init=False)
    realm: Realm

    __mapper_args__ = {
        "properties": {
            "realm": relationship("Realm", uselist=False, back_populates="maps")
        }
    }


@mapperRegistry.mapped
@dataclass
class Realm:
    __table__ = Table(
        "realms",
        mapperRegistry.metadata,
        Column("realmID", Integer, primary_key=True),
        Column("realmName", Text, nullable=False, unique=True)
    )

    __mapper_args__ = {
        "properties": {
            "maps": relationship("GameMap", back_populates="realm")
        }
    }

    realmID: int = field(init=False)
    realmName: str
    maps: list[GameMap] = field(default_factory=list, init=False)


@mapperRegistry.mapped
@dataclass
class ItemAddon:
    __table__ = Table(
        "item_addons",
        mapperRegistry.metadata,
        Column("addonID", Integer, primary_key=True),
        Column("addonName", Text, nullable=False, unique=True),
        Column("itemType", sqlalchemy.Enum(ItemType), nullable=False)
    )
    addonID: int = field(init=False)
    addonName: str
    itemType: ItemType


@mapperRegistry.mapped
@dataclass
class KillerAddon:
    __table__ = Table(
        "killer_addons",
        mapperRegistry.metadata,
        Column("addonID", Integer, primary_key=True),
        Column("addonName", Text, nullable=False),
        Column("killerID", Integer, ForeignKey("killers.killerID"), nullable=False)
    )
    addonID: int = field(init=False)
    addonName: str
    killerID: int = field(init=False)
    killer: Killer

    __mapper_args__ = {
        "properties": {
            "killer": relationship("Killer", uselist=False)
        }
    }


@mapperRegistry.mapped
@dataclass
class Perk:
    __table__ = Table(
        "perks",
        mapperRegistry.metadata,
        Column("perkID", Integer, primary_key=True),
        Column("perkName", Text, nullable=False),
        Column("perkType", sqlalchemy.Enum(PerkType), nullable=False),
        Column("perkTier", Integer, nullable=False, default=1)
    )
    perkID: int = field(init=False)
    perkName: str
    perkType: PerkType
    perkTier: int


@mapperRegistry.mapped
@dataclass
class Offering:
    __table__ = Table(
        "offerings",
        mapperRegistry.metadata,
        Column("offeringID", Integer, primary_key=True),
        Column("offeringName", Text, nullable=False, unique=True)
    )
    offeringID: int = field(init=False)
    offeringName: str




# @mapperRegistry.mapped
# @dataclass
# class KillerMatchPerk:
#     __table__ = Table()
#
#
# @mapperRegistry.mapped
# @dataclass
# class SurvivorMatchPerk:
#     __table__ = Table()


@dataclass
class DBDMatch(ABC):
    matchID: int
    points: int
    gameMap: GameMap
    gameMapID: int
    offering: Offering
    offeringID: int
    matchDate: date
    rank: int


@mapperRegistry.mapped
@dataclass
class SurvivorMatch(DBDMatch):
    __table__ = Table(
        "survivor_matches",
        mapperRegistry.metadata,
        Column("matchID", Integer, primary_key=True),
        Column("points", Integer, default=0),
        Column("matchDate", Date, nullable=False),
        Column("rank", Integer, default=20, nullable=True),
        Column("offeringID", Integer, ForeignKey("offerings.offeringID"), nullable=True),
        Column("gameMapID", Integer, ForeignKey("maps.mapID"), nullable=True),
        Column("facedKillerID", Integer, ForeignKey("killers.killerID"), nullable=False),
        Column("itemID", Integer, ForeignKey("items.itemID"), nullable=True),
        Column("matchResult", sqlalchemy.Enum(SurvivorMatchResult), nullable=False)
    )
    facedKiller: Killer
    facedKillerID: int
    item: Item
    matchResult: SurvivorMatchResult
    itemAddons: tuple[ItemAddon]
    # perks: list[SurvivorMatchPerk]

    __mapper_args__ = {
        "properties": {

        }
    }


@mapperRegistry.mapped
@dataclass
class KillerMatch(DBDMatch):
    __table__ = Table(
        "killer_matches",
        mapperRegistry.metadata,
        Column(),
        Column(),
        Column(),
        Column(),
        Column(),
        Column(),
        Column(),
        Column(),
        Column(),
        Column()
    )
    facedSurvivors: list[FacedSurvivor]
    sacrifices: int
    kills: int
    disconnects: int
    killerAddons: tuple[KillerAddon]
    # perks: list[KillerMatchPerk]

    __mapper_args__ = {
        "properties": {

        }
    }
