import pytest
from solution import solve

def test_hidden_0():
    assert solve(*[' a = x=y ; ; b=2 ']) == {'a': 'x=y', 'b': '2'}

def test_hidden_1():
    assert solve(*['a=1;a=2']) == {'a': '2'}
