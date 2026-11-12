import pytest
from solution import solve

def test_public_0():
    assert solve(*['a=1']) == {'a': '1'}
