import pytest
from solution import solve

def test_regression_0():
    assert solve(*[-2, 0]) == [-2, -1, 0]
