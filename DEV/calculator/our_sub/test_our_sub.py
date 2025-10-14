import pytest
from our_sub import our_sub

def test_sub_equal_number(a,b):
    assert our_sub(2, 3 ) == 0, "Should be 0 always"
