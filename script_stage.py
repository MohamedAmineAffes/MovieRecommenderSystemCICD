import pandas as pd
import numpy as np
import pytest
from recommender import weighted_rating, get_recommendations, improved_recommendations, hybrid
from surprise import SVD

# Fixture to mock data
@pytest.fixture
def mock_data():
    # Mock smd DataFrame
    smd = pd.DataFrame({
        "title": ["The Godfather", "The Dark Knight", "Avatar"],
        "vote_count": [1000, 2000, 3000],
        "vote_average": [8.0, 8.5, 7.5],
        "year": [1972, 2008, 2009],
        "id": [1, 2, 3]
    })
    indices = pd.Series(range(len(smd)), index=smd["title"])
    cosine_sim = np.eye(len(smd))  # Dummy similarity matrix
    titles = smd["title"]
    id_map = pd.DataFrame({"movieId": [1, 2, 3], "id": [1, 2, 3], "title": smd["title"]}).set_index("title")
    indices_map = id_map.set_index("id")
    svd = SVD()
    return smd, indices, cosine_sim, titles, id_map, indices_map, svd

def test_weighted_rating():
    movie = pd.Series({'vote_count': 1000, 'vote_average': 8})
    score = weighted_rating(movie, m=100, C=6.0)  # Mock m and C
    assert isinstance(score, float)
    assert score > 0 and score <= 10


def test_improved_recommendations(mock_data):
    smd, indices, cosine_sim, titles, _, _, _ = mock_data
    results = improved_recommendations("The Godfather", smd, indices, cosine_sim, weighted_rating)
    assert isinstance(results, pd.DataFrame)
    assert "title" in results.columns
    assert len(results) > 0
