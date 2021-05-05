import sqlalchemy
import sqlite3
from bs4 import BeautifulSoup
from util import saveImageFromURL, splitGIFIntoImages
import requests
from models import Killer, Survivor
import os

class Database:
    __instance = None

    def __init__(self, url: str):
        self._engine = sqlalchemy.create_engine(url)

    def getNewSession(self):
        return Session(self._engine)

    @staticmethod
    def instance():
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

        killersDoc = requests.get(KILLERS_URL).content
        killersParser = BeautifulSoup(killersDoc, 'html.parser')
        mainDiv = killersParser.find('div', attrs={'style': 'color: #fff;'})
        aTags = mainDiv.find_all('a')
        killers = [Killer(killerID=i, killerName=aTags[j].get('title', ''), killerAlias=aTags[j+1].get('title', '')) for i, j in enumerate(range(0, len(aTags), 2))]
        killerUrls = [f"{BASE_URL}{a.get('href', '')}" for a in aTags[::2]]
        #todo: download killer portrait for each of the killers
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
        survivors = [Survivor(survivorID=i, survivorName=a.get('title', '')) for i,a in enumerate(aTags[::2])]
        survivorUrls = [f"{BASE_URL}{a.get('href', '')}" for a in aTags[::2]]

        for i, url in enumerate(survivorUrls):
            survivorPageParser = BeautifulSoup(requests.get(url).content, 'html.parser')
            infoTable = survivorPageParser.find('table', attrs={"class": "infoboxtable"})
            imgTag = infoTable.find('img')
            imgUrl = imgTag.get('src', '')
            name = survivors[i].survivorName.lower().replace(' ', '-')
            dest = f'../images/survivors/{name}.png'
            if not os.path.exists(dest):
                saveImageFromURL(imgUrl, dest)
            #todo: download gifs here and split them into perk icons

        print(killers)
        print(survivors)