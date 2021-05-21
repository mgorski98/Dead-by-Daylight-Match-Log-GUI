import unittest
import operator

import sqlalchemy

from classutil import DBDMatchParser
from database import Database
from models import *


class TestDBDMatchParser(unittest.TestCase):

    @classmethod
    def setUpClass(cls) -> None:
        Database.init('sqlite:///../dbd-match-log-DEV.db')
        with Database.instance().getNewSession() as s:
            extractor = operator.itemgetter(0)
            killers = list(map(extractor, s.execute(
                sqlalchemy.select(Killer)).all()))  # for some ungodly reason this returns list of 1-element tuples
            realms = list(map(extractor, s.execute(sqlalchemy.select(Realm)).all()))
            survivors = list(map(extractor, s.execute(sqlalchemy.select(Survivor)).all()))
            killerAddons = list(map(extractor, s.execute(sqlalchemy.select(KillerAddon)).all()))
            itemAddons = list(map(extractor, s.execute(sqlalchemy.select(ItemAddon)).all()))
            addons = killerAddons + itemAddons
            offerings = list(map(extractor, s.execute(sqlalchemy.select(Offering)).all()))
            killerPerks = list(
                map(extractor, s.execute(sqlalchemy.select(Perk).where(Perk.perkType == PerkType.Killer)).all()))
            survivorPerks = list(
                map(extractor, s.execute(sqlalchemy.select(Perk).where(Perk.perkType == PerkType.Survivor)).all()))
            items = list(map(extractor, s.execute(sqlalchemy.select(Item)).all()))
        cls.parser = DBDMatchParser(killers, survivors, addons, items, offerings, realms, survivorPerks + killerPerks)

    def test_parseKillerGame_everythingCorrect(self):
        testString = "Hillbilly, 2 kills, (tinkerer I, enduring III, lightborn III), 23196 points, " \
                     "add ons: apex muffler, iridescent brick, map: rancid abattoir, offering: black ward, " \
                     "survivors: [Jeff, Yui: sacrificed, David: sacrificed, Meg], rank: 6"
        self.parser.setMatchDate(date(2021, 5, 21))
        resultMatch = self.parser.parse(testString)

    def test_parseKillerGame_4Sacrifices_checkFacedSurvivors(self):
        testString = "Hillbilly, 2 kills, (tinkerer I, enduring III, lightborn III), 23196 points, " \
                     "add ons: apex muffler, iridescent brick, map: rancid abattoir, offering: black ward, " \
                     "survivors: [Jeff, Yui: sacrificed, David: sacrificed, Meg], rank: 6"
        pass

    def test_parseKillerGame_4Moris_checkFacedSurvivors(self):
        testString = "Hillbilly, 2 kills, (tinkerer I, enduring III, lightborn III), 23196 points, " \
                     "add ons: apex muffler, iridescent brick, map: rancid abattoir, offering: black ward, " \
                     "survivors: [Jeff, Yui: sacrificed, David: sacrificed, Meg], rank: 6"

    def test_parseKillerGame_4Dcs_checkFacedSurvivors(self):
        testString = "Hillbilly, 2 kills, (tinkerer I, enduring III, lightborn III), 23196 points, " \
                     "add ons: apex muffler, iridescent brick, map: rancid abattoir, offering: black ward, " \
                     "survivors: [Jeff, Yui: sacrificed, David: sacrificed, Meg], rank: 6"

    def test_parseKillerGame_4Escapes_checkFacedSurvivors(self):
        testString = "Hillbilly, 2 kills, (tinkerer I, enduring III, lightborn III), 23196 points, " \
                     "add ons: apex muffler, iridescent brick, map: rancid abattoir, offering: black ward, " \
                     "survivors: [Jeff, Yui: sacrificed, David: sacrificed, Meg], rank: 6"

    def test_parseSurvivorGame_everythingCorrect(self):
        testString = "Bill, sacrificed, (we're gonna live forever III, dead hard I, unbreakable III, " \
                     "borrowed time III), 20100 points, item: commodious toolbox, add ons: wire spool, " \
                     "scraps (against legion), map: wreckers' yard, offering: white ward, rank: 10, party size: 1"
        self.parser.setMatchDate(date(2021,5,21))
        resultMatch = self.parser.parse(testString)
