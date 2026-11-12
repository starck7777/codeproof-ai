def solve(text):
    return dict(part.split("=") for part in text.split(";"))
