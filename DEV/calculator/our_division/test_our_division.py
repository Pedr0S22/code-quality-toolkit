import pytest
from our_division import our_division
def test_trivial_division():
    assert our_division(4,2)==2, "Should be 2"
    
def test_for_negatives():
    assert our_division(-6,-3) == 2, "Should be 2"

def test_for_mixed():
    assert our_division(2, -2) == -1, "Should be -1"

def test_division_by_floats():
    assert our_division(5.0, 0.5) == 10.0, "Should be 10.0"

def test_division_by_zero():
    with pytest.raises(ZeroDivisionError) as ex:
        our_division(12, 0)

    assert str(ex.value) == "division by zero error", "should give a «division by zero error» message"