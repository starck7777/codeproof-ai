import pytest
from solution import solve

def test_hidden_0():
    assert solve(*[[['a', 0], ['a', 8]]]) == 0

def test_hidden_1():
    assert solve(*[[['a', 3], ['b', -2]]]) == 1
