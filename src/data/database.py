import sqlite3
from datetime import datetime

import numpy as np
import pandas as pd


class Database:
    def __init__(self, filename='data/processed/bgg.db'):
        self.filename = filename
        self.conn = None
        self.games = self.load()
        self.df = None
        print(len(self.games))

    def load(self):
        self.conn = sqlite3.connect(self.filename)
        try:
            df = pd.read_sql_query("select * from games;", self.conn)
            df.set_index('gameid', inplace=True, drop=False)
            df['updated'] = df['updated'].apply(lambda x: self.parse_date(x))
            df.index.name = 'gameid'
            self.df = df
        except pd.io.sql.DatabaseError:
            print("The games table cannot be found in the database. " +
                  "Therefore, I'm initalizing the database from scratch")
            self.conn.close()
            return {}
        else:
            df_dict = self.df.to_dict(orient='index')
            print("database at {} loaded".format(self.filename))
            self.conn.close()
            return df_dict

    @staticmethod
    def parse_date(date_string):
        if isinstance(date_string, str):
            return datetime.strptime(date_string, '%Y-%m-%d %H:%M:%S.%f')
        else:
            return date_string

    def close(self):
        self.games_as_df()
        self.conn = sqlite3.connect(self.filename)
        try:
            cur = self.conn.cursor()
            count_info = cur.execute("select count(*) as n from games;").fetchall()
            cur.close()
            n = count_info[0][0]
        except sqlite3.OperationalError:
            n = 0
        if len(self.df) < n:
            raise GamesDisappearedError
        else:
            self.df.to_sql("games", self.conn, if_exists="replace", index=False)
            print("         Data saved at {}".format(self.filename))
        self.conn.close()

    def set_game(self, game, overwrite=True, verbose=False):
        try:
            if not isinstance(game, dict):
                raise TypeError
        except TypeError:
            print("Uh oh!")
            print(game.gamedict)
        else:
            if game['gameid'] in self.games and not overwrite:
                if verbose:
                    print("Game id {} is already in the database".format(game['gameid']))
            else:
                self.games[game['gameid']] = game

    def get_game(self, gameid):
        try:
            return self.games[gameid]
        except KeyError as e:
            print("Game id {} does not exist in the database.".format(e.args[0]))
            raise GameNotInDatabaseError(gameid=gameid)

    def print(self):
        for game in self.games:
            self.games[game].print()

    def get_gameids_by(self, col='rank', reverse=False):
        list_of_tuples = [(gameid, self.games[gameid][col]) for gameid in self.games]
        sorted_tuples = sorted(list_of_tuples, key=lambda x: x[1], reverse=reverse)
        return [k for k, v in sorted_tuples]

    def games_as_df(self):
        df = pd.DataFrame.from_dict(self.games, orient='index')
        df = df.where((pd.notnull(df)), None)
        df['random'] = np.random.uniform(low=-0.5, high=0.5, size=(len(df),))
        df.index.name = 'gameid'
        self.games = df.to_dict(orient='index')
        self.df = df


class GameNotInDatabaseError(Exception):
    def __init__(self, gameid=None):
        self.gameid = gameid


class GamesDisappearedError(Exception):
    def __init__(self):
        pass
