import re
from datetime import date
from typing import Union, Callable

from models import Killer, Survivor, KillerAddon, Item, ItemAddon, Offering, Realm, Perk, KillerMatch, SurvivorMatch, \
    DBDMatch, KillerMatchPerk, FacedSurvivorState, FacedSurvivor, MatchKillerAddon, MatchItemAddon, SurvivorMatchResult, \
    SurvivorMatchPerk


class DBDMatchParser(object):

    def __init__(self, killers: list[Killer], survivors: list[Survivor], addons: list[Union[KillerAddon,ItemAddon]], items: list[Item], offerings: list[Offering], realms: list[Realm], perks: list[Perk]):
        self._killers = killers
        self._survivors = survivors
        self._addons = addons
        self._items = items
        self._offerings = offerings
        self._realms = realms
        self._perks = perks
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
        return self.__parseKillerGame if any(charName in k.killerAlias for k in self._killers) else self.__parseSurvivorGame if any(charName in _s.survivorName for _s in self._survivors) else None

    def __parseKillerGame(self, s: str) -> KillerMatch:
        #parsing killer
        firstCommaIndex = s.index(',')
        killerName = s[:firstCommaIndex]
        killer = next(k for k in self._killers if killerName in k.killerAlias)

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
        perkParseEndIndex = s.index(')', perkParseStartIndex)
        perksStr = s[perkParseStartIndex+1:perkParseEndIndex].strip()
        perks = []
        if perksStr:
            perkStrings = perksStr.split(',')
            for perkStr in perkStrings:
                perkStr = perkStr.strip()
                nameParts = perkStr.split(" ")
                perkName = ' '.join(nameParts[:-1])
                tier = len(nameParts[-1])
                perks.append(next(p for p in self._perks if p.perkName.lower() == perkName.lower() and tier == p.perkTier))

        #parsing points
        points = self.__parsePoints(s)


        #parsing add ons info
        addons = self.__parseAddonsInfo(s)
        #parsing map info
        gameMapIndex = s.find('map:')
        gameMap = None
        if gameMapIndex != -1:
            commaIndex = s.find(',', gameMapIndex)
            mapName = s[gameMapIndex+len("map:"):commaIndex].strip().lower()
            for r in self._realms:
                gameMap = next((m for m in r.maps if m.mapName.lower() == mapName), None)
                if gameMap is not None:
                    break
        #parsing offering info
        offeringName = re.search(r'offering: (.*?),', s).group(1).strip().lower()
        offering = next(o for o in self._offerings if o.offeringName.lower() == offeringName)
        #parsing faced survivors info
        facedSurvivorsString = re.search(r'survivors: \[(.*)\]', s).group(1)
        facedSurvivorsStrings = facedSurvivorsString.split(',')
        #if there's 4 of any elimination method and no states specified then we assume all of them were eliminated that way
        #same with escapes, if there's 0 of each method then all of them escaped
        survivors = [next(_s for _s in self._survivors if (fss[:fss.index(':')].strip() if ':' in fss else fss.strip()) in _s.survivorName) for fss in facedSurvivorsStrings]
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
        #parsing rank info
        rank = int(re.search(r'rank: (\d{1,2})', s).group(1))
        return KillerMatch(killer=killer, rank=rank, points=points, matchDate=self._matchDate,
                           gameMap=gameMap, offering=offering, killerAddons=addons, perks=[KillerMatchPerk(perk=perk) for perk in perks],
                           facedSurvivors=facedSurvivors)



    def __parseSurvivorGame(self, s: str) -> SurvivorMatch:
        firstCommaIndex = s.index(',')
        survivorName = s[:firstCommaIndex]
        survivor = next(_s for _s in self._survivors if survivorName in _s.survivorName)

        perkParseStartIndex = s.index('(')
        # parsing perks
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
                perks.append(
                    next(p for p in self._perks if p.perkName.lower() == perkName.lower() and tier == p.perkTier))

        # parsing points
        points = self.__parsePoints(s)

        #parsing item info
        itemName = re.search(r'item: (.*?),', s).group(1).strip()
        item = next((i for i in self._items if i.itemName.lower() == itemName), None)
        # parsing add ons info
        addons = [] if item is None else self.__parseAddonsInfo(s)

        # parsing map info
        gameMapIndex = s.find('map:')
        gameMap = None
        if gameMapIndex != -1:
            commaIndex = s.find(',', gameMapIndex)
            mapName = s[gameMapIndex + len("map:"):commaIndex].strip().lower()
            for r in self._realms:
                gameMap = next((m for m in r.maps if m.mapName.lower() == mapName), None)
                if gameMap is not None:
                    break

        # parsing offering info
        offeringName = re.search(r'offering: (.*?),', s).group(1).strip().lower()
        offering = next(o for o in self._offerings if o.offeringName.lower() == offeringName)

        #parsing match result
        matchResultStr = s[firstCommaIndex+1:perkParseStartIndex].replace(',','').strip()
        matchResult = SurvivorMatchResult[''.join(e.capitalize() for e in matchResultStr.split(' '))]

        #parsing faced killer
        facedKillerName = re.search(r'\(against (.*)\)',s).group(1)
        facedKiller = next(k for k in self._killers if facedKillerName in k.killerAlias.lower())
        #parsing rank
        rank = int(re.search(r'rank: (\d{1,2})', s).group(1))

        #parsing party size
        partySize = int(re.search(r"party size: ([1-4])",s).group(1))

        return SurvivorMatch(survivor=survivor,perks=[SurvivorMatchPerk(perk=perk) for perk in perks], item=item,
                             itemAddons=addons, facedKiller=facedKiller, rank=rank, partySize=partySize,
                             matchResult=matchResult,offering=offering,gameMap=gameMap,points=points,matchDate=self._matchDate)

    def __parseAddonsInfo(self, s: str) -> list[Union[KillerAddon, ItemAddon]]:
        addons = []
        match = re.search(r'add ons: (.*)(?=\()', s)
        if not match:  # means its a killer string
            addonsIndex = s.index('add ons:')
            mapIndex = s.index('map:')
            addonsStr = s[addonsIndex + len('add ons:'):mapIndex].rstrip(',').strip()
            if addonsStr != 'none':
                addonNames = [e.strip() for e in addonsStr.split(',') if e]
                addons = [MatchKillerAddon(killerAddon=next(addon for addon in self._addons if addon.addonName.lower() == a)) for a in addonNames]
        else:
            addonsStr = match.group(1).rstrip(',').strip()
            if addonsStr != 'none':
                addonNames = addonsStr.split(',')
                addons = [MatchItemAddon(itemAddon=next(addon for addon in self._addons if addon.addonName.lower() == a.strip())) for a in addonNames]
        return addons

    def __parsePoints(self, s: str) -> int:
        try:
            return int(re.search('(\d+) points', s).group(1))
        except ValueError:
            return 0
