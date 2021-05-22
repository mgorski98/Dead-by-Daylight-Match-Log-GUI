from __future__ import annotations

import enum
from abc import ABC
from dataclasses import dataclass, field
from datetime import date
from typing import Optional, Callable
from io import StringIO

from sqlalchemy import Table, Column, Integer, Text, ForeignKey, Date, Enum
from sqlalchemy.orm import registry, relationship

from util import splitUpper

mapperRegistry = registry()

#<editor-fold desc="Enums">
class SurvivorMatchResult(enum.Enum):
    Sacrificed = 0
    Killed = 1
    Escaped = 2
    HatchEscape = 3
    Tunnelled = 4
    Camped = 5
    BledOut = 6
    KillerDisconnected = 7

class ItemType(enum.Enum):
    Medkit = 0
    Key = 1
    Flashlight = 2
    Toolbox = 3
    Firecracker = 4
    Map = 5

class PerkType(enum.Enum):
    Killer = 0
    Survivor = 1

class FacedSurvivorState(enum.Enum):
    Sacrificed = 0
    Killed = 1
    BledOut = 2
    Disconnected = 3
    Escaped = 4
#</editor-fold>

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
    killerID: int = field(init=False,compare=False,hash=False)
    killerName: str
    killerAlias: str

    def __str__(self):
        return f'{self.killerName} - {self.killerAlias}'

@mapperRegistry.mapped
@dataclass
class Survivor:
    __table__ = Table(
        "survivors",
        mapperRegistry.metadata,
        Column("survivorID", Integer, primary_key=True),
        Column("survivorName", Text, unique=True, nullable=False)
    )
    survivorID: int = field(init=False,compare=False,hash=False)
    survivorName: str

    def __str__(self):
        return self.survivorName


@mapperRegistry.mapped
@dataclass
class Item:
    __table__ = Table(
        "items",
        mapperRegistry.metadata,
        Column("itemID", Integer, primary_key=True),
        Column("itemName", Text, nullable=False, unique=True),
        Column("itemType", Enum(ItemType), nullable=False)
    )
    itemID: int = field(init=False,compare=False,hash=False)
    itemName: str
    itemType: ItemType

    def __str__(self):
        return self.itemName

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
    mapID: int = field(init=False,compare=False,hash=False)
    mapName: str
    realmID: int = field(init=False,compare=False,hash=False)

    def __str__(self):
        return self.mapName

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
            "maps": relationship("GameMap", lazy='subquery')
        }
    }

    realmID: int = field(init=False,compare=False,hash=False)
    realmName: str
    maps: list[GameMap] = field(default_factory=list)


@mapperRegistry.mapped
@dataclass
class ItemAddon:
    __table__ = Table(
        "item_addons",
        mapperRegistry.metadata,
        Column("addonID", Integer, primary_key=True),
        Column("addonName", Text, nullable=False, unique=True),
        Column("itemType", Enum(ItemType), nullable=False)
    )
    addonID: int = field(init=False,compare=False,hash=False)
    addonName: str
    itemType: ItemType

    def __str__(self):
        return self.addonName

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
    addonID: int = field(init=False,compare=False,hash=False)
    addonName: str
    killerID: int = field(init=False,compare=False,hash=False)
    killer: Killer

    __mapper_args__ = {
        "properties": {
            "killer": relationship("Killer", uselist=False, lazy='subquery')
        }
    }

    def __str__(self):
        return self.addonName

@mapperRegistry.mapped
@dataclass
class Perk:
    __table__ = Table(
        "perks",
        mapperRegistry.metadata,
        Column("perkID", Integer, primary_key=True),
        Column("perkName", Text, nullable=False),
        Column("perkType", Enum(PerkType), nullable=False),
        Column("perkTier", Integer, nullable=False, default=1)
    )
    perkID: int = field(init=False,compare=False,hash=False)
    perkName: str
    perkType: PerkType
    perkTier: int

    def __str__(self):
        return f'{self.perkName} {"I" * self.perkTier}'


@mapperRegistry.mapped
@dataclass
class Offering:
    __table__ = Table(
        "offerings",
        mapperRegistry.metadata,
        Column("offeringID", Integer, primary_key=True),
        Column("offeringName", Text, nullable=False, unique=True)
    )
    offeringID: int = field(init=False,compare=False,hash=False)
    offeringName: str

    def __str__(self):
        return self.offeringName


@mapperRegistry.mapped
@dataclass
class KillerMatchPerk:
    __table__ = Table(
        "killer_match_perks",
        mapperRegistry.metadata,
        Column("killerMatchPerkID", Integer, primary_key=True),
        Column("killerPerkID", Integer, ForeignKey("perks.perkID"), nullable=False),
        Column("killerMatchID", Integer, ForeignKey("killer_matches.matchID"), nullable=False)
    )
    killerMatchPerkID: int = field(init=False,compare=False,hash=False)
    killerPerkID: int = field(init=False,compare=False,hash=False)
    perk: Perk
    killerMatchID: int = field(init=False,compare=False,hash=False)

    __mapper_args__ = {
        "properties": {
            "perk": relationship("Perk",uselist=False, lazy='subquery')
        }
    }

    def __str__(self):
        return str(self.perk)

@mapperRegistry.mapped
@dataclass
class SurvivorMatchPerk:
    __table__ = Table(
        "survivor_match_perks",
        mapperRegistry.metadata,
        Column("survivorMatchPerkID", Integer, primary_key=True),
        Column("survivorPerkID", Integer, ForeignKey("perks.perkID"), nullable=False),
        Column("survivorMatchID", Integer, ForeignKey("survivor_matches.matchID"), nullable=False)
    )
    survivorMatchPerkID: int = field(init=False,compare=False,hash=False)
    survivorPerkID: int = field(init=False,compare=False,hash=False)
    perk: Perk
    survivorMatchID: int = field(init=False,compare=False,hash=False)

    __mapper_args__ = {
        "properties": {
            "perk": relationship("Perk",uselist=False, lazy='subquery')
        }
    }

    def __str__(self):
        return str(self.perk)

@mapperRegistry.mapped
@dataclass
class MatchKillerAddon:
    __table__ = Table(
        "match_killer_addons",
        mapperRegistry.metadata,
        Column("matchKillerAddonID", Integer, primary_key=True),
        Column("killerAddonID", Integer, ForeignKey("killer_addons.addonID"), nullable=False),
        Column("killerMatchID", Integer, ForeignKey("killer_matches.matchID"), nullable=False)
    )
    matchKillerAddonID: int = field(init=False,compare=False,hash=False)
    killerAddon: KillerAddon
    killerAddonID: int = field(init=False,compare=False,hash=False)
    killerMatchID: int = field(init=False,compare=False,hash=False)

    __mapper_args__ = {
        "properties": {
            "killerAddon": relationship("KillerAddon", uselist=False, backref="killer_addons", lazy='subquery')
        }
    }

    def __str__(self):
        return str(self.killerAddon)

@mapperRegistry.mapped
@dataclass
class MatchItemAddon:
    __table__ = Table(
        "match_item_addons",
        mapperRegistry.metadata,
        Column("matchItemAddonID", Integer, primary_key=True),
        Column("itemAddonID", Integer, ForeignKey("item_addons.addonID"), nullable=False),
        Column("survivorMatchID", Integer, ForeignKey("survivor_matches.matchID"),nullable=False)
    )
    matchItemAddonID: int = field(init=False,compare=False,hash=False)
    itemAddon: ItemAddon
    itemAddonID: int = field(init=False,compare=False,hash=False)
    survivorMatchID: int = field(init=False,compare=False,hash=False)

    __mapper_args__ = {
        "properties": {
            "itemAddon": relationship("ItemAddon",uselist=False,backref="item_addons", lazy='subquery')
        }
    }

    def __str__(self):
        return str(self.itemAddon)

@mapperRegistry.mapped
@dataclass
class FacedSurvivor:
    __table__ = Table(
        "faced_survivors",
        mapperRegistry.metadata,
        Column("facedSurvivorID", Integer, primary_key=True),
        Column("state", Enum(FacedSurvivorState), nullable=False),
        Column("killerMatchID", Integer, ForeignKey("killer_matches.matchID"), nullable=False),
        Column("survivorID", Integer, ForeignKey("survivors.survivorID"), nullable=False)
    )
    facedSurvivorID: int = field(init=False,compare=False,hash=False)
    survivorID: int = field(init=False,compare=False,hash=False)
    facedSurvivor: Survivor
    killerMatchID: int = field(init=False,compare=False,hash=False)
    state: FacedSurvivorState

    __mapper_args__ = {
        "properties": {
            "facedSurvivor": relationship("Survivor",uselist=False, lazy='subquery')
        }
    }

    def __str__(self):
        return f'{self.facedSurvivor} - {" ".join(x.lower() for x in splitUpper(self.state.name)).capitalize()}'


@dataclass
class DBDMatch(ABC):
    matchID: int = field(init=False,compare=False,hash=False)
    points: int
    gameMap: Optional[GameMap]
    gameMapID: int = field(init=False,compare=False,hash=False)
    offering: Optional[Offering]
    offeringID: int = field(init=False,compare=False,hash=False)
    matchDate: date
    rank: int


@mapperRegistry.mapped
@dataclass
class SurvivorMatch(DBDMatch):
    __table__ = Table(
        "survivor_matches",
        mapperRegistry.metadata,
        Column("matchID", Integer, primary_key=True),
        Column("survivorID", Integer, ForeignKey("survivors.survivorID"), nullable=False),
        Column("points", Integer, default=0),
        Column("matchDate", Date, nullable=False),
        Column("rank", Integer, default=20, nullable=True),
        Column("offeringID", Integer, ForeignKey("offerings.offeringID"), nullable=True),
        Column("gameMapID", Integer, ForeignKey("maps.mapID"), nullable=True),
        Column("facedKillerID", Integer, ForeignKey("killers.killerID"), nullable=False),
        Column("itemID", Integer, ForeignKey("items.itemID"), nullable=True),
        Column("matchResult", Enum(SurvivorMatchResult), nullable=False),
        Column("partySize", Integer, nullable=True, default=1)
    )
    survivor: Survivor
    survivorID: int = field(init=False,compare=False,hash=False)
    facedKiller: Killer
    facedKillerID: int = field(init=False,compare=False,hash=False)
    item: Optional[Item]
    itemID: int = field(init=False,compare=False,hash=False)
    matchResult: SurvivorMatchResult
    partySize: int
    perks: list[SurvivorMatchPerk] = field(default_factory=list)
    itemAddons: list[MatchItemAddon] = field(default_factory=list)

    __mapper_args__ = {
        "properties": {
            "facedKiller": relationship("Killer",uselist=False, lazy='subquery'),
            "item": relationship("Item",uselist=False, lazy='subquery'),
            "perks": relationship("SurvivorMatchPerk", lazy='subquery'),
            "offering": relationship("Offering",uselist=False, lazy='subquery'),
            "gameMap": relationship("GameMap",uselist=False, lazy='subquery'),
            "itemAddons": relationship("MatchItemAddon", lazy='subquery'),
            "survivor": relationship("Survivor", uselist=False, lazy='subquery')
        }
    }


@mapperRegistry.mapped
@dataclass
class KillerMatch(DBDMatch):
    __table__ = Table(
        "killer_matches",
        mapperRegistry.metadata,
        Column("matchID", Integer, primary_key=True),
        Column("killerID", Integer, ForeignKey("killers.killerID"), nullable=False),
        Column("points", Integer, default=0),
        Column("matchDate", Date, nullable=False),
        Column("rank", Integer, nullable=True, default=20),
        Column("offeringID", Integer, ForeignKey("offerings.offeringID"), nullable=True),
        Column("gameMapID", Integer, ForeignKey("maps.mapID"), nullable=True)
    )
    killer: Killer
    killerID: int = field(init=False,compare=False,hash=False)
    facedSurvivors: list[FacedSurvivor] = field(default_factory=list)
    perks: list[KillerMatchPerk] = field(default_factory=list)
    killerAddons: list[MatchKillerAddon] = field(default_factory=list)

    @property
    def disconnects(self) -> int:
        return self.__countOf(lambda surv: surv.state == FacedSurvivorState.Disconnected)

    @property
    def sacrifices(self) -> int:
        return self.__countOf(lambda surv: surv.state == FacedSurvivorState.Sacrificed)

    @property
    def kills(self) -> int:
        return self.__countOf(lambda surv: surv.state == FacedSurvivorState.Killed)

    def __countOf(self, filterFunc: Callable[[FacedSurvivor], int]):
        return sum(1 if filterFunc(survivor) else 0 for survivor in self.facedSurvivors)

    def __str__(self):
        with StringIO('') as builder:
            builder.write(self.matchDate.strftime('%d/%m/%Y'))
            builder.writelines((f"Killer: {self.killer.killerAlias}\n", f"Game points: {self.points:,}\n"))
            builder.write(f'Game map: {self.gameMap if self.gameMap is not None else "???"}\n')
            builder.write(f'Match offering: {self.offering if self.offering is not None else "???"}\n')
            builder.write(f"Played at rank: {self.rank}\n")
            if len(self.perks) > 0:
                builder.write("Used perks:\n")
                builder.writelines(f'- {perk}\n' for perk in self.perks)

            builder.write(f"User add-ons: {', '.join(map(str, self.killerAddons))}\n" if len(self.killerAddons) > 0 else "No add-ons used in this match\n")
            if len(self.facedSurvivors) > 0:
                builder.write("Faced survivors: \n")
                builder.writelines(f'\t{fs}\n' for fs in self.facedSurvivors)
            else:
                builder.write("No data about faced survivors\n")

            return builder.getvalue()

    __mapper_args__ = {
        "properties": {
            "facedSurvivors": relationship("FacedSurvivor", lazy='subquery'),
            "offering": relationship("Offering",uselist=False, lazy='subquery'),
            "gameMap": relationship("GameMap",uselist=False, lazy='subquery'),
            "perks": relationship("KillerMatchPerk", lazy='subquery'),
            "killerAddons": relationship("MatchKillerAddon", lazy='subquery'),
            "killer": relationship("Killer", uselist=False, lazy='subquery')
        }
    }
