import re
from collections import Counter
from datetime import date

import numpy as np
from sklearn.cluster import KMeans
import operator
from tqdm import tqdm


class FeatureGenerator:
    def __init__(self, df):
        self.df = df

    def do_clustering(self, n_clusters=5, biggest_cluster=999999, imax=50000, cluster_max=140):
        cat_cols = [col for col in self.df.columns if 'cat-' in col and
                    col != 'cat-expansion for base-game' and col != 'cat-fan expansion']
        mech_cols = [col for col in self.df.columns if 'mech-' in col]
        selection = (self.df['updated'] == 1) & (self.df['rank'] <= 1000)

        for c, x in zip(['category-cluster', 'mechanics-cluster'], [cat_cols, mech_cols]):
            data = np.array(self.df[selection][x].fillna(0))
            print("\nKmeans Clustering\n")
            for i in tqdm(range(imax)):
                km = KMeans(n_clusters=n_clusters, init='k-means++', max_iter=1000, n_init=1)\
                    .fit(data)
                clusters = list(km.predict(data))
                biggest_cluster = max([tupl[1] for tupl in Counter(clusters).items()])
                if biggest_cluster < cluster_max:
                    break
            if biggest_cluster >= cluster_max:
                print('No suitable cluster configuration found!')
            print(Counter(clusters).items())

            cluster_titles = []
            for cl in range(0, n_clusters):
                center = km.cluster_centers_[cl]
                center = {x[idx]: int(np.round(cat * 100)) for idx, cat in enumerate(center)}
                sorted_x = sorted(center.items(), key=operator.itemgetter(1), reverse=True)
                for cat in sorted_x[:5]:
                    print('* {} - {}'.format(re.sub(r'(cat-|mech-)', '', cat[0]), cat[1]))

                cluster_titles.append(str(cl + 1) + ') ' + ' - '.join(
                    [re.sub(r'(cat-|mech-)', '', cat[0]) for cat in sorted_x[:3]]))
                indices = [i for i, clu in enumerate(clusters) if clu == cl]
                df_cluster = self.df[selection].iloc[indices]
                print(("\n{}" + '-' * 100 + '\n')
                      .format(list(df_cluster[df_cluster['votes'] >= 10000]['title'])))

            print(cluster_titles)
            data_all = np.array(self.df[x].fillna(0))
            clusters_all = list(km.predict(data_all))
            print(len(self.df))
            print(len([cluster_titles[ele] for ele in clusters_all]))
            self.df[c] = [cluster_titles[ele] for ele in clusters_all]

    def add_final_score_best_players(self):
        self.df['final_score'] = self.df.apply(self.final_score, axis=1)
        self.df['best_for'] = self.df.apply(self.best_players, axis=1)

    @staticmethod
    def final_score(row):
        years_since_publishing = date.today().year - row['year'] + 2
        lasting_popularity = np.log10(
            row['numplays_month'] + row['numplays'] / 10000. * np.log10(years_since_publishing))
        final_score = row['bggrating'] * 2 + lasting_popularity
        return final_score

    @staticmethod
    def best_players(row):
        if row['nplayers_best_min'] == 2:
            return '2 players'
        elif row['nplayers_best_min'] == 3:
            return '3 players'
        elif row['nplayers_best_min'] == 4:
            return '4 players'
        elif row['nplayers_best_min'] >= 5:
            return '5 or more players'
