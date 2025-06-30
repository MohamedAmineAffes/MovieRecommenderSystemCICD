import pytest
import pandas as pd
import numpy as np
from recommender import (
    load_data,
    weighted_rating,
    build_chart,
    get_recommendations,
    get_director,
    filter_keywords,
    improved_recommendations,
    convert_int,
    hybrid,
)

@pytest.fixture(scope="module")
def data():
    # Load the data only once for all tests
    return load_data()

def test_convert_int():
    assert convert_int("10") == 10
    assert np.isnan(convert_int("not_a_number"))

def test_get_director():
    crew = [{"job": "Director", "name": "James Cameron"}, {"job": "Producer", "name": "Someone"}]
    assert get_director(crew) == "James Cameron"
    assert np.isnan(get_director([{"job": "Producer", "name": "Someone"}]))


def test_weighted_rating():
    x = {"vote_count": 200, "vote_average": 8.5}
    m = 100
    C = 7.0
    wr = weighted_rating(x, m, C)
    assert wr > 0


def test_get_recommendations(data):
    titles = data["titles"]
    indices = data["indices"]
    cosine_sim = data["cosine_sim_basic"]
    # Pick a sample movie title from the dataset
    sample_title = titles.iloc[0]
    recs = get_recommendations(sample_title, titles, indices, cosine_sim)
    assert sample_title not in recs.values
    assert len(recs) == 30

if __name__ == "__main__":
    pytest.main()
