import pytest
from solution import solve

def test_regression_0():
    assert solve(*[[['a', -1], ['b', 0]]]) == [['b', 0], ['a', -1]]
