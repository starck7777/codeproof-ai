def solve(events):
    seen = set()
    total = 0
    for identity, amount in events:
        if identity not in seen:
            seen.add(identity)
            total += amount
    return total
