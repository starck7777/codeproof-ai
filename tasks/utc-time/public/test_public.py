import pytest
from solution import solve

def test_public_0():
    assert solve(*['1970-01-01T00:00:00Z']) == 0
