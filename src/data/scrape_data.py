import re
from datetime import datetime
from time import time, sleep

import numpy as np
import requests
from boardgamegeek import BoardGameGeek
from bs4 import BeautifulSoup
from retrying import retry
from tqdm import tqdm

from src.data.utils import retry_if_attribute_error


class BGGGame:
    def __init__(self, gamedict, gid, bgg):
        self.gid = gid
        self.bgg = bgg
        self.gamedict = gamedict

    @retry(wait_exponential_multiplier=500, wait_exponential_max=600000, stop_max_delay=600000,
           retry_on_exception=retry_if_attribute_error)
    def update_gamedata(self):
        url = self.gamedict['url']
        pagetext = requests.get(url)
        soup = BeautifulSoup(pagetext.text, "html.parser")
        gameinfo = re.search('geekitemPreload = (\{.*\}\});', soup.find("script").contents[0]).group(1)
        gameinfo_dict = eval(gameinfo.replace("true", "True")
                                     .replace("false", "False")
                                     .replace("null", "np.nan"))
        self.process_gameinfo(gameinfo_dict)

    def process_gameinfo(self, gameinfo_dict):
        g = self.bgg.game(game_id=self.gid)
        self.gamedict['description'] = g.description
        self.gamedict['minage'] = g.min_age
        self.gamedict['minplayers'] = g.min_players
        self.gamedict['maxplayers'] = g.max_players
        try:
            self.gamedict['minplaytime'] = int(gameinfo_dict['item']['minplaytime'])
        except:
            self.gamedict['minplaytime'] = np.nan
        try:
            self.gamedict['maxplaytime'] = int(gameinfo_dict['item']['maxplaytime'])
        except:
            self.gamedict['maxplaytime'] = np.nan
        try:
            self.gamedict['subdomain'] = gameinfo_dict['item']['rankinfo'][1]['subdomain']
        except:
            self.gamedict['subdomain'] = ''
        try:
            polls = gameinfo_dict['item']['polls']
            try:
                self.gamedict['weight'] = polls['boardgameweight']['averageweight']
            except:
                self.gamedict['weight'] = np.nan
            try:
                self.gamedict['weight_votes'] = polls['boardgameweight']['votes']
            except:
                self.gamedict['weight_votes'] = np.nan
            try:
                self.gamedict['suggested_age'] = int(polls['playerage'].replace('+',''))
            except:
                self.gamedict['suggested_age'] = np.nan
            try:
                self.gamedict['nplayers_best_min'] = \
                    int(min([d['min'] for d in polls['userplayers']['best']]))
            except:
                self.gamedict['nplayers_best_min'] = 0
            try:
                self.gamedict['nplayers_best_max'] = \
                    int(max([d['max'] for d in polls['userplayers']['best']]))
            except:
                self.gamedict['nplayers_best_max'] = 0
            try:
                self.gamedict['nplayers_recom_min'] = \
                    int(min([d['min'] for d in polls['userplayers']['recommended']]))
            except:
                self.gamedict['nplayers_recom_min'] = 0
            try:
                self.gamedict['nplayers_recom_max'] = \
                    int(max([d['max'] for d in polls['userplayers']['recommended']]))
            except:
                self.gamedict['nplayers_recom_max'] = 0
            try:
                self.gamedict['nplayers_votes'] = int(polls['userplayers']['totalvotes'])
            except:
                self.gamedict['nplayers_votes'] = np.nan
        except:
            self.gamedict['weight'] = np.nan
            self.gamedict['weight_votes'] = np.nan
            self.gamedict['suggested_age'] = np.nan
            self.gamedict['nplayers_best_min'] = 0
            self.gamedict['nplayers_best_max'] = 0
            self.gamedict['nplayers_recom_min'] = 0
            self.gamedict['nplayers_recom_max'] = 0
            self.gamedict['nplayers_votes'] = np.nan
        try:
            stats = gameinfo_dict['item']['stats']
            self.gamedict.update(stats)
        except:
            pass
        categories = {'cat-'+ele.lower(): 1 for ele in g.categories}
        self.gamedict.update(categories)
        mechanisms = {'mech-'+ele.lower(): 1 for ele in g.mechanics}
        self.gamedict.update(mechanisms)
        self.gamedict.update(categories)
        self.gamedict['updated'] = datetime.now()

    @staticmethod
    def new_game(gamesoup, publisher):
        game = {}
        try:
            game['rank'] = int(gamesoup.find("td", attrs={"class": "collection_rank"})
                                       .find("a")['name'])
        except TypeError:
            game['rank'] = 999999
        game['title'] = gamesoup.find("td", {"class": "collection_objectname"})\
                                .find("a").contents[0]
        game['url'] = "http://www.boardgamegeek.com" + \
                      gamesoup.find("td", {"class": "collection_objectname"}).find("a")['href']
        game['gameid'] = int(re.search(r'\/(\d*)\/',
                                       gamesoup.find("td", {"class": "collection_objectname"})
                                               .find("a")['href']).group(1))
        try:
            game['year'] = int(re.search('\((\d*)\)',
                                         gamesoup.find("td", {"class": "collection_objectname"})
                                                 .find("span").contents[0]).group(1))
        except AttributeError:
            game['year'] = 1900
        ratings = gamesoup.find_all("td", {"class": "collection_bggrating"})
        try:
            game['bggrating'] = float(ratings[0].contents[0])
        except ValueError:
            game['bggrating'] = None
        try:
            game['avgrating'] = float(ratings[1].contents[0])
        except ValueError:
            game['avgrating'] = None
        try:
            game['votes'] = int(ratings[2].contents[0])
        except ValueError:
            game['votes'] = 0
        game['publisher'] = publisher
        game['updated'] = datetime(2000, 1, 1)
        return game


class BGGInterface:
    def __init__(self, db):
        self.db = db
        self.bgg = BoardGameGeek()
        self.publishers = {
                "999 Games": "&include%5Bpublisherid%5D=267",
                "Asmodee": "&include%5Bpublisherid%5D=157",
                "Avalon Hill": "&include%5Bpublisherid%5D=5",
                "Bergsala Enigma": "&include%5Bpublisherid%5D=6784",
                "Cool mini or not": "&include%5Bpublisherid%5D=34793",
                "Czech Games Edition": "&include%5Bpublisherid%5D=7345",
                "Days of Wonder": "&include%5Bpublisherid%5D=1027",
                "Don & Co": "&include%5Bpublisherid%5D=137",
                "Fantasy Flight Games": "&include%5Bpublisherid%5D=17",
                "Fun Forge": "&include%5Bpublisherid%5D=8832",
                "Games Workshop": "&include%5Bpublisherid%5D=26",
                "Guillotine Games": "&include%5Bpublisherid%5D=21020",
                "Hurrican": "&include%5Bpublisherid%5D=6015",
                "Iello": "&include%5Bpublisherid%5D=8923",
                "Intrafin Games": "&include%5Bpublisherid%5D=5380",
                "Libellud": "&include%5Bpublisherid%5D=9051",
                "Ludonaute": "&include%5Bpublisherid%5D=11688",
                "Monolith Games": "&include%5Bpublisherid%5D=27147",
                "Osprey Games": "&include%5Bpublisherid%5D=29313",
                "Plaid Hat Games": "&include%5Bpublisherid%5D=10754",
                "Queen Games": "&include%5Bpublisherid%5D=47",
                "Repos Production": "&include%5Bpublisherid%5D=4384",
                "Space Cowboys": "&include%5Bpublisherid%5D=25842",
                "Steve Jackson Games": "&include%5Bpublisherid%5D=19",
                "Story Factory": "&include%5Bpublisherid%5D=17940",
                "Studio McVey": "&include%5Bpublisherid%5D=21608",
                "The Game Master": "&include%5Bpublisherid%5D=2862",
                "White Goblin Games": "&include%5Bpublisherid%5D=4932",
                "Z-Man Games": "&include%5Bpublisherid%5D=538"
            }

    def add_new_games(self):
        for k, v in tqdm(self.publishers.items(), total=len(self.publishers.keys())):
            self.get_games_of_publisher(k, v)
        self.save_data()

    def get_games_of_publisher(self, publisher, query, sleeptime=1):
        print('Processing games by {}'.format(publisher))
        more_games_available = True
        url = "https://boardgamegeek.com/search/boardgame/page/1?sort=rank&advsearch=1" + query
        while more_games_available:
            pagetext = requests.get(url)
            print(url)
            sleep(sleeptime)
            soup = BeautifulSoup(pagetext.text, "html.parser")
            if len(soup.find("div", attrs={"id": "collection"})
                       .find_all("tr", attrs={"id": "row_"})) > 0:
                for gamesoup in soup.find("div", attrs={"id": "collection"}) \
                                    .find_all("tr", attrs={"id": "row_"}):
                    game = BGGGame.new_game(gamesoup, publisher)
                    self.db.set_game(game, overwrite=False)
            try:
                url = "https://boardgamegeek.com" + soup.find("a", {"title": "next page"})['href']
            except TypeError:
                more_games_available = False
        print('')

    def save_data(self):
        self.db.close()

    def update_all_game_details(self, freshness=60, save_every=120):
        gameids = self.db.get_gameids_by(col='rank')
        t0 = time()
        for gid in tqdm(gameids):
            if 'updated' in self.db.games[gid]:
                try:
                    if (datetime.now() - self.db.games[gid]['updated']).days <= freshness:
                        continue
                except AttributeError:
                    pass
            try:
                print('{:>6} - {:>6} - {}'.format(gid, self.db.games[gid]['rank'],
                                                  self.db.games[gid]['url']))
            except:
                print("Couldn't print the game title for some reason")
            game = BGGGame(self.db.games[gid], gid, self.bgg)
            game.update_gamedata()
            self.db.set_game(game.gamedict, overwrite=True)
            t1 = time()
            if t1 - t0 >= save_every:
                self.save_data()
                t0 = time()
        self.save_data()

