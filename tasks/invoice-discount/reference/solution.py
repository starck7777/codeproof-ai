def solve(lines, discount):
    if type(discount) is not int or not 0 <= discount <= 100:
        raise ValueError("invalid discount")
    for q, p in lines:
        if type(q) is not int or type(p) is not int or q < 0 or p < 0:
            raise ValueError("invalid line")
    return sum(q*p for q,p in lines) * (100-discount) // 100
