import pytest
from our_module import our_module

def test_float():
    assert our_module(10, 2.5 ) == 0, "Should be 0"
    assert our_module(33.5, 5 ) == 3.5, "Should be 3.5"
    assert our_module(55.5, 5.5 ) == 0.5, "Should be 0.5"
