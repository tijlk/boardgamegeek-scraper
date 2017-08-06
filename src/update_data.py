from src.data.scrape_data import BGGInterface
from src.features.build_features import FeatureGenerator
from src.visualization.visualize import CandidateViewer
from src.data.database import Database

db = Database()

bgg = BGGInterface(db)
bgg.add_new_games()
bgg.update_all_game_details()

feature_generator = FeatureGenerator(db.df)
feature_generator.do_clustering()
feature_generator.add_final_score_best_players()

bgg.df = feature_generator.df
bgg.save_data()

viewer = CandidateViewer(db.df)
viewer.show_candidates()
