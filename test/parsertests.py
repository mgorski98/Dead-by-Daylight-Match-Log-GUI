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
        testString = "Hillbilly, 4 kills, (tinkerer I, enduring III, lightborn III), 23196 points, " \
                     "add ons: apex muffler, iridescent brick, map: rancid abattoir, offering: black ward, " \
                     "survivors: [Jeff, Yui, David, Meg], rank: 6"
        matchDate = date(2020, 3,20)
        self.parser.setMatchDate(matchDate)
        resultMatch = self.parser.parse(testString)
        self.assertTrue(all(s.state == FacedSurvivorState.Sacrificed for s in resultMatch.facedSurvivors))

    def test_parseKillerGame_4Moris_checkFacedSurvivors(self):
        testString = "Hillbilly, 0 kills, 4 moris, (tinkerer I, enduring III, lightborn III), 23196 points, " \
                     "add ons: apex muffler, iridescent brick, map: rancid abattoir, offering: black ward, " \
                     "survivors: [Jeff, Yui, David, Meg], rank: 6"
        matchDate = date(2020, 3, 20)
        self.parser.setMatchDate(matchDate)
        resultMatch = self.parser.parse(testString)
        self.assertTrue(all(s.state == FacedSurvivorState.Killed for s in resultMatch.facedSurvivors))

    def test_parseKillerGame_4Dcs_checkFacedSurvivors(self):
        testString = "Hillbilly, 0 kills, 4 disconnects, (tinkerer I, enduring III, lightborn III), 23196 points, " \
                     "add ons: apex muffler, iridescent brick, map: rancid abattoir, offering: black ward, " \
                     "survivors: [Jeff, Yui, David, Meg], rank: 6"
        matchDate = date(2020, 3, 20)
        self.parser.setMatchDate(matchDate)
        resultMatch = self.parser.parse(testString)
        self.assertTrue(all(s.state == FacedSurvivorState.Disconnected for s in resultMatch.facedSurvivors))

    def test_parseKillerGame_4Escapes_checkFacedSurvivors(self):
        testString = "Hillbilly, 0 kills, (tinkerer I, enduring III, lightborn III), 23196 points, " \
                     "add ons: apex muffler, iridescent brick, map: rancid abattoir, offering: black ward, " \
                     "survivors: [Jeff, Yui, David, Meg], rank: 6"
        matchDate = date(2020, 3, 20)
        self.parser.setMatchDate(matchDate)
        resultMatch = self.parser.parse(testString)
        self.assertTrue(all(s.state == FacedSurvivorState.Escaped for s in resultMatch.facedSurvivors))

    def test_parseKillerGame_checkIfSurvivorStatesCorrect(self):
        testString = "Hillbilly, 1 kill, 2 moris, 1 disconnect (tinkerer I, enduring III, lightborn III), 23196 points, " \
                     "add ons: apex muffler, iridescent brick, map: rancid abattoir, offering: black ward, " \
                     "survivors: [Jeff: sacrificed, Yui: killed, David: killed, Meg: disconnected], rank: 6"
        matchDate = date(2020, 3, 20)
        self.parser.setMatchDate(matchDate)
        resultMatch = self.parser.parse(testString)
        expectedStates = [FacedSurvivorState.Sacrificed, FacedSurvivorState.Killed, FacedSurvivorState.Killed, FacedSurvivorState.Disconnected]
        resultStates = [s.state for s in resultMatch.facedSurvivors]
        self.assertEqual(expectedStates, resultStates)

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

    def test_parseSurvivorGame_ifNoItemAndAddons(self):
        testString = "Bill, sacrificed, (we're gonna live forever III, dead hard I, unbreakable III, " \
                     "borrowed time III), 20100 points, item: none, add ons: none (against legion), " \
                     "map: wreckers' yard, offering: white ward, rank: 10, party size: 1"
        matchDate = date(2020, 3, 20)
        self.parser.setMatchDate(matchDate)
        resultMatch = self.parser.parse(testString)
        survivor = next(s for s in self.survivors if s.survivorName == 'William "Bill" Overbeck')
        facedKiller = next(k for k in self.killers if k.killerAlias == 'The Legion')
        perks = [
            Perk(perkName="We're Gonna Live Forever", perkType=PerkType.Survivor, perkTier=3),
            Perk(perkName='Dead Hard', perkType=PerkType.Survivor, perkTier=1),
            Perk(perkName='Unbreakable', perkType=PerkType.Survivor, perkTier=3),
            Perk(perkName='Borrowed Time', perkType=PerkType.Survivor, perkTier=3)
        ]
        expectedMatch = SurvivorMatch(rank=10,partySize=1,offering=Offering(offeringName='White Ward'),gameMap=GameMap(mapName="Wreckers' Yard"),
                                      points=20100, matchDate=matchDate,itemAddons=[],item=None,
                                      survivor=survivor,perks=[SurvivorMatchPerk(perk=perk) for perk in perks],
                                      facedKiller=facedKiller,matchResult=SurvivorMatchResult.Sacrificed)
        self.assertEqual(resultMatch, expectedMatch)

    def test_parseGame_failWhen_moreThan4Perks(self):
        testString = "Bill, sacrificed, (we're gonna live forever III, dead hard I, unbreakable III, " \
                     "borrowed time III, sprint burst III), 20100 points, item: none, add ons: none (against legion), " \
                     "map: wreckers' yard, offering: white ward, rank: 10, party size: 1"
        matchDate = date(2020,3,20)
        self.parser.setMatchDate(matchDate)
        self.assertRaises(AssertionError, lambda: self.parser.parse(testString))

    def test_parseGame_failWhen_samePerkMoreThanOnce(self):
        testString = "Bill, sacrificed, (we're gonna live forever III, dead hard I, unbreakable III, " \
                     "unbreakable I), 20100 points, item: none, add ons: none (against legion), " \
                     "map: wreckers' yard, offering: white ward, rank: 10, party size: 1"
        matchDate = date(2020, 3, 20)
        self.parser.setMatchDate(matchDate)
        self.assertRaises(AssertionError, lambda: self.parser.parse(testString))

    def test_parseGame_failWhen_sameAddonInBothSlots(self):
        testString = "Bill, sacrificed, (we're gonna live forever III, dead hard I, unbreakable III, " \
                     "unbreakable I), 20100 points, item: camping aid kit, add ons: bandages, bandages (against legion), " \
                     "map: wreckers' yard, offering: white ward, rank: 10, party size: 1"
        matchDate = date(2020, 3, 20)
        self.parser.setMatchDate(matchDate)
        self.assertRaises(AssertionError, lambda: self.parser.parse(testString))

    def test_parseGame_failWhen_addonsForWrongItemType(self):
        testString = "Bill, sacrificed, (we're gonna live forever III, dead hard I, unbreakable III, " \
                     "unbreakable I), 20100 points, item: camping aid kit, add ons: scraps, bandages (against legion), " \
                     "map: wreckers' yard, offering: white ward, rank: 10, party size: 1"
        matchDate = date(2020, 3, 20)
        self.parser.setMatchDate(matchDate)
        self.assertRaises(AssertionError, lambda: self.parser.parse(testString))

    def test_parseKillerGame_failWhen_moreThan4Eliminations(self):
        testString = "Hillbilly, 10 kills, 20 moris, (tinkerer I, enduring III, lightborn III), 23196 points, " \
                     "add ons: apex muffler, map: rancid abattoir, offering: black ward, " \
                     "survivors: [Jeff, Yui: sacrificed, David: sacrificed, Meg], rank: 6"
        self.parser.setMatchDate(date(2021, 5, 21))
        self.assertRaises(AssertionError, lambda: self.parser.parse(testString))

    def test_parseGame_failWhen_rankNotBetween1And20(self):
        testString = "Bill, sacrificed, (we're gonna live forever III, dead hard I, unbreakable III, " \
                     "borrowed time III), 20100 points, item: none, add ons: none (against legion), " \
                     "map: wreckers' yard, offering: white ward, rank: 50, party size: 1"
        self.parser.setMatchDate(date(2021, 5, 21))
        self.assertRaises(AssertionError, lambda: self.parser.parse(testString))

    #todo: make tests for when there is no map, rank, party size etc. information