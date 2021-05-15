from __future__ import annotations

import os

import requests
import sqlalchemy
from PIL import Image
from bs4 import BeautifulSoup
from sqlalchemy.orm import Session

from models import Killer, Survivor, Perk, PerkType, ItemType, Item
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

        '''killersDoc = requests.get(KILLERS_URL).content
        killersParser = BeautifulSoup(killersDoc, 'html.parser')
        mainDiv = killersParser.find('div', attrs={'style': 'color: #fff;'})
        aTags = mainDiv.find_all('a')
        killers = [Killer(killerName=aTags[j].get('title', ''), killerAlias=aTags[j + 1].get('title', '')) for i, j in enumerate(range(0, len(aTags), 2))]
        killerUrls = [f"{BASE_URL}{a.get('href', '')}" for a in aTags[::2]]
        for i, url in enumerate(killerUrls):
            killerPageParser = BeautifulSoup(requests.get(url).content, 'html.parser')
            infoTable = killerPageParser.find('table', attrs={"class": "infoboxtable"})
            imgTag = infoTable.find('img')
            imgUrl = imgTag.get('src', '')
            name = killers[i].killerAlias.lower().replace(' ', '-')
            dest = f'../images/killers/the-{name}.png'
            if not os.path.exists(dest):
                saveImageFromURL(imgUrl, dest)'''
            # perksTable = killerPageParser.find('table', attrs={'class': 'wikitable'})
            # rows = perksTable.find_all('tr')
            # for row in rows:
            #     perkName = row.find_all('th')[1].find('a').get('title', '')#perk name is in second column
            #     parsedPerks = [
            #         Perk(perkTier=j + 1, perkType=PerkType.Killer, perkName=f'{perkName} {"I" * (j + 1)}') for j in range(3)
            #     ] #range 3 because there are only 3 perk tiers
            #     perks += parsedPerks
            #     #download and save images
            #     imgTag = row.find('img')
            #     gifUrl = imgTag.get('src', '')
            #     tempGifPath = '../temp/temp.gif'
            #     saveImageFromURL(gifUrl, tempGifPath)
            #     img = Image.open(tempGifPath)
            #     for frameIndex in range(img.n_frames):
            #         filename = f'{perkName} {"I" * (frameIndex + 1)}'.lower().replace(' ', '-').replace(':', '')
            #         gifPath = f'../images/perks/{filename}.png'
            #         if not os.path.exists(gifPath):
            #             img.seek(frameIndex)
            #             frameRGBA = img.convert("RGBA")
            #             frameRGBA.save(gifPath)


        '''survivorsDoc = requests.get(SURVIVORS_URL).content
        survivorsParser = BeautifulSoup(survivorsDoc, 'html.parser')
        mainDiv = survivorsParser.find('div', attrs={'style': 'color: #fff;'})
        aTags = mainDiv.find_all('a')
        survivors = [Survivor(survivorName=a.get('title', '')) for i, a in enumerate(aTags[::2])]
        survivorUrls = [f"{BASE_URL}{a.get('href', '')}" for a in aTags[::2]]'''

        """for i, url in enumerate(survivorUrls):
            survivorPageParser = BeautifulSoup(requests.get(url).content, 'html.parser')
            infoTable = survivorPageParser.find('table', attrs={"class": "infoboxtable"})
            imgTag = infoTable.find('img')
            imgUrl = imgTag.get('src', '')
            name = survivors[i].survivorName.lower().replace(' ', '-').replace('"', '')
            dest = f'../images/survivors/{name}.png'
            if not os.path.exists(dest):
                saveImageFromURL(imgUrl, dest)"""
            # perksTable = survivorPageParser.find('table', attrs={'class': 'wikitable'})
            # rows = perksTable.find_all('tr')
            # for row in rows:
            #     perkName = row.find_all('th')[1].find('a').get('title', '')#perk name is in second column
            #     perks += [
            #         Perk(perkTier=j + 1, perkType=PerkType.Survivor, perkName=f'{perkName} {"I" * (j + 1)}') for j in range(3)
            #     ] #range 3 because there are only 3 perk tiers
            #     #download and save images
            #     imgTag = row.find('img')
            #     gifUrl = imgTag.get('src', '')
            #     tempGifPath = '../temp/temp.gif'
            #     saveImageFromURL(gifUrl, tempGifPath)
            #     img = Image.open(tempGifPath)
            #     for frameIndex in range(img.n_frames):
            #         filename = f'{perkName} {"I" * (frameIndex + 1)}'.lower().replace(' ', '-').replace(':', '')
            #         gifPath = f'../images/perks/{filename}.png'
            #         if not os.path.exists(gifPath):
            #             img.seek(frameIndex)
            #             frameRGBA = img.convert("RGBA")
            #             frameRGBA.save(gifPath)

        '''perksDoc = requests.get(PERKS_URL).content
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
                    print(f"saving gif: {filename}")
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
                    print(f"saving gif: {filename}")
                    frameRGBA.save(perkPath)

        '''
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
                #todo: download item icon
                itemImageSrc = itemImageTableHeader.find('img').get('src','')

        # addonsDoc = requests.get(ADDONS_URL).content
        # addonsParser = BeautifulSoup(addonsDoc, 'html.parser')
        #
        # offeringsDoc = requests.get(OFFERINGS_URL).content
        # offeringsParser = BeautifulSoup(offeringsDoc, 'html.parser')
        #
        # realmsDoc = requests.get(REALM_URL).content
        # realmsParser = BeautifulSoup(realmsDoc, 'html.parser')