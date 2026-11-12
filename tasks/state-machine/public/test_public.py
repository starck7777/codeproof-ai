import pytest
from solution import solve

def test_public_0():
    assert solve(*[['paid', 'shipped']]) == 'shipped'
