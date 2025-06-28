import pandas as pd
import numpy as np
from ast import literal_eval
from sklearn.feature_extraction.text import TfidfVectorizer, CountVectorizer
from sklearn.metrics.pairwise import linear_kernel, cosine_similarity
from nltk.stem.snowball import SnowballStemmer
from surprise import Reader, Dataset, SVD
from recommender import (
    weighted_rating,
    build_chart,
    get_recommendations,
    improved_recommendations,
    hybrid,
    get_director,
    filter_keywords,
    convert_int,
)
import warnings

warnings.simplefilter("ignore")

# === Load movies metadata and preprocess genres ===
md = pd.read_csv("models/movies_metadata.csv")
md["genres"] = (
    md["genres"]
    .fillna("[]")
    .apply(literal_eval)
    .apply(lambda x: [i["name"] for i in x] if isinstance(x, list) else [])
)

# Calculate mean vote and 95th percentile for vote counts (C and m)
vote_counts = md[md["vote_count"].notnull()]["vote_count"].astype("int")
vote_averages = md[md["vote_average"].notnull()]["vote_average"].astype("int")
C = vote_averages.mean()
m = vote_counts.quantile(0.95)

# Extract year from release_date safely
md["year"] = pd.to_datetime(md["release_date"], errors="coerce").apply(
    lambda x: str(x).split("-")[0] if pd.notnull(x) else np.nan
)

# Filter qualified movies based on m and not null votes
qualified = md[
    (md["vote_count"] >= m)
    & (md["vote_count"].notnull())
    & (md["vote_average"].notnull())
][["title", "year", "vote_count", "vote_average", "popularity", "genres"]]

qualified["vote_count"] = qualified["vote_count"].astype("int")
qualified["vote_average"] = qualified["vote_average"].astype("int")

# Calculate weighted rating for qualified movies
qualified["wr"] = qualified.apply(lambda x: weighted_rating(x, m, C), axis=1)
qualified = qualified.sort_values("wr", ascending=False).head(250)

# Prepare genre-specific dataframe gen_md for build_chart
s = (
    md.apply(lambda x: pd.Series(x["genres"]), axis=1)
    .stack()
    .reset_index(level=1, drop=True)
)
s.name = "genre"
gen_md = md.drop("genres", axis=1).join(s)

# Example: Build chart for 'Romance' genre
romance_chart = build_chart(gen_md, "Romance")
print("Top Romance Movies:\n", romance_chart.head(10))

# === Prepare small dataset based on links_small ===
links_small = pd.read_csv("models/links_small.csv")
links_small = links_small[links_small["tmdbId"].notnull()]["tmdbId"].astype("int")

# Drop bad rows from md
md = md.drop([19730, 29503, 35587])
md["id"] = md["id"].astype("int")

# Filter md by links_small
smd = md[md["id"].isin(links_small)]

# Fill tagline and description columns
smd["tagline"] = smd["tagline"].fillna("")
smd["description"] = smd["overview"] + smd["tagline"]
smd["description"] = smd["description"].fillna("")

# TF-IDF vectorization on description
tf = TfidfVectorizer(analyzer="word", ngram_range=(1, 2), min_df=1, stop_words="english")
tfidf_matrix = tf.fit_transform(smd["description"])

# Compute cosine similarity matrix
cosine_sim = linear_kernel(tfidf_matrix, tfidf_matrix)

# Reset index and prepare indices and titles series for recommendations
smd = smd.reset_index(drop=True)
titles = smd["title"]
indices = pd.Series(smd.index, index=smd["title"])

# === Example: get recommendations based on description similarity ===
print("Recommendations based on description for 'The Godfather':")
print(get_recommendations("The Godfather", titles, indices, cosine_sim).head(10))

# === Load credits and keywords, merge with md ===
credits = pd.read_csv("models/credits.csv")
keywords = pd.read_csv("models/keywords.csv")

keywords["id"] = keywords["id"].astype("int")
credits["id"] = credits["id"].astype("int")
md["id"] = md["id"].astype("int")

md = md.merge(credits, on="id")
md = md.merge(keywords, on="id")

# Filter md by links_small for advanced recommendations
smd = md[md["id"].isin(links_small)]

# Convert stringified lists to actual lists
smd["cast"] = smd["cast"].apply(literal_eval)
smd["crew"] = smd["crew"].apply(literal_eval)
smd["keywords"] = smd["keywords"].apply(literal_eval)

# Compute additional features
smd["cast_size"] = smd["cast"].apply(len)
smd["crew_size"] = smd["crew"].apply(len)
smd["director"] = smd["crew"].apply(get_director)
smd["cast"] = smd["cast"].apply(lambda x: [i["name"] for i in x] if isinstance(x, list) else [])
smd["cast"] = smd["cast"].apply(lambda x: x[:3] if len(x) >= 3 else x)
smd["keywords"] = smd["keywords"].apply(lambda x: [i["name"] for i in x] if isinstance(x, list) else [])

# Normalize text
smd["cast"] = smd["cast"].apply(lambda x: [str.lower(i.replace(" ", "")) for i in x])
smd["director"] = smd["director"].astype(str).apply(lambda x: x.lower().replace(" ", ""))
smd["director"] = smd["director"].apply(lambda x: [x, x, x])

# Filter and stem keywords
s = (
    smd.apply(lambda x: pd.Series(x["keywords"]), axis=1)
    .stack()
    .reset_index(level=1, drop=True)
)
s.name = "keyword"
s = s.value_counts()
s = s[s > 1]

stemmer = SnowballStemmer("english")
smd["keywords"] = smd["keywords"].apply(lambda x: filter_keywords(x, s))
smd["keywords"] = smd["keywords"].apply(lambda x: [stemmer.stem(i) for i in x])
smd["keywords"] = smd["keywords"].apply(lambda x: [i.lower().replace(" ", "") for i in x])

# Create "soup" feature for advanced content-based filtering
smd["soup"] = smd["keywords"] + smd["cast"] + smd["director"] + smd["genres"]
smd["soup"] = smd["soup"].apply(lambda x: " ".join(x))

# Compute count matrix and cosine similarity for "soup"
count = CountVectorizer(analyzer="word", ngram_range=(1, 2), min_df=1, stop_words="english")
count_matrix = count.fit_transform(smd["soup"])
cosine_sim = cosine_similarity(count_matrix, count_matrix)

smd = smd.reset_index(drop=True)
titles = smd["title"]
indices = pd.Series(smd.index, index=smd["title"])

# === Example: improved recommendations ===
print("Improved recommendations for 'The Dark Knight':")
print(improved_recommendations("The Dark Knight", smd, indices, cosine_sim, weighted_rating))

print("Improved recommendations for 'Mean Girls':")
print(improved_recommendations("Mean Girls", smd, indices, cosine_sim, weighted_rating))

# === Prepare SVD collaborative filtering model ===
reader = Reader()
ratings = pd.read_csv("models/ratings_small.csv")
data = Dataset.load_from_df(ratings[["userId", "movieId", "rating"]], reader)

svd = SVD()
from surprise.model_selection import cross_validate

results = cross_validate(svd, data, measures=["RMSE", "MAE"], cv=5, verbose=True)
trainset = data.build_full_trainset()
svd.fit(trainset)

# === Map movie IDs ===
id_map = pd.read_csv("models/links_small.csv")[["movieId", "tmdbId"]]
id_map["tmdbId"] = id_map["tmdbId"].apply(convert_int)
id_map.columns = ["movieId", "id"]
id_map = id_map.merge(smd[["title", "id"]], on="id").set_index("title")
indices_map = id_map.set_index("id")

# === Example: hybrid recommendation ===
print("Hybrid recommendations for user 1 and movie 'Avatar':")
print(hybrid(1, "Avatar", indices, cosine_sim, smd, id_map, indices_map, svd))

print("Hybrid recommendations for user 500 and movie 'Avatar':")
print(hybrid(500, "Avatar", indices, cosine_sim, smd, id_map, indices_map, svd))
