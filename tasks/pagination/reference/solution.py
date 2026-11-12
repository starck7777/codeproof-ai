def solve(items, page, size):
    if type(page) is not int or type(size) is not int or page < 1 or size < 1:
        raise ValueError("invalid page")
    return items[(page-1)*size:page*size]
