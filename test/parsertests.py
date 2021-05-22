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
            cls.killers = list(map(extractor, s.execute(
                sqlalchemy.select(Killer)).all()))  # for some ungodly reason this returns list of 1-element tuples
            cls.realms = list(map(extractor, s.execute(sqlalchemy.select(Realm)).all()))
            cls.survivors = list(map(extractor, s.execute(sqlalchemy.select(Survivor)).all()))
            killerAddons = list(map(extractor, s.execute(sqlalchemy.select(KillerAddon)).all()))
            itemAddons = list(map(extractor, s.execute(sqlalchemy.select(ItemAddon)).all()))
            cls.addons = killerAddons + itemAddons
            cls.offerings = list(map(extractor, s.execute(sqlalchemy.select(Offering)).all()))
            cls.perks = list(map(extractor, s.execute(sqlalchemy.select(Perk)).all()))
            cls.items = list(map(extractor, s.execute(sqlalchemy.select(Item)).all()))
        cls.parser = DBDMatchParser(cls.killers, cls.survivors, cls.addons, cls.items, cls.offerings, cls.realms, cls.perks)

    def test_parseKillerGame_everythingCorrect(self):
        testString = "Hillbilly, 2 kills, (tinkerer I, enduring III, lightborn III), 23196 points, " \
                     "add ons: apex muffler, map: rancid abattoir, offering: black ward, " \
                     "survivors: [Jeff, Yui: sacrificed, David: sacrificed, Meg], rank: 6"
        self.parser.setMatchDate(date(2021, 5, 21))
        resultMatch = self.parser.parse(testString)
        killer = next(k for k in self.killers if k.killerAlias == 'The Hillbilly')
        perks = [Perk(perkType=PerkType.Killer,perkName='Tinkerer',perkTier=1), Perk(perkType=PerkType.Killer,perkName='Enduring',perkTier=3), Perk(perkType=PerkType.Killer, perkName='Lightborn', perkTier=3)]
        addons = [KillerAddon(killer=killer,addonName='Apex Muffler')]
        survivorNames = ['Jeffrey "Jeff" Johansen','Yui Kimura','David King','Meg Thomas']
        states = [FacedSurvivorState.Escaped, FacedSurvivorState.Sacrificed, FacedSurvivorState.Sacrificed, FacedSurvivorState.Escaped]
        facedSurvivors = [FacedSurvivor(state=state,facedSurvivor=Survivor(survivorName=name)) for name,state in zip(survivorNames,states)]
        expectedMatch = KillerMatch(killer=killer, rank=6, points=23196, matchDate=date(2021,5,21),
                           gameMap=GameMap(mapName='Rancid Abattoir'), offering=Offering(offeringName='Black Ward'),
                           killerAddons=[MatchKillerAddon(killerAddon=addon) for addon in addons],
                           perks=[KillerMatchPerk(perk=perk) for perk in perks],
                           facedSurvivors=facedSurvivors)
        self.assertEqual(resultMatch,expectedMatch)

    def test_parseKillerGame_4Sacrifices_checkFacedSurvivors(self):
        testString = "Hillbilly, 2 kills, (tinkerer I, enduring III, lightborn III), 23196 points, " \
                     "add ons: apex muffler, iridescent brick, map: rancid abattoir, offering: black ward, " \
                     "survivors: [Jeff, Yui: sacrificed, David: sacrificed, Meg], rank: 6"

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
        matchDate = date(2021,5,21)
        self.parser.setMatchDate(matchDate)
        survivor = next(s for s in self.survivors if s.survivorName == 'William "Bill" Overbeck')
        perks = [
            Perk(perkName="We're Gonna Live Forever",perkType=PerkType.Survivor,perkTier=3),
            Perk(perkName='Dead Hard',perkType=PerkType.Survivor,perkTier=1),
            Perk(perkName='Unbreakable',perkType=PerkType.Survivor,perkTier=3),
            Perk(perkName='Borrowed Time',perkType=PerkType.Survivor,perkTier=3)
        ]
        item = Item(itemType=ItemType.Toolbox,itemName='Commodious Toolbox')
        addons = [ItemAddon(addonName='Wire Spool',itemType=ItemType.Toolbox), ItemAddon(addonName='Scraps',itemType=ItemType.Toolbox)]
        facedKiller = next(k for k in self.killers if k.killerAlias == 'The Legion')
        expectedMatch = SurvivorMatch(matchResult=SurvivorMatchResult.Sacrificed, points=20100, partySize=1, offering=Offering(offeringName='White Ward'),
                                      gameMap=GameMap(mapName="Wreckers' Yard"), perks=[SurvivorMatchPerk(perk=perk) for perk in perks],
                                      matchDate=matchDate,facedKiller=facedKiller,itemAddons=[MatchItemAddon(itemAddon=addon) for addon in addons],item=item,
                                      survivor=survivor,rank=10)
        resultMatch = self.parser.parse(testString)
        self.assertEqual(resultMatch,expectedMatch)
