import pytest
import numpy as np
from recommender import (
    convert_int,
    get_director,
    weighted_rating,
)


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

if __name__ == "__main__":
    pytest.main()
