import pytest
from solution import solve

def test_regression_0():
    with pytest.raises(ValueError):
        solve(*['broken'])
