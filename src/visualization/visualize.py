class CandidateViewer:
    def __init__(self, df):
        self.df = df

    def show_candidates(self):
        best_players_selections = ['2 players', '3 players', '4 players', '5 or more players']
        weight_selections = [(1, 1.4), (1.5, 1.9), (1.9, 2.5), (2.5, 3.1), (3.1, 4)]

        cols = ['title', 'year', 'weight', 'best_for', 'final_score', 'category-cluster',
                'mechanics-cluster', 'url']

        for n_players in best_players_selections:
            for weight_range in weight_selections:
                selection = (self.df['best_for'] == n_players) & (self.df['weight'] >= weight_range[0]) & \
                    (self.df['weight'] <= weight_range[1]) & (self.df['year'] >= 2000) & (self.df['weight_votes'] >= 10) & \
                    (self.df['final_score'] >= 15)
                print('Weight: {} to {} - Best for {}'.format(weight_range[0], weight_range[1], n_players))
                print('-'*80)
                selected = self.df[selection][cols].sort_values('final_score', ascending=False).head(10)
                for idx, row in selected.iterrows():
                    print('{:<35} ({}) - {:.2f}, {}, {:.1f}, Cat: {}, Mech: {}\n\t\t{}'\
                          .format(row['title'][:35], row['year'], row['weight'], row['best_for'], row['final_score'],
                                  row['category-cluster'][0], row['mechanics-cluster'][0], row['url']))
                print('\n\n')
