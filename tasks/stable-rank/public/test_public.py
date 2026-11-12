import pytest
from solution import solve

def test_public_0():
    assert solve(*[[['b', 2], ['a', 3]]]) == [['a', 3], ['b', 2]]
