<<<<<<< HEAD
import pytest
from our_add import our_add
def test_trivial_division():
    assert our_division(4,2)==2, "Should be 2"
=======
def test_for_negatives():
    assert our_division(-6,-3) == 2, "Should be 2"
>>>>>>> 2c11f5a110f1adfda9e786fb2445155d9a3abac3

def test_for_mixed():
    assert our_division(2, -2) == 1, "Should be 1 (error)"