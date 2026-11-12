import pytest
from solution import solve

def test_regression_0():
    assert solve(*[[' 3 ', {}, '4']]) == [3, 4]
