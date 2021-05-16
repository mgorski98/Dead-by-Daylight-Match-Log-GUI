from __future__ import annotations

import os
import time
from typing import Optional, Union

import requests
import sqlalchemy
from PIL import Image
from PyQt5.QtCore import QThread, pyqtSlot, pyqtSignal, QObject, QRunnable
from bs4 import BeautifulSoup
from sqlalchemy.orm import Session

from models import Killer, Survivor, Perk, PerkType, ItemType, Item, Offering, Realm, GameMap, KillerAddon, ItemAddon
from util import saveImageFromURL


class Database:
    __instance = None

    def __init__(self, url: str):
        self._engine = sqlalchemy.create_engine(url)

    def getNewSession(self) -> Session:
        return Session(self._engine)

    @staticmethod
    def instance() -> Database:
        return Database.__instance

    @staticmethod
    def init(dbUrl: str):
        if Database.__instance is None:
            Database.__instance = Database(dbUrl)

    @staticmethod
    def update():
        if Database.__instance is None:
            raise ValueError("Database is not initialized. Call Database.init() before invoking any of its methods")
        BASE_URL = 'https://deadbydaylight.fandom.com'
        BASE_WIKI_URL = 'https://deadbydaylight.fandom.com/wiki/'
        KILLERS_URL = f'{BASE_WIKI_URL}Killers'
        SURVIVORS_URL = f'{BASE_WIKI_URL}Survivors'
        ITEMS_URL = f'{BASE_WIKI_URL}Items'
        ADDONS_URL = f'{BASE_WIKI_URL}Add-ons'
        OFFERINGS_URL = f'{BASE_WIKI_URL}Offerings'
        REALM_URL = f'{BASE_WIKI_URL}Realms'
        PERKS_URL = f'{BASE_WIKI_URL}Perks'

        killersDoc = requests.get(KILLERS_URL).content
        killersParser = BeautifulSoup(killersDoc, 'html.parser')
        mainDiv = killersParser.find('div', attrs={'style': 'color: #fff;'})
        aTags = mainDiv.find_all('a')
        killers = [Killer(killerName=aTags[j].get('title', ''), killerAlias='The '+aTags[j + 1].get('title', '')) for i, j in enumerate(range(0, len(aTags), 2))]
        killerUrls = [f"{BASE_URL}{a.get('href', '')}" for a in aTags[::2]]
        for i, url in enumerate(killerUrls):
            killerPageParser = BeautifulSoup(requests.get(url).content, 'html.parser')
            infoTable = killerPageParser.find('table', attrs={"class": "infoboxtable"})
            imgTag = infoTable.find('img')
            imgUrl = imgTag.get('src', '')
            name = killers[i].killerAlias.lower().replace(' ', '-')
            dest = f'../images/killers/the-{name}.png'
            if not os.path.exists(dest):
                saveImageFromURL(imgUrl, dest)

        survivorsDoc = requests.get(SURVIVORS_URL).content
        survivorsParser = BeautifulSoup(survivorsDoc, 'html.parser')
        mainDiv = survivorsParser.find('div', attrs={'style': 'color: #fff;'})
        aTags = mainDiv.find_all('a')
        survivors = [Survivor(survivorName=a.get('title', '')) for i, a in enumerate(aTags[::2])]
        survivorUrls = [f"{BASE_URL}{a.get('href', '')}" for a in aTags[::2]]

        for i, url in enumerate(survivorUrls):
            survivorPageParser = BeautifulSoup(requests.get(url).content, 'html.parser')
            infoTable = survivorPageParser.find('table', attrs={"class": "infoboxtable"})
            imgTag = infoTable.find('img')
            imgUrl = imgTag.get('src', '')
            name = survivors[i].survivorName.lower().replace(' ', '-').replace('"', '')
            dest = f'../images/survivors/{name}.png'
            if not os.path.exists(dest):
                saveImageFromURL(imgUrl, dest)

        perksDoc = requests.get(PERKS_URL).content
        perksParser = BeautifulSoup(perksDoc, 'html.parser')
        tables = perksParser.find_all('table', attrs={'class': 'wikitable sortable'})
        killerTable, survivorTable = tables[1], tables[0]
        tempGifPath = '../temp/temp.gif'
        perks = []
        for perkRow in survivorTable.find('tbody').find_all('tr')[1:]:
            targetHeader = perkRow.find_all('th')[1]
            targetAnchor = targetHeader.find('a')
            perkUrl = targetAnchor.get('href','')
            perkName = targetAnchor.get('title','')
            perks += [Perk(perkType=PerkType.Survivor, perkName=f'{perkName} {"I" * (i+1)}', perkTier=i+1) for i in range(3)]
            fullUrl = f'{BASE_URL}{perkUrl}'
            doc = requests.get(fullUrl).content
            parser = BeautifulSoup(doc, 'html.parser')
            table = parser.find('table',attrs={'class':'wikitable'})
            targetRow = table.find_all('tr')[1] #second row contains gif info
            imgSrc = targetRow.find('img').get('src','')
            saveImageFromURL(imgSrc, tempGifPath)
            img = Image.open(tempGifPath)
            for frameIndex in range(img.n_frames):
                filename = f'{perkName} {"I" * (frameIndex + 1)}'.lower().replace(' ', '-').replace(':', '')
                perkPath = f'../images/perks/{filename}.png'
                if not os.path.exists(perkPath):
                    img.seek(frameIndex)
                    frameRGBA = img.convert("RGBA")
                    frameRGBA.save(perkPath)

        for perkRow in killerTable.find('tbody').find_all('tr')[1:]:
            targetHeader = perkRow.find_all('th')[1]
            targetAnchor = targetHeader.find('a')
            perkUrl = targetAnchor.get('href', '')
            perkName = targetAnchor.get('title', '')
            perks += [Perk(perkType=PerkType.Killer, perkName=f'{perkName} {"I" * (i+1)}', perkTier=i+1) for i in range(3)]
            fullUrl = f'{BASE_URL}{perkUrl}'
            doc = requests.get(fullUrl).content
            parser = BeautifulSoup(doc, 'html.parser')
            table = parser.find('table', attrs={'class': 'wikitable'})
            targetRow = table.find_all('tr')[1]  # second row contains gif info
            imgSrc = targetRow.find('img').get('src', '')
            saveImageFromURL(imgSrc, tempGifPath)
            img = Image.open(tempGifPath)
            for frameIndex in range(img.n_frames):
                filename = f'{perkName} {"I" * (frameIndex + 1)}'.lower().replace(' ', '-').replace(':', '')
                perkPath = f'../images/perks/{filename}.png'
                if not os.path.exists(perkPath):
                    img.seek(frameIndex)
                    frameRGBA = img.convert("RGBA")
                    frameRGBA.save(perkPath)


        itemsDoc = requests.get(ITEMS_URL).content
        itemsParser = BeautifulSoup(itemsDoc, 'html.parser')
        itemTypesInParsingOrder = [
            ItemType.Firecracker, ItemType.Flashlight, ItemType.Key,
            ItemType.Map, ItemType.Medkit, ItemType.Toolbox
        ]
        itemsTable = itemsParser.find_all('table', class_='wikitable')[1] #we need the second one, first one has rarities
        itemRows = itemsTable.find('tbody').find_all('tr')
        ITEM_ROW_CHILD_COUNT = 3
        currentIndex = -1
        currentItemType = itemTypesInParsingOrder[0]
        items = []
        for itemRow in itemRows:
            big = itemRow.find('big')
            if big is not None and big.text == 'Unused Items':
                break

            children = itemRow.find_all(recursive=False)
            childCount = len(children)
            if childCount != ITEM_ROW_CHILD_COUNT and children[0].name == 'th': #it means new section has begun
                currentIndex += 1
                currentItemType = itemTypesInParsingOrder[currentIndex]
            elif childCount == ITEM_ROW_CHILD_COUNT: #else we parse every new item
                itemImageTableHeader, itemNameTableHeader = children[0], children[1]
                itemName = itemNameTableHeader.find('a').get('title','').replace("(Item)", "").strip()
                items.append(Item(itemName=itemName, itemType=currentItemType))
                itemImageSrc = itemImageTableHeader.find('img').get('src','')
                filename = itemName.lower().replace('"','').replace(' ', '-').replace("'", '')
                itemImgPath = f'../images/items/{filename}.png'
                if not os.path.exists(itemImgPath):
                    saveImageFromURL(itemImageSrc, itemImgPath)

        addonsDoc = requests.get(ADDONS_URL).content
        addonsParser = BeautifulSoup(addonsDoc, 'html.parser')

        addonsRoot = addonsParser.find('div', class_='mw-parser-output')
        killerAddons, itemAddons = [], []
        #last 2 addon tables are not needed (they are for unused/decommisioned addons)
        children = addonsRoot.find_all(recursive=False)
        count = 0
        startIndex = 0
        killersCount = len(killers)
        for i, child in enumerate(children):
            if child.name == 'table':
                count += 1
            if count == 3: #third table
                startIndex = i + 2 #we need to skip one div
                break

        currentKiller = None
        killersDone = []
        for i in range(startIndex, len(children)):
            if len(killersDone) == killersCount:
                break
            tagName = children[i].name
            tableClass = children[i].get('class', 'none')[0] #for some reason this get() call returns a single element list
            if tagName == 'p':
                paragraphText = ''.join(children[i].find_all(text=True)).strip()
                if paragraphText:
                    currentKiller = next((k for k in killers if k.killerAlias in paragraphText), None)
                    print(f"Current killer: {currentKiller}")
            elif tagName == 'table' and tableClass == 'wikitable':
                addonRows = children[i].find('tbody').find_all('tr')[1:]
                for row in addonRows:
                    headers = row.find_all('th')
                    addonNameHeader, addonImageHeader = headers[1], headers[0]
                    addonName = addonNameHeader.find('a').get('title', '')
                    killerAddons.append(KillerAddon(killer=currentKiller, addonName=addonName))
                    imgSrc = addonImageHeader.find('img').get('src','')
                    filename = addonName.lower().replace(" ", "-").replace('"', '').replace("'", "")
                    imgPath = f'../images/addons/{filename}.png'
                    if not os.path.exists(imgPath):
                        saveImageFromURL(imgSrc, imgPath)
                killersDone.append(currentKiller)

        itemTypesInParsingOrder = itemTypesInParsingOrder[1:]
        addonTables = addonsRoot.find_all('table', class_='wikitable')

        itemAddonTables = addonTables[len(addonTables) - 2 - len(itemTypesInParsingOrder) - 1:len(addonTables) - 3]
        for i, table in enumerate(itemAddonTables):
            rows = table.find('tbody').find_all('tr')[1:] #we skip first row because its just headers
            for row in rows:
                headers = row.find_all('th')
                addonImageHeader, addonNameHeader = headers[0], headers[1]
                addonName = addonNameHeader.find('a').get('title', '')
                itemAddons.append(ItemAddon(itemType=itemTypesInParsingOrder[i], addonName=addonName))
                imgSrc = addonImageHeader.find('img').get('src', '')
                filename = addonName.lower().replace('"', '').replace("'", "").replace(' ', '-')
                imgPath = f'../images/addons/{filename}.png'
                if not os.path.exists(imgPath):
                    saveImageFromURL(imgSrc, imgPath)

        offeringsDoc = requests.get(OFFERINGS_URL).content
        offeringsParser = BeautifulSoup(offeringsDoc, 'html.parser')

        offeringTables = offeringsParser.find_all('table', class_='wikitable')
        offeringTables = offeringTables[:len(offeringTables)-2]
        offerings = []
        for table in offeringTables:
            rows = table.find('tbody').find_all('tr')
            for row in rows:
                headers = row.find_all('th')
                imgSrc = headers[0].find('img').get('src', '')
                offeringName = headers[1].find('a').get('title', '')
                offerings.append(Offering(offeringName=offeringName))
                filename = offeringName.lower().replace(' ', '-').replace('"', '').replace(':', '').replace('\'', '')
                imgFilePath = f'../images/offerings/{filename}.png'
                if not os.path.exists(imgFilePath):
                    saveImageFromURL(imgSrc, imgFilePath)

        realmsDoc = requests.get(REALM_URL).content
        realmsParser = BeautifulSoup(realmsDoc, 'html.parser')
        realmsRoot = realmsParser.find('div', class_="mw-parser-output")
        children = realmsRoot.find_all(recursive=False)
        childCount = len(children)
        startIndex = next((i for i in range(0, childCount) if children[i].name == 'h3'), 0)
        endIndex = next((i for i in range(0, childCount) if children[i].name == 'h3' and any(c.text == 'Recurring Locations' for c in children[i].find_all(recursive=False))), 0)
        realms = []
        for i in range(startIndex, endIndex, 2):
            realmName = children[i].find('a').get('title', '').replace("(Realm)", "").strip()
            maps = []
            for tag in children[i+1].find_all('td'):
                mapName = tag.find('center').find('a').get('title', '')
                maps.append(GameMap(mapName=mapName))
                imgSrc = tag.find('div', class_='center').find('img').get('src', '')
                filename = mapName.lower().replace("\"",'').replace(" ", "-").replace(":","").replace("'", "")
                imgFilePath = f'../images/maps/{filename}.png'
                if not os.path.exists(imgFilePath):
                    saveImageFromURL(imgSrc, imgFilePath)
            realms.append(Realm(maps=maps,realmName=realmName))

class DatabaseWorkerSignals(QObject):
    progressUpdated = pyqtSignal(str)
    finished = pyqtSignal()

class DatabaseUpdateWorker(QRunnable):

    def __init__(self):
        super().__init__()
        self._BASE_URL = 'https://deadbydaylight.fandom.com'
        self._BASE_WIKI_URL = 'https://deadbydaylight.fandom.com/wiki/'
        self.signals = DatabaseWorkerSignals()


    def run(self) -> None:
        killers = self.__updateKillerInfo(f'{self._BASE_WIKI_URL}Killers')
        survivors = self.__updateSurvivorInfo(f'{self._BASE_WIKI_URL}Survivors')
        items = self.__updateItems(f'{self._BASE_WIKI_URL}Items')
        perks = self.__updatePerks(f'{self._BASE_WIKI_URL}Perks')
        addons = self.__updateAddons(f'{self._BASE_WIKI_URL}Add-ons', killers)
        offerings = self.__updateOfferings(f'{self._BASE_WIKI_URL}Offerings')
        realms = self.__updateRealms(f'{self._BASE_WIKI_URL}Realms')

        guiMessageTemplates = [
            "Saving killers: progress {0}/{1}",
            "Saving survivors: progress {0}/{1}",
            "Saving items: progress {0}/{1}",
            "Saving perks: progress {0}/{1}",
            "Saving addons: progress {0}/{1}",
            "Saving offerings: progress {0}/{1}",
            "Saving realms: progress {0}/{1}",
        ]

        with Database.instance().getNewSession() as dbSession:
            for itemList, message in zip([killers, survivors, items, perks, addons, offerings, realms],guiMessageTemplates):
                currentItems, totalItems = 0, len(itemList)
                for item in itemList:
                    try:
                        with dbSession.begin():
                            dbSession.add(item)
                            dbSession.commit()
                    except Exception as e:
                        pass
                    finally:
                        currentItems += 1
                        self.signals.progressUpdated.emit(message.format(currentItems, totalItems))

        self.signals.finished.emit()


    def __updateKillerInfo(self, url: str) -> list[Killer]:
        self.signals.progressUpdated.emit("Updating killers...")
        killersDoc = requests.get(url).content
        killersParser = BeautifulSoup(killersDoc, 'html.parser')
        mainDiv = killersParser.find('div', attrs={'style': 'color: #fff;'})
        aTags = mainDiv.find_all('a')
        killers = [Killer(killerName=aTags[j].get('title', ''), killerAlias='The ' + aTags[j + 1].get('title', '')) for
                   i, j in enumerate(range(0, len(aTags), 2))]
        # killerUrls = [f"{self._BASE_URL}{a.get('href', '')}" for a in aTags[::2]]
        # self.signals.progressUpdated.emit("Updating killer portraits...")
        # for i, url in enumerate(killerUrls):
        #     killerPageParser = BeautifulSoup(requests.get(url).content, 'html.parser')
        #     infoTable = killerPageParser.find('table', attrs={"class": "infoboxtable"})
        #     imgTag = infoTable.find('img')
        #     imgUrl = imgTag.get('src', '')
        #     name = killers[i].killerAlias.lower().replace(' ', '-')
        #     dest = f'../images/killers/{name}.png'
        #     if not os.path.exists(dest):
        #         self.signals.progressUpdated.emit(f"Saving portrait: {name}.png")
        #         saveImageFromURL(imgUrl, dest)
        #     else:
        #         self.signals.progressUpdated.emit(f"Skipping portrait for {killers[i].killerAlias} because it already exists")
        return killers

    def __updateSurvivorInfo(self, url: str) -> list[Survivor]:
        self.signals.progressUpdated.emit("Updating survivors...")
        survivorsDoc = requests.get(url).content
        survivorsParser = BeautifulSoup(survivorsDoc, 'html.parser')
        mainDiv = survivorsParser.find('div', attrs={'style': 'color: #fff;'})
        aTags = mainDiv.find_all('a')
        survivors = [Survivor(survivorName=a.get('title', '')) for i, a in enumerate(aTags[::2])]
        # survivorUrls = [f"{self._BASE_URL}{a.get('href', '')}" for a in aTags[::2]]
        # self.signals.progressUpdated.emit("Updating survivor portraits...")
        # for i, url in enumerate(survivorUrls):
        #     survivorPageParser = BeautifulSoup(requests.get(url).content, 'html.parser')
        #     infoTable = survivorPageParser.find('table', attrs={"class": "infoboxtable"})
        #     imgTag = infoTable.find('img')
        #     imgUrl = imgTag.get('src', '')
        #     name = survivors[i].survivorName.lower().replace(' ', '-').replace('"', '')
        #     dest = f'../images/survivors/{name}.png'
        #     if not os.path.exists(dest):
        #         self.signals.progressUpdated.emit(f"Saving portrait: {name}.png")
        #         saveImageFromURL(imgUrl, dest)
        #     else:
        #         self.signals.progressUpdated.emit(f"Skipping portrait for {survivors[i].survivorName} because it already exists")

        return survivors

    def __updateItems(self, url: str) -> list[Item]:
        self.signals.progressUpdated.emit('Updating survivor items...')
        itemsDoc = requests.get(url).content
        itemsParser = BeautifulSoup(itemsDoc, 'html.parser')
        itemTypesInParsingOrder = [
            ItemType.Firecracker, ItemType.Flashlight, ItemType.Key,
            ItemType.Map, ItemType.Medkit, ItemType.Toolbox
        ]
        itemsTable = itemsParser.find_all('table', class_='wikitable')[
            1]  # we need the second one, first one has rarities
        itemRows = itemsTable.find('tbody').find_all('tr')
        ITEM_ROW_CHILD_COUNT = 3
        currentIndex = -1
        currentItemType = itemTypesInParsingOrder[0]
        items = []
        for itemRow in itemRows:
            big = itemRow.find('big')
            if big is not None and big.text == 'Unused Items':
                break

            children = itemRow.find_all(recursive=False)
            childCount = len(children)
            if childCount != ITEM_ROW_CHILD_COUNT and children[0].name == 'th':  # it means new section has begun
                currentIndex += 1
                currentItemType = itemTypesInParsingOrder[currentIndex]
                self.signals.progressUpdated.emit(f"Parsing items for type: {currentItemType.name}")
            elif childCount == ITEM_ROW_CHILD_COUNT:  # else we parse every new item
                itemImageTableHeader, itemNameTableHeader = children[0], children[1]
                itemName = itemNameTableHeader.find('a').get('title', '').replace("(Item)", "").strip()
                item = Item(itemName=itemName, itemType=currentItemType)
                items.append(item)
                itemImageSrc = itemImageTableHeader.find('img').get('src', '')
                filename = itemName.lower().replace('"', '').replace(' ', '-').replace("'", '')
                itemImgPath = f'../images/items/{filename}.png'
                if not os.path.exists(itemImgPath):
                    self.signals.progressUpdated.emit(f"Saving item icon: {filename}.png")
                    saveImageFromURL(itemImageSrc, itemImgPath)
                else:
                    self.signals.progressUpdated.emit(f"Skipping icon for {item.itemName} because it already exists")
        return items

    def __updatePerks(self, url: str) -> list[Perk]:
        perksDoc = requests.get(url).content
        perksParser = BeautifulSoup(perksDoc, 'html.parser')
        tables = perksParser.find_all('table', attrs={'class': 'wikitable sortable'})
        killerTable, survivorTable = tables[1], tables[0]
        tempGifPath = '../temp/temp.gif'
        perks = []
        self.signals.progressUpdated.emit("Updating survivor perks...")
        for perkRow in survivorTable.find('tbody').find_all('tr')[1:]:
            targetHeader = perkRow.find_all('th')[1]
            targetAnchor = targetHeader.find('a')
            perkUrl = targetAnchor.get('href', '')
            perkName = targetAnchor.get('title', '')
            perks += [Perk(perkType=PerkType.Survivor, perkName=f'{perkName} {"I" * (i + 1)}', perkTier=i + 1) for i in
                      range(3)]
            # fullUrl = f'{self._BASE_URL}{perkUrl}'
            # doc = requests.get(fullUrl).content
            # parser = BeautifulSoup(doc, 'html.parser')
            # table = parser.find('table', attrs={'class': 'wikitable'})
            # targetRow = table.find_all('tr')[1]  # second row contains gif info
            # imgSrc = targetRow.find('img').get('src', '')
            # saveImageFromURL(imgSrc, tempGifPath)
            # img = Image.open(tempGifPath)
            # for frameIndex in range(img.n_frames):
            #     filename = f'{perkName} {"I" * (frameIndex + 1)}'.lower().replace(' ', '-').replace(':', '')
            #     perkPath = f'../images/perks/{filename}.png'
            #     if not os.path.exists(perkPath):
            #         img.seek(frameIndex)
            #         frameRGBA = img.convert("RGBA")
            #         self.signals.progressUpdated.emit(f"Saving perk icon: {filename}.png")
            #         frameRGBA.save(perkPath)
            #     else:
            #         self.signals.progressUpdated.emit(f"Skipping icon for {perkName + ' ' + 'I' * (frameIndex+1)} because it already exists")
            #

        self.signals.progressUpdated.emit("Updating killer perks...")
        for perkRow in killerTable.find('tbody').find_all('tr')[1:]:
            targetHeader = perkRow.find_all('th')[1]
            targetAnchor = targetHeader.find('a')
            perkUrl = targetAnchor.get('href', '')
            perkName = targetAnchor.get('title', '')
            perks += [Perk(perkType=PerkType.Killer, perkName=f'{perkName} {"I" * (i + 1)}', perkTier=i + 1) for i in
                      range(3)]
            # fullUrl = f'{self._BASE_URL}{perkUrl}'
            # doc = requests.get(fullUrl).content
            # parser = BeautifulSoup(doc, 'html.parser')
            # table = parser.find('table', attrs={'class': 'wikitable'})
            # targetRow = table.find_all('tr')[1]  # second row contains gif info
            # imgSrc = targetRow.find('img').get('src', '')
            # saveImageFromURL(imgSrc, tempGifPath)
            # img = Image.open(tempGifPath)
            # for frameIndex in range(img.n_frames):
            #     filename = f'{perkName} {"I" * (frameIndex + 1)}'.lower().replace(' ', '-').replace(':', '')
            #     perkPath = f'../images/perks/{filename}.png'
            #     if not os.path.exists(perkPath):
            #         img.seek(frameIndex)
            #         frameRGBA = img.convert("RGBA")
            #         self.signals.progressUpdated.emit(f"Saving perk icon: {filename}.png")
            #         frameRGBA.save(perkPath)
            #     else:
            #         self.signals.progressUpdated.emit(f"Skipping icon for {perkName + ' ' + 'I' * (frameIndex + 1)} because it already exists")
        return perks

    def __updateOfferings(self, url: str) -> list[Offering]:
        self.signals.progressUpdated.emit("Updating offerings...")
        offeringsDoc = requests.get(url).content
        offeringsParser = BeautifulSoup(offeringsDoc, 'html.parser')

        offeringTables = offeringsParser.find_all('table', class_='wikitable')
        offeringTables = offeringTables[:len(offeringTables) - 2]
        offerings = []
        for table in offeringTables:
            rows = table.find('tbody').find_all('tr')
            for row in rows:
                headers = row.find_all('th')
                imgSrc = headers[0].find('img').get('src', '')
                offeringName = headers[1].find('a').get('title', '')
                offerings.append(Offering(offeringName=offeringName))
                filename = offeringName.lower().replace(' ', '-').replace('"', '').replace(':', '').replace('\'', '')
                imgFilePath = f'../images/offerings/{filename}.png'
                if not os.path.exists(imgFilePath):
                    self.signals.progressUpdated.emit(f"Saving icon {filename}.png")
                    saveImageFromURL(imgSrc, imgFilePath)
                else:
                    self.signals.progressUpdated.emit(f"Skipping icon for {offeringName} because it already exists")
        return offerings

    def __updateRealms(self, url: str) -> list[Realm]:
        self.signals.progressUpdated.emit("Updating realms...")
        realmsDoc = requests.get(url).content
        realmsParser = BeautifulSoup(realmsDoc, 'html.parser')
        realmsRoot = realmsParser.find('div', class_="mw-parser-output")
        children = realmsRoot.find_all(recursive=False)
        childCount = len(children)
        startIndex = next((i for i in range(0, childCount) if children[i].name == 'h3'), 0)
        endIndex = next((i for i in range(0, childCount) if children[i].name == 'h3' and any(
            c.text == 'Recurring Locations' for c in children[i].find_all(recursive=False))), 0)
        realms = []
        for i in range(startIndex, endIndex, 2):
            realmName = children[i].find('a').get('title', '').replace("(Realm)", "").strip()
            maps = []
            self.signals.progressUpdated.emit(f"Parsing maps for {realmName}...")
            for tag in children[i + 1].find_all('td'):
                mapName = tag.find('center').find('a').get('title', '')
                _map = GameMap(mapName=mapName)
                maps.append(_map)
                imgSrc = tag.find('div', class_='center').find('img').get('src', '')
                filename = mapName.lower().replace("\"", '').replace(" ", "-").replace(":", "").replace("'", "")
                imgFilePath = f'../images/maps/{filename}.png'
                if not os.path.exists(imgFilePath):
                    self.signals.progressUpdated.emit(f"Saving icon {filename}.png")
                    saveImageFromURL(imgSrc, imgFilePath)
                else:
                    self.signals.progressUpdated.emit(f"Skipping icon for {_map.mapName} because it already exists")
            realms.append(Realm(maps=maps, realmName=realmName))
        return realms

    def __updateAddons(self, url: str, killers: list[Killer]) -> list[Union[KillerAddon, ItemAddon]]:
        addonsDoc = requests.get(url).content
        addonsParser = BeautifulSoup(addonsDoc, 'html.parser')
        itemTypesInParsingOrder = [
            ItemType.Firecracker, ItemType.Flashlight, ItemType.Key,
            ItemType.Map, ItemType.Medkit, ItemType.Toolbox
        ]
        addonsRoot = addonsParser.find('div', class_='mw-parser-output')
        killerAddons, itemAddons = [], []
        # last 2 addon tables are not needed (they are for unused/decommisioned addons)
        children = addonsRoot.find_all(recursive=False)
        count = 0
        startIndex = 0
        killersCount = len(killers)
        self.signals.progressUpdated.emit("Updating killer add-ons...")
        for i, child in enumerate(children):
            if child.name == 'table':
                count += 1
            if count == 3:  # third table
                startIndex = i + 2  # we need to skip one div
                break

        currentKiller = None
        killersDone = []
        for i in range(startIndex, len(children)):
            if len(killersDone) == killersCount:
                break
            tagName = children[i].name
            tableClass = children[i].get('class', 'none')[
                0]  # for some reason this get() call returns a single element list
            if tagName == 'p':
                paragraphText = ''.join(children[i].find_all(text=True)).strip()
                if paragraphText:
                    currentKiller = next((k for k in killers if k.killerAlias in paragraphText), None)
                    self.signals.progressUpdated.emit(f"Parsing add-ons for killer: {currentKiller.killerAlias}")
            elif tagName == 'table' and tableClass == 'wikitable':
                addonRows = children[i].find('tbody').find_all('tr')[1:]
                for row in addonRows:
                    headers = row.find_all('th')
                    addonNameHeader, addonImageHeader = headers[1], headers[0]
                    addonName = addonNameHeader.find('a').get('title', '')
                    killerAddons.append(KillerAddon(killer=currentKiller, addonName=addonName))
                    imgSrc = addonImageHeader.find('img').get('src', '')
                    filename = addonName.lower().replace(" ", "-").replace('"', '').replace("'", "")
                    imgPath = f'../images/addons/{filename}.png'
                    if not os.path.exists(imgPath):
                        self.signals.progressUpdated.emit(f"Saving icon {filename}.png")
                        saveImageFromURL(imgSrc, imgPath)
                    else:
                        self.signals.progressUpdated.emit(f"Skipping icon for {addonName} because it already exists")
                killersDone.append(currentKiller)

        self.signals.progressUpdated.emit("Updating item add-ons...")
        itemTypesInParsingOrder = itemTypesInParsingOrder[1:]
        addonTables = addonsRoot.find_all('table', class_='wikitable')

        itemAddonTables = addonTables[len(addonTables) - 2 - len(itemTypesInParsingOrder) - 1:len(addonTables) - 3]
        for i, table in enumerate(itemAddonTables):
            self.signals.progressUpdated.emit(f"Parsing add-ons for item type: {itemTypesInParsingOrder[i].name}")
            rows = table.find('tbody').find_all('tr')[1:]  # we skip first row because its just headers
            for row in rows:
                headers = row.find_all('th')
                addonImageHeader, addonNameHeader = headers[0], headers[1]
                addonName = addonNameHeader.find('a').get('title', '')
                itemAddons.append(ItemAddon(itemType=itemTypesInParsingOrder[i], addonName=addonName))
                imgSrc = addonImageHeader.find('img').get('src', '')
                filename = addonName.lower().replace('"', '').replace("'", "").replace(' ', '-')
                imgPath = f'../images/addons/{filename}.png'
                if not os.path.exists(imgPath):
                    self.signals.progressUpdated.emit(f"Saving icon {filename}.png")
                    saveImageFromURL(imgSrc, imgPath)
                else:
                    self.signals.progressUpdated.emit(f"Skipping icon for {addonName} because it already exists")
        return itemAddons + killerAddons