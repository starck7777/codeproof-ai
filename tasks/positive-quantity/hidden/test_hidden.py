import pytest
from solution import solve

def test_hidden_0():
    with pytest.raises(ValueError):
        solve(*[0, 3])

def test_hidden_1():
    with pytest.raises(ValueError):
        solve(*[True, 2])
