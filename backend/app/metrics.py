import math
import statistics


def aggregate(attempts):
    valid = [
        a for a in attempts if a.get("evaluation") and a.get("failure_category") != "infrastructure"
    ]
    wins = sum(a["evaluation"]["success"] for a in valid)
    durations = sorted(a.get("duration", 0) for a in valid)
    costs = [a.get("cost") for a in valid]
    cost = sum(costs) if costs and all(c is not None for c in costs) else None
    tokens = [a.get("tokens") for a in valid]
    hidden_total = sum(a["evaluation"]["hidden"]["total"] for a in valid)
    return {
        "valid": len(valid),
        "successes": wins,
        "success_rate": wins / len(valid) if valid else None,
        "hidden_pass_rate": sum(a["evaluation"]["hidden"]["passed"] for a in valid) / hidden_total
        if hidden_total
        else None,
        "regression_free_rate": sum(
            a["evaluation"]["regression"]["passed"] == a["evaluation"]["regression"]["total"]
            for a in valid
        )
        / len(valid)
        if valid
        else None,
        "median_duration": statistics.median(durations) if durations else None,
        "p95_duration": durations[max(0, math.ceil(0.95 * len(durations)) - 1)]
        if durations
        else None,
        "total_cost": cost,
        "cost_per_success": cost / wins if cost is not None and wins else None,
        "total_tokens": sum(tokens) if tokens and all(t is not None for t in tokens) else None,
        "infrastructure_failures": sum(
            a.get("failure_category") == "infrastructure" for a in attempts
        ),
    }


def price(usage, pricing):
    if usage is None or pricing is None:
        return None
    return (
        usage["prompt_tokens"] * pricing["input_per_million"]
        + usage["completion_tokens"] * pricing["output_per_million"]
    ) / 1_000_000
