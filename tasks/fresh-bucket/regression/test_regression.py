import pytest
from solution import solve

def test_regression_0():
    assert solve(*['d', []]) == ['d']
