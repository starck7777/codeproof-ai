def solve(quantity, price):
    if type(quantity) is not int or quantity <= 0 or price < 0:
        raise ValueError("invalid")
    return quantity * price
