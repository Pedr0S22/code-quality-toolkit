import pytest
from our_multiplication import our_multiplication

def test_trivial_multiplication():
    assert our_multiplication(2, 3) == 6, "Should be 6"

def test_for_zero():
    assert our_multiplication(5, 0) == 0, "Should be 0 (error)"

def test_for_negatives():
    assert our_multiplication(-2, 3) == -6, "Should be -6"