import pytest
from solution import solve

def test_regression_0():
    assert solve(*['1969-12-31T23:00:00-01:00']) == 0
