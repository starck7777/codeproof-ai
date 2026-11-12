import pytest
from solution import solve

def test_public_0():
    assert solve(*[['1', 'x', None]]) == [1]
