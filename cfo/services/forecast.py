"""Cash-flow forecasting algorithm. CLI only parses args and calls this."""

from datetime import date as date_cls

from cfo.services import income, expense
from cfo.services.income_source import list_sources


# scenario name -> (income factor, expense factor)
SCENARIO_FACTORS = {
    "base": (1.0, 1.0),
    "optimist": (1.2, 0.9),
    "pessimist": (0.8, 1.1),
}


class ForecastError(Exception):
    """Validation or lookup failure surfaced to the CLI as a clean message."""


def _projected_monthly_income(window: int = 6) -> float:
    """Sum of average monthly income across recurring sources (last `window` months)."""
    total = 0.0
    for s in list_sources():
        if s["is_recurring"]:
            total += income.get_monthly_average(s["id"], months=window)
    return total


def run(months: int = 6, scenario: str = "base") -> dict:
    """Project cash flow forward `months` months using a built-in scenario."""
    if scenario not in SCENARIO_FACTORS:
        raise ForecastError(
            f"Unknown scenario '{scenario}'. Choose from: {', '.join(SCENARIO_FACTORS)}"
        )
    if months <= 0:
        raise ForecastError("--months must be greater than zero.")
    inc_factor, exp_factor = SCENARIO_FACTORS[scenario]
    monthly_income = _projected_monthly_income(6) * inc_factor
    monthly_expense = expense.get_monthly_average(3) * exp_factor
    rows, balance = [], 0.0
    today = date_cls.today()
    year, month = today.year, today.month
    for _ in range(months):
        net = monthly_income - monthly_expense
        balance += net
        rows.append(
            {
                "month": f"{year:04d}-{month:02d}",
                "income": monthly_income,
                "expense": monthly_expense,
                "net": net,
                "balance": balance,
            }
        )
        month += 1
        if month > 12:
            month, year = 1, year + 1
    return {
        "scenario": scenario,
        "monthly_income": monthly_income,
        "monthly_expense": monthly_expense,
        "rows": rows,
    }
