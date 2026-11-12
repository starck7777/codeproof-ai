import pytest
from solution import solve

def test_hidden_0():
    assert solve(*[[['z', 2], ['a', 2]]]) == [['a', 2], ['z', 2]]

def test_hidden_1():
    assert solve(*[[]]) == []
