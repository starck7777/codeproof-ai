def solve(text):
    result = {}
    for part in text.split(";"):
        if not part.strip():
            continue
        if "=" not in part:
            raise ValueError("missing equals")
        k, v = part.split("=", 1)
        result[k.strip()] = v.strip()
    return result
