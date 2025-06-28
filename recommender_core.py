import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer, CountVectorizer
from sklearn.metrics.pairwise import linear_kernel, cosine_similarity
from nltk.stem.snowball import SnowballStemmer
from surprise import Reader, Dataset, SVD
from recommender import weighted_rating, get_director, filter_keywords, convert_int
from ast import literal_eval
import warnings

warnings.simplefilter("ignore")


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
