import pytest
from solution import solve

def test_hidden_0():
    assert solve(*[[0, '0', -2]]) == [0, 0, -2]

def test_hidden_1():
    assert solve(*[[]]) == []
