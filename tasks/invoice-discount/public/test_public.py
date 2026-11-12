import pytest
from solution import solve

def test_public_0():
    assert solve(*[[[1, 1], [1, 1]], 50]) == 1
