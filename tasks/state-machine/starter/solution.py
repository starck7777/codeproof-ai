def solve(events):
    state = "draft"
    for event in events:
        state = event
    return state
