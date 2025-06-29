import numpy as np
import pandas as pd
from ast import literal_eval
from sklearn.feature_extraction.text import TfidfVectorizer, CountVectorizer
from sklearn.metrics.pairwise import linear_kernel, cosine_similarity
from nltk.stem.snowball import SnowballStemmer
from surprise import Reader, Dataset, SVD



def load_data():
    # Load metadata
    md = pd.read_csv("models/movies_metadata.csv")
    md["genres"] = md["genres"].fillna("[]").apply(literal_eval).apply(
        lambda x: [i["name"] for i in x] if isinstance(x, list) else []
    )
    md = md.drop([19730, 29503, 35587])
    md["id"] = md["id"].astype("int")

    # Load links dataset
    links_small = pd.read_csv("models/links_small.csv")
    links_small = links_small[links_small["tmdbId"].notnull()]["tmdbId"].astype("int")

    # Filter metadata
    smd = md[md["id"].isin(links_small)].copy()
    smd["tagline"] = smd["tagline"].fillna("")
    smd["description"] = smd["overview"].fillna("") + smd["tagline"]

    # Compute TF-IDF matrix
    tfidf = TfidfVectorizer(analyzer="word", ngram_range=(1, 2), min_df=1, stop_words="english")
    tfidf_matrix = tfidf.fit_transform(smd["description"])
    cosine_sim_basic = linear_kernel(tfidf_matrix, tfidf_matrix)

    smd = smd.reset_index(drop=True)
    titles = smd["title"]
    indices = pd.Series(smd.index, index=smd["title"])

    # Load additional datasets
    credits = pd.read_csv("models/credits.csv")
    keywords = pd.read_csv("models/keywords.csv")
    keywords["id"] = keywords["id"].astype("int")
    credits["id"] = credits["id"].astype("int")

    md = md.merge(credits, on="id").merge(keywords, on="id")
    smd = md[md["id"].isin(links_small)].copy()

    # Preprocess cast, crew, keywords
    smd["cast"] = smd["cast"].apply(literal_eval)
    smd["crew"] = smd["crew"].apply(literal_eval)
    smd["keywords"] = smd["keywords"].apply(literal_eval)

    smd["director"] = smd["crew"].apply(get_director)
    smd["cast"] = smd["cast"].apply(lambda x: [i["name"].lower().replace(" ", "") for i in x[:3]] if isinstance(x, list) else [])
    smd["director"] = smd["director"].astype(str).apply(lambda x: [x.lower().replace(" ", "")] * 3)
    smd["keywords"] = smd["keywords"].apply(lambda x: [i["name"].lower().replace(" ", "") for i in x if isinstance(i, dict)])

    # Filter rare keywords
    keyword_counts = smd.explode("keywords")["keywords"].value_counts()
    keyword_counts = keyword_counts[keyword_counts > 1]

    stemmer = SnowballStemmer("english")
    smd["keywords"] = smd["keywords"].apply(lambda x: filter_keywords(x, keyword_counts))
    smd["keywords"] = smd["keywords"].apply(lambda x: [stemmer.stem(i) for i in x])

    # Create soup feature
    smd["soup"] = smd["keywords"] + smd["cast"] + smd["director"] + smd["genres"]
    smd["soup"] = smd["soup"].apply(lambda x: " ".join(x))

    # Compute advanced cosine similarity
    count_vectorizer = CountVectorizer(analyzer="word", ngram_range=(1, 2), min_df=1, stop_words="english")
    count_matrix = count_vectorizer.fit_transform(smd["soup"])
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

    # ID mapping for hybrid
    id_map = pd.read_csv("models/links_small.csv")[["movieId", "tmdbId"]]
    id_map["tmdbId"] = id_map["tmdbId"].apply(convert_int)
    id_map.columns = ["movieId", "id"]
    id_map = id_map.merge(smd[["title", "id"]], on="id").set_index("title")
    indices_map = id_map.set_index("id")

    return {
        "titles": titles,
        "indices": indices,
        "cosine_sim_basic": cosine_sim_basic,
        "smd": smd,
        "titles_adv": titles_adv,
        "indices_adv": indices_adv,
        "cosine_sim_advanced": cosine_sim_advanced,
        "svd": svd,
        "id_map": id_map,
        "indices_map": indices_map
    }



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
