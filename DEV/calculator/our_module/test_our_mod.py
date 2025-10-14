import pytest
from our_module import our_module

def test_float():
    assert our_module(10, 2.5 ) == 0, "Should be 0"
    assert our_module(33.5, 5 ) == 3.5, "Should be 3.5"
    assert our_module(55.5, 5.5 ) == 0.5, "Should be 0.5"

def test_int():
    assert our_module(10, 3 ) == 1, "Should be 1"
    assert our_module(5, 8 ) == 5, "Should be 5"
    assert our_module(12, 4 ) == 0, "Should be 0"
    assert our_module(0, 5 ) == 0, "Should be 0"
    assert our_module(13, 13 ) == 0, "Should be 0"


# @pytest.mark.parametrize(
#     "a, b, expected",
#     [ (0, 3.5, 0.5), (10, 2.5, 0), (33.5, 5, 3.5), (55.5, 5.5, 0.5) ]
# )
# def test_multiples(a, b, expected):
#     assert our_module(a, b) == expected
