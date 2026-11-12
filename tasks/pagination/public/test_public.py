import pytest
from solution import solve

def test_public_0():
    assert solve(*[[1, 2, 3], 1, 2]) == [1, 2]
