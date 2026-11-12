def solve(updates):
    cache = {}
    for key, value in updates:
        if value is None:
            cache.pop(key, None)
        else:
            cache[key] = value
    return cache
