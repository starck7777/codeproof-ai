from datetime import datetime
def solve(value):
    return int(datetime.fromisoformat(value).replace(tzinfo=None).timestamp())
