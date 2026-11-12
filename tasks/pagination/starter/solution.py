def solve(items, page, size):
    return items[page * size:(page + 1) * size]
