def solve(lines, discount):
    return sum(q * p * (100-discount) // 100 for q, p in lines)
