from solution import solve

def test_independent_calls():
    assert solve("b") == ["b"]
    assert solve("d") == ["d"]
