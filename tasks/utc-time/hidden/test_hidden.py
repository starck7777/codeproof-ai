import pytest
from solution import solve

def test_hidden_0():
    assert solve(*['1970-01-01T02:00:00+02:00']) == 0

def test_hidden_1():
    assert solve(*['1970-01-01T00:00:01']) == 1
