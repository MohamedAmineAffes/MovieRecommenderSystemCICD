import pytest
from recommender import (

    weighted_rating,
)

def test_weighted_rating():
    x = {"vote_count": 200, "vote_average": 8.5}
    m = 100
    C = 7.0
    wr = weighted_rating(x, m, C)
    assert wr > 0

if __name__ == "__main__":
    pytest.main()
