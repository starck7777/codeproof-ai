def solve(updates):
    cache = {}
    for key, value in updates:
        cache.setdefault(key, value)
    return cache
