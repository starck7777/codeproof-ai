def solve(entries):
    return sorted(entries, key=lambda x: (-x[1], x[0]))
