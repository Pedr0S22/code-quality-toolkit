import pytest
from our_multiplication import our_multiplication

def test_trivial_multiplication():
    assert our_multiplication(2, 3) == 6, "Should be 6"
