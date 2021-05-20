from typing import Union, Callable

from models import Killer, Survivor, KillerAddon, Item, ItemAddon, Offering, Realm, Perk, KillerMatch, SurvivorMatch, \
    DBDMatch


class DBDMatchParser(object):

    def __init__(self, killers: list[Killer], survivors: list[Survivor], addons: list[Union[KillerAddon,ItemAddon]], items: list[Item], offerings: list[Offering], realms: list[Realm], perks: list[Perk]):
        self._killers = killers
        self._survivors = survivors
        self._addons = addons
        self._items = items
        self._offerings = offerings
        self._realms = realms
        self._perks = perks

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
        firstCommaIndex = s.index(',')
        killerName = s[:firstCommaIndex]
        killer = next(k for k in self._killers if killerName in k.killerAlias)
        elimsDict = {'kill':0,'mori':0,'disconnect':0}
        perkParseStartIndex = s.index('(', firstCommaIndex)
        eliminationsInfo = s[firstCommaIndex+1:perkParseStartIndex]
        print(eliminationsInfo)
        return KillerMatch()


    def __parseSurvivorGame(self, s: str) -> SurvivorMatch:
        pass