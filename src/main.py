from __future__ import annotations
import sys
from PyQt5.QtWidgets import QApplication
from MainWindow import MainWindow
from database import Database
from src.models import Killer, KillerAddon, GameMap, Realm, Item, ItemType, SurvivorMatch, SurvivorMatchResult, \
    Offering, OfferingType, Perk, SurvivorMatchPerk, PerkType, MatchKillerAddon, Survivor
from sqlalchemy import insert, select
from datetime import date


def main() -> None:
    Database.init('sqlite:///../dbd-match-log-DEV.db')
    # Database.update()
    # with Database.instance().getNewSession() as dbSession:
        # matchDate = date(2021, 5, 7)
        # offering = Offering(offeringName='Fresh Primrose Blossom', offeringType=OfferingType.Survivor)
        # realm = Realm(realmName='Autohaven Wreckers')
        # gameMap = GameMap(realm=realm,mapName='Gas Heaven')
        # realm.maps = [gameMap]
        # killer = Killer(killerName='Evan Macmillan',killerAlias='The Trapper')
        # perks = [Perk(perkName='Lithe', perkType=PerkType.Survivor, perkTier=3),Perk(perkName='Urban Evasion', perkType=PerkType.Survivor, perkTier=3),Perk(perkName='Borrowed Time', perkType=PerkType.Survivor, perkTier=3)]
        # matchPerks = [SurvivorMatchPerk(perk=perks[0]),SurvivorMatchPerk(perk=perks[1]),SurvivorMatchPerk(perk=perks[2])]
        # surv = Survivor(survivorName='Claudette Morel')
        # survMatch = SurvivorMatch(
        #     points=20000, matchDate=matchDate, partySize=3, survivor=surv,
        #     matchResult=SurvivorMatchResult.Escaped, rank=15, offering=offering,
        #     gameMap=gameMap, facedKiller=killer, item=None, itemAddons=[], perks=matchPerks
        # )
        # dbSession.add_all([survMatch, surv, offering, realm, gameMap, killer, *matchPerks, *perks])
        # query = select(SurvivorMatch)
        # matches = dbSession.execute(query).all()
        # print(matches)
        # dbSession.commit()
    app = QApplication(sys.argv)
    window = MainWindow(title='Dead by Daylight match log', windowSize=(960, 700))
    window.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()