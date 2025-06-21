import numpy as np
import pandas as pd
from ast import literal_eval
from sklearn.feature_extraction.text import TfidfVectorizer, CountVectorizer
from sklearn.metrics.pairwise import linear_kernel, cosine_similarity
from nltk.stem.snowball import SnowballStemmer
from surprise import Reader, Dataset, SVD

# Global variables you might want to initialize later with real data:
C = None
m = None
vote_counts = None
vote_averages = None
cosine_sim = None
smd = None
indices = None
id_map = None
indices_map = None
svd = None

def weighted_rating(x, m, C):
    v = x["vote_count"]
    R = x["vote_average"]
    return (v / (v + m) * R) + (m / (m + v) * C)

def build_chart(gen_md, genre, percentile=0.85):
    df = gen_md[gen_md["genre"] == genre]
    vote_counts = df[df["vote_count"].notnull()]["vote_count"].astype("int")
    vote_averages = df[df["vote_average"].notnull()]["vote_average"].astype("int")
    C = vote_averages.mean()
    m = vote_counts.quantile(percentile)

    qualified = df[
        (df["vote_count"] >= m)
        & (df["vote_count"].notnull())
        & (df["vote_average"].notnull())
    ][["title", "year", "vote_count", "vote_average", "popularity"]]
    qualified["vote_count"] = qualified["vote_count"].astype("int")
    qualified["vote_average"] = qualified["vote_average"].astype("int")

    qualified["wr"] = qualified.apply(
        lambda x: (x["vote_count"] / (x["vote_count"] + m) * x["vote_average"])
        + (m / (m + x["vote_count"]) * C),
        axis=1,
    )
    qualified = qualified.sort_values("wr", ascending=False).head(250)
    return qualified

def get_recommendations(title, titles, indices, cosine_sim):
    idx = indices[title]
    sim_scores = list(enumerate(cosine_sim[idx]))
    sim_scores = sorted(sim_scores, key=lambda x: x[1], reverse=True)
    sim_scores = sim_scores[1:31]
    movie_indices = [i[0] for i in sim_scores]
    return titles.iloc[movie_indices]

def get_director(crew):
    for i in crew:
        if i["job"] == "Director":
            return i["name"]
    return np.nan

def filter_keywords(x, s):
    words = []
    for i in x:
        if i in s:
            words.append(i)
    return words

def improved_recommendations(title, smd, indices, cosine_sim, weighted_rating):
    idx = indices[title]
    sim_scores = list(enumerate(cosine_sim[idx]))
    sim_scores = sorted(sim_scores, key=lambda x: x[1], reverse=True)
    sim_scores = sim_scores[1:26]
    movie_indices = [i[0] for i in sim_scores]

    movies = smd.iloc[movie_indices][["title", "vote_count", "vote_average", "year"]]
    vote_counts = movies[movies["vote_count"].notnull()]["vote_count"].astype("int")
    vote_averages = movies[movies["vote_average"].notnull()]["vote_average"].astype("int")
    C = vote_averages.mean()
    m = vote_counts.quantile(0.60)
    qualified = movies[
        (movies["vote_count"] >= m)
        & (movies["vote_count"].notnull())
        & (movies["vote_average"].notnull())
    ]
    qualified["vote_count"] = qualified["vote_count"].astype("int")
    qualified["vote_average"] = qualified["vote_average"].astype("int")
    qualified["wr"] = qualified.apply(lambda x: weighted_rating(x, m, C), axis=1)
    qualified = qualified.sort_values("wr", ascending=False).head(10)
    return qualified

def convert_int(x):
    try:
        return int(x)
    except:
        return np.nan

def hybrid(userId, title, indices, cosine_sim, smd, id_map, indices_map, svd):
    idx = indices[title]
    tmdbId = id_map.loc[title]["id"]
    movie_id = id_map.loc[title]["movieId"]
    sim_scores = list(enumerate(cosine_sim[int(idx)]))
    sim_scores = sorted(sim_scores, key=lambda x: x[1], reverse=True)
    sim_scores = sim_scores[1:26]
    movie_indices = [i[0] for i in sim_scores]
    movies = smd.iloc[movie_indices][
        ["title", "vote_count", "vote_average", "year", "id"]
    ]
    movies["est"] = movies["id"].apply(
        lambda x: svd.predict(userId, indices_map.loc[x]["movieId"]).est
    )
    movies = movies.sort_values("est", ascending=False)
    return movies.head(10)
