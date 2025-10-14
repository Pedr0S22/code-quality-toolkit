import pytest
from our_sub import our_sub

def test_sub_equal_trivialsubstraction():
    assert our_sub(5,2) == 3, "Should be 3 always"

def test_sub_negative_number():
    assert our_sub(5, -3) == 8, "Should be 8 always"

def test_sub_equal_number():
    assert our_sub(3, 3 ) == 0, "Should be 0 always"
