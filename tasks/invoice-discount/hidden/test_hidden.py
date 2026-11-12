import pytest
from solution import solve

def test_hidden_0():
    with pytest.raises(ValueError):
        solve(*[[[-1, 3]], 0])

def test_hidden_1():
    assert solve(*[[[2, 100]], 10]) == 180
