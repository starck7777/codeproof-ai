import pytest
from solution import solve

def test_hidden_0():
    assert solve(*[2, 2]) == [2]

def test_hidden_1():
    assert solve(*[3, 1]) == []
