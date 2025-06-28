from flask import Flask, request, jsonify, render_template
import pandas as pd
import numpy as np
from ast import literal_eval
from sklearn.feature_extraction.text import TfidfVectorizer, CountVectorizer
from sklearn.metrics.pairwise import linear_kernel, cosine_similarity
from nltk.stem.snowball import SnowballStemmer
from surprise import Reader, Dataset, SVD
from recommender import (
    weighted_rating,
    get_recommendations,
    improved_recommendations,
    hybrid,
    get_director,
    filter_keywords,
    convert_int,
)
import warnings

warnings.simplefilter("ignore")

app = Flask(__name__)

# ===== Load Data Once =====
print("Loading data...")

# Metadata
md = pd.read_csv("models/movies_metadata.csv")
md["genres"] = md["genres"].fillna("[]").apply(literal_eval).apply(lambda x: [i["name"] for i in x] if isinstance(x, list) else [])
md = md.drop([19730, 29503, 35587])
md["id"] = md["id"].astype("int")

# Small links dataset
links_small = pd.read_csv("models/links_small.csv")
links_small = links_small[links_small["tmdbId"].notnull()]["tmdbId"].astype("int")

# Initial filtering
smd = md[md["id"].isin(links_small)]
smd["tagline"] = smd["tagline"].fillna("")
smd["description"] = smd["overview"] + smd["tagline"]
smd["description"] = smd["description"].fillna("")

# TF-IDF Matrix
tf = TfidfVectorizer(analyzer="word", ngram_range=(1, 2), min_df=1, stop_words="english")
tfidf_matrix = tf.fit_transform(smd["description"])
cosine_sim_basic = linear_kernel(tfidf_matrix, tfidf_matrix)

smd = smd.reset_index(drop=True)
titles = smd["title"]
indices = pd.Series(smd.index, index=smd["title"])

# Advanced Features
credits = pd.read_csv("models/credits.csv")
keywords = pd.read_csv("models/keywords.csv")
keywords["id"] = keywords["id"].astype("int")
credits["id"] = credits["id"].astype("int")
md = md.merge(credits, on="id").merge(keywords, on="id")
smd = md[md["id"].isin(links_small)]

# Preprocessing
smd["cast"] = smd["cast"].apply(literal_eval)
smd["crew"] = smd["crew"].apply(literal_eval)
smd["keywords"] = smd["keywords"].apply(literal_eval)
smd["director"] = smd["crew"].apply(get_director)
smd["cast"] = smd["cast"].apply(lambda x: [i["name"].lower().replace(" ", "") for i in x[:3]] if isinstance(x, list) else [])
smd["director"] = smd["director"].astype(str).apply(lambda x: [x.lower().replace(" ", "")]*3)
smd["keywords"] = smd["keywords"].apply(lambda x: [i["name"].lower().replace(" ", "") for i in x if isinstance(x, dict)])

# Filter keywords
s = smd.explode("keywords")["keywords"].value_counts()
s = s[s > 1]
stemmer = SnowballStemmer("english")
smd["keywords"] = smd["keywords"].apply(lambda x: filter_keywords(x, s))
smd["keywords"] = smd["keywords"].apply(lambda x: [stemmer.stem(i) for i in x])

# Soup feature
smd["soup"] = smd["keywords"] + smd["cast"] + smd["director"] + smd["genres"]
smd["soup"] = smd["soup"].apply(lambda x: " ".join(x))

# Count Vectorizer for advanced recommendations
count = CountVectorizer(analyzer="word", ngram_range=(1, 2), min_df=1, stop_words="english")
count_matrix = count.fit_transform(smd["soup"])
cosine_sim_advanced = cosine_similarity(count_matrix, count_matrix)

smd = smd.reset_index(drop=True)
titles_adv = smd["title"]
indices_adv = pd.Series(smd.index, index=smd["title"])

# Collaborative filtering
ratings = pd.read_csv("models/ratings_small.csv")
reader = Reader()
data = Dataset.load_from_df(ratings[["userId", "movieId", "rating"]], reader)
svd = SVD()
trainset = data.build_full_trainset()
svd.fit(trainset)

# ID Mapping
id_map = pd.read_csv("models/links_small.csv")[["movieId", "tmdbId"]]
id_map["tmdbId"] = id_map["tmdbId"].apply(convert_int)
id_map.columns = ["movieId", "id"]
id_map = id_map.merge(smd[["title", "id"]], on="id").set_index("title")
indices_map = id_map.set_index("id")

print("Data loaded successfully.")


# ===== API Routes =====

@app.route("/")
def home():
    return render_template("index.html")


@app.route("/recommend/basic", methods=["GET"])
def recommend_basic():
    movie = request.args.get("title")
    if movie not in titles.values:
        return jsonify({"error": "Movie not found"}), 404
    recs = get_recommendations(movie, titles, indices, cosine_sim_basic).head(10)
    return jsonify(recs.tolist())


@app.route("/recommend/improved", methods=["GET"])
def recommend_improved():
    movie = request.args.get("title")
    if movie not in titles_adv.values:
        return jsonify({"error": "Movie not found"}), 404
    recs = improved_recommendations(movie, smd, indices_adv, cosine_sim_advanced, weighted_rating)
    return jsonify(recs.tolist())


@app.route("/recommend/hybrid", methods=["GET"])
def recommend_hybrid():
    movie = request.args.get("title")
    user_id = request.args.get("userId", type=int)
    if movie not in titles_adv.values:
        return jsonify({"error": "Movie not found"}), 404
    recs = hybrid(user_id, movie, indices_adv, cosine_sim_advanced, smd, id_map, indices_map, svd)
    return jsonify(recs.tolist())


# ===== Main =====

if __name__ == "__main__":
    app.run(debug=True)
