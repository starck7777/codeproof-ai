import pytest
from solution import solve

def test_hidden_0():
    assert solve(*[[['a', 1], ['a', None]]]) == {}

def test_hidden_1():
    assert solve(*[[['x', None]]]) == {}
