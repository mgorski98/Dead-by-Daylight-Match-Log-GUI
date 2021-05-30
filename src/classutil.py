import dataclasses
import re
from datetime import date, datetime
from typing import Union, Callable, Optional

from PyQt5.QtCore import QRunnable, QObject, pyqtSignal

from database import Database
from globaldata import Globals
from models import Killer, Survivor, KillerAddon, Item, ItemAddon, Offering, Realm, Perk, KillerMatch, SurvivorMatch, \
    DBDMatch, KillerMatchPerk, FacedSurvivorState, FacedSurvivor, MatchKillerAddon, MatchItemAddon, SurvivorMatchResult, \
    SurvivorMatchPerk, GameMap
from util import isDateString, levenshteinDistance
from dataclasses import dataclass

@dataclass(frozen=True)
class DBDResources(object):
    killers: list[Killer]
    survivors: list[Survivor]
    addons: list[Union[KillerAddon, ItemAddon]]
    items: list[Item]
    offerings: list[Offering]
    realms: list[Realm]
    perks: list[Perk]


class DBDMatchParser(object):

    def __init__(self, resources: DBDResources):
        self._resources = resources
        self._matchDate = None

    def setMatchDate(self, d: date):
        self._matchDate = d

    def parse(self, s: str) -> DBDMatch:
        firstCommaIndex = s.index(',')
        if firstCommaIndex == -1:
            raise ValueError("No commas found in match entry. Corrupted entry")
        charName = s[:firstCommaIndex].strip()
        handler = self.__determineMatchType(charName)
        if handler is None:
            raise ValueError(f"No character named {charName} found.")
        return handler(s)

    def __determineMatchType(self, charName: str) -> Callable[[str], DBDMatch]:
        return self.__parseKillerGame if any(charName in k.killerAlias for k in self._resources.killers) else self.__parseSurvivorGame if any(charName in _s.survivorName for _s in self._resources.survivors) else None

    def __parseKillerGame(self, s: str) -> KillerMatch:
        #parsing killer
        firstCommaIndex = s.index(',')
        killerName = s[:firstCommaIndex]
        killer = next(k for k in self._resources.killers if killerName in k.killerAlias)

        #parsing eliminations
        elimsDict = {'kill':0,'mori':0,'disconnect':0}
        perkParseStartIndex = s.index('(', firstCommaIndex)
        eliminationsInfo = s[firstCommaIndex+1:perkParseStartIndex]
        if not 'kill' in eliminationsInfo:
            raise ValueError(f"No kills specified in string")
        eliminationsInfoStrings = list(filter(lambda _s: _s.strip(), eliminationsInfo.split(',')))
        for elimString in eliminationsInfoStrings:
            for key in elimsDict.keys():
                if key in elimString:
                    tokens = elimString.strip().split(" ")
                    elimsDict[key] += int(tokens[0])
                    break

        assert sum(elimsDict.values()) in range(0,5), "Cannot be more than 4 eliminations"

        #parsing perks
        perks = self.__parsePerks(s)

        #parsing points
        points = self.__parsePoints(s)


        addons = self.__parseAddonsInfo(s)
        gameMap = self.__parseMap(s)
        offering = self.__parseOffering(s)

        #parsing faced survivors info
        facedSurvivorsMatch = re.search(r'survivors: \[(.*)\]', s)
        facedSurvivors = []
        if facedSurvivorsMatch:
            facedSurvivorsString = facedSurvivorsMatch.group(1)
            facedSurvivorsStrings = facedSurvivorsString.split(',')
            #if there's 4 of any elimination method and no states specified then we assume all of them were eliminated that way
            #same with escapes, if there's 0 of each method then all of them escaped
            survivors = [next(_s for _s in self._resources.survivors if (fss[:fss.index(':')].strip() if ':' in fss else fss.strip()) in _s.survivorName) for fss in facedSurvivorsStrings]
            survivorStates = []
            MAX_ELIMS = 4
            MAX_ELIMS_RANGE = range(MAX_ELIMS)
            if elimsDict['kill'] == MAX_ELIMS: #all of them sacrificed
                survivorStates = [FacedSurvivorState.Sacrificed for _ in MAX_ELIMS_RANGE]
            elif elimsDict['mori'] == MAX_ELIMS: #all of them were mori'd
                survivorStates = [FacedSurvivorState.Killed for _ in MAX_ELIMS_RANGE]
            elif elimsDict['disconnect'] == MAX_ELIMS: #all of them disconnected
                survivorStates = [FacedSurvivorState.Disconnected for _ in MAX_ELIMS_RANGE]
            elif all(v == 0 for v in elimsDict.values()): #everyone escaped
                survivorStates = [FacedSurvivorState.Escaped for _ in MAX_ELIMS_RANGE]
            else: #parse it normally
                for fss in facedSurvivorsStrings:
                    fss = fss.strip()
                    state = FacedSurvivorState.Escaped
                    parts = fss.split(':')
                    if len(parts) > 1:
                        statePart = parts[1].strip()
                        state = FacedSurvivorState[''.join(e.capitalize() for e in statePart.split(' '))]
                    survivorStates.append(state)
            facedSurvivors = [FacedSurvivor(state=state, facedSurvivor=survivor) for state,survivor in zip(survivorStates, survivors)]

        rank = self.__parseRank(s)

        return KillerMatch(killer=killer, rank=rank, points=points, matchDate=self._matchDate,
                           gameMap=gameMap, offering=offering, killerAddons=addons, perks=[KillerMatchPerk(perk=perk) for perk in perks],
                           facedSurvivors=facedSurvivors)



    def __parseSurvivorGame(self, s: str) -> SurvivorMatch:
        firstCommaIndex = s.index(',')
        survivorName = s[:firstCommaIndex]
        survivor = next(_s for _s in self._resources.survivors if survivorName in _s.survivorName)

        perks = self.__parsePerks(s)

        # parsing points
        points = self.__parsePoints(s)

        #parsing item info
        itemName = re.search(r'item: (.*?),', s).group(1).strip()
        item = next((i for i in self._resources.items if i.itemName.lower() == itemName), None)
        # parsing add ons info
        addons = [] if item is None else self.__parseAddonsInfo(s)
        assert len(addons) in range(0,3), "There cannot be more than 2 add-ons"
        assert len(addons) == len(set(map(str, addons))), "There cannot be 2 of the same add-on"
        # parsing map info
        gameMap = self.__parseMap(s)

        # parsing offering info
        offering = self.__parseOffering(s)
        perkParseStartIndex = s.index('(')
        #parsing match result
        matchResultStr = s[firstCommaIndex+1:perkParseStartIndex].replace(',','').strip()
        matchResult = SurvivorMatchResult[''.join(e.capitalize() for e in matchResultStr.split(' '))]

        #parsing faced killer
        facedKillerName = re.search(r'\(\s*against (.*)\)',s).group(1)
        facedKiller = next(k for k in self._resources.killers if facedKillerName in k.killerAlias.lower())
        #parsing rank
        rank = self.__parseRank(s)

        #parsing party size
        partySize=1
        partySizeMatch = re.search(r"party size: ([1-4])",s)
        if partySizeMatch:
            partySize = int(partySizeMatch.group(1))

        return SurvivorMatch(survivor=survivor,perks=[SurvivorMatchPerk(perk=perk) for perk in perks], item=item,
                             itemAddons=addons, facedKiller=facedKiller, rank=rank, partySize=partySize,
                             matchResult=matchResult,offering=offering,gameMap=gameMap,points=points,matchDate=self._matchDate)

    def __parsePerks(self, s: str) -> list[Perk]:
        perkParseStartIndex = s.index('(')
        perkParseEndIndex = s.index(')', perkParseStartIndex)
        perksStr = s[perkParseStartIndex + 1:perkParseEndIndex].strip()
        perks = []
        if perksStr:
            perkStrings = perksStr.split(',')
            for perkStr in perkStrings:
                perkStr = perkStr.strip()
                nameParts = perkStr.split(" ")
                perkName = ' '.join(nameParts[:-1])
                tier = len(nameParts[-1])
                perk = next(
                    (p for p in self._resources.perks if p.perkName.lower() == perkName.lower() and tier == p.perkTier),
                    None)
                assert perk is not None, f"Unknown perk: {perkName} {tier}"
                perks.append(perk)
        assert len(perks) in range(0, 5), "There cannot be more than 4 perks"
        assert len(perks) == len(set(map(lambda p: p.perkName, perks))), "There cannot be duplicate perks!"
        return perks

    def __parseAddonsInfo(self, s: str) -> Union[list[MatchItemAddon], list[MatchKillerAddon]]:
        addons = []
        match = re.search(r'add ons: (.*)(?=\()', s)
        if not match:  # means its a killer string
            addonsIndex = s.index('add ons:')
            mapIndex = s.find('map:')
            if mapIndex == -1: #means its at the end of the string
                addonsStr = s[addonsIndex+len('add ons:'):].strip()
            else:
                addonsStr = s[addonsIndex + len('add ons:'):mapIndex].rstrip(',').strip()
            if addonsStr != 'none':
                addonNames = [e.strip() for e in addonsStr.split(',') if e]
                addons = [MatchKillerAddon(killerAddon=next(addon for addon in self._resources.addons if addon.addonName.lower() == a.strip().lower())) if a != 'zori' else MatchKillerAddon(killerAddon=next(addon for addon in self._resources.addons if addon.addonName == 'Zōri')) for a in addonNames]
        else:
            addonsStr = match.group(1).rstrip(',').strip()
            if addonsStr != 'none':
                addonNames = addonsStr.split(',')
                addons = [MatchItemAddon(itemAddon=next(addon for addon in self._resources.addons if addon.addonName.lower() == a.strip().lower())) for a in addonNames]
        return addons

    def __parsePoints(self, s: str) -> int:
        match = re.search('(\d+) points', s)
        return int(match.group(1)) if match else 0

    def __parseOffering(self, s: str) -> Optional[Offering]:
        offeringMatch = re.search(r'offering: (.*?),', s)
        offering = None
        if offeringMatch:
            offeringName = offeringMatch.group(1).strip().lower()
            offering = None if offeringName == 'none' else next(
                o for o in self._resources.offerings if o.offeringName.lower() == offeringName)
        return offering

    def __parseRank(self, s:str) -> Optional[int]:
        rank = None
        rankMatch = re.search(r'rank: (\d{1,2})', s)
        if rankMatch:
            rank = int(rankMatch.group(1))
            assert rank in range(Globals.HIGHEST_RANK,
                                 Globals.LOWEST_RANK + 1), "Rank can only be equal to numbers from range 1 to 20"
        return rank

    def __parseMap(self,s:str) -> Optional[GameMap]:
        gameMapIndex = s.find('map:')
        gameMap = None
        if gameMapIndex != -1:
            commaIndex = s.find(',', gameMapIndex)
            mapName = s[gameMapIndex + len("map:"):commaIndex].strip().lower()
            for r in self._resources.realms:
                gameMap = next((m for m in r.maps if m.mapName.lower() == mapName), None)
                if gameMap is not None:
                    break
        return gameMap


class DBDMatchLogFileLoader(object):

    def __init__(self, parser: DBDMatchParser, encoding: str ='utf-8'):
        self.parser = parser
        self.encoding = encoding
        self.errors = []

    def load(self, path: str) -> list[DBDMatch]:
        self.errors = []
        with open(path, mode='r', encoding=self.encoding) as f:
            games = []
            currentDate = None
            parseGames = False
            currentLine = 0
            for line in f:
                currentLine+=1
                line = line.strip()
                if not line:
                    continue
                if isDateString(line, '%d %m %Y'):
                    currentDate = datetime.strptime(line, '%d %m %Y')
                    self.parser.setMatchDate(currentDate)
                    parseGames=True
                    continue
                elif parseGames:
                    try:
                        game = self.parser.parse(line)
                        games.append(game)
                    except ValueError:#empty
                        parseGames=False
                        currentDate=None
                    except AssertionError as e:
                        self.errors.append(f'Error at line {currentLine} in file {path}: {e}')

        return games


class LogFileLoadWorkerSignals(QObject):
    finished = pyqtSignal(object, object) #lets you pass loaded games and errors occurred during loading
    fileLoadStarted = pyqtSignal(str) #emits the file path


class LogFileLoadWorker(QRunnable):


    def __init__(self, loader: DBDMatchLogFileLoader, paths: list[str]):
        super(LogFileLoadWorker, self).__init__()
        self.signals = LogFileLoadWorkerSignals()
        self.filePaths = paths
        self.loader = loader

    def run(self) -> None:
        allGames, allErrors = [], []
        for file in self.filePaths:
            self.signals.fileLoadStarted.emit(file)
            games = self.loader.load(file)
            errors = self.loader.errors
            allGames += games
            allErrors += errors
        self.signals.finished.emit(allGames, allErrors)

class DatabaseMatchListWorkerSignals(QObject):
    finished = pyqtSignal()

class DatabaseMatchListSaveWorker(QRunnable):

    def __init__(self, matchesToSave: list[DBDMatch]):
        super().__init__()
        self.matches = matchesToSave
        self.signals = DatabaseMatchListWorkerSignals()

    def run(self) -> None:
        with Database.instance().getNewSession() as s:
            s.add_all(self.matches)
            s.commit()
            self.signals.finished.emit()