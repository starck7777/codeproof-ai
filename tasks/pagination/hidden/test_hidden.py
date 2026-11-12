import pytest
from solution import solve

def test_hidden_0():
    assert solve(*[[1], 4, 1]) == []

def test_hidden_1():
    with pytest.raises(ValueError):
        solve(*[[1], 0, 1])
