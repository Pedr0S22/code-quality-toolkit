import pytest
from our_module import our_module

#Our_module test functions to check its behavior with int and float inputs
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
    
def test_negative_numbers():
    # Testando casos com números negativos
    assert our_module(-10, 3) == 2, "Should be 2"      # Python: -10 % 3 = 2
    assert our_module(10, -3) == -2, "Should be -2"    # Python: 10 % -3 = -2
    assert our_module(-10, -3) == -1, "Should be -1"   # Python: -10 % -3 = -1
    assert our_module(-5, 8) == 3, "Should be 3"       # Python: -5 % 8 = 3
    assert our_module(5, -8) == -3, "Should be -3"     # Python: 5 % -8 = -3
    assert our_module(-12, 4) == 0, "Should be 0"      # Python: -12 % 4 = 0
    assert our_module(-13, -13) == 0, "Should be 0"    # Python: -13 % -13 = 0


# @pytest.mark.parametrize(
#     "a, b, expected",
#     [ (0, 3.5, 0.5), (10, 2.5, 0), (33.5, 5, 3.5), (55.5, 5.5, 0.5) ]
# )
# def test_multiples(a, b, expected):
#     assert our_module(a, b) == expected
