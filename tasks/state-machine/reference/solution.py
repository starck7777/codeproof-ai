def solve(events):
    allowed = {"draft": {"paid", "cancelled"}, "paid": {"shipped", "cancelled"}, "shipped": {"delivered"}, "delivered": set(), "cancelled": set()}
    state = "draft"
    for event in events:
        if event != state and event not in allowed[state]:
            raise ValueError("invalid transition")
        state = event
    return state
