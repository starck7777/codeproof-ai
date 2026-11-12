import pytest
from solution import solve

def test_hidden_0():
    with pytest.raises(ValueError):
        solve(*[['delivered']])

def test_hidden_1():
    assert solve(*[['paid', 'paid', 'cancelled']]) == 'cancelled'
