"""AI-powered financial insights via Claude or OpenAI (optional [ai] / [openai] extras).

Only aggregated data is sent to the model — never individual transaction rows.
The financial-context block is sent first so it is cached cheaply (Anthropic prompt
caching / OpenAI automatic prefix caching). Provider-specific calls live in ai_providers.
"""

from cfo.core.config import get_api_key, get_base_currency, get_provider, get_ai_model
from cfo.services.ai_providers import AIError, complete, PROVIDER_DEFAULT_MODEL, VALID_PROVIDERS

__all__ = ["AIError", "VALID_PROVIDERS", "VALID_FOCUS", "VALID_GOALS",
           "analyze", "anomalies", "suggest", "build_context"]

VALID_FOCUS = ("expenses", "income", "cashflow", "all")
VALID_GOALS = ("reduce-expenses", "increase-cashflow", "optimize-categories")

SYSTEM_PROMPT = (
    "You are a pragmatic CFO assistant for a freelancer or small team. "
    "You are given aggregated financial data (totals and breakdowns, never individual "
    "transactions). Base your answers strictly on that data, quantify with the figures "
    "provided, and be concise and actionable. If the data is empty or insufficient, say so."
)


def _fmt(rows) -> str:
    return "\n".join(f"  {r['key']}: {r['amount']:.2f} ({r['pct']:.1f}%)" for r in rows) or "  (none)"


def build_context(date_from=None, date_to=None) -> str:
    """Build a deterministic, aggregated financial-context block (no raw rows)."""
    from cfo.services import expense, income, forecast

    exp_cat = expense.summary(date_from, date_to, "category")
    exp_mon = expense.summary(date_from, date_to, "month")
    inc_src = income.summary(date_from, date_to, "source")
    inc_mon = income.summary(date_from, date_to, "month")
    parts = [
        "AGGREGATED FINANCIAL DATA (no individual transactions)",
        f"Base currency: {get_base_currency()}",
        f"Total expenses: {exp_cat['total']:.2f} | Total income: {inc_src['total']:.2f}",
        "\nExpenses by category:", _fmt(exp_cat["rows"]),
        "\nExpenses by month:", _fmt(exp_mon["rows"]),
        "\nIncome by source:", _fmt(inc_src["rows"]),
        "\nIncome by month:", _fmt(inc_mon["rows"]),
    ]
    try:
        fc = forecast.run(months=6, scenario="base")
        lines = "\n".join(f"  {r['month']}: net {r['net']:.2f}, balance {r['balance']:.2f}" for r in fc["rows"])
        parts += [
            f"\n6-month forecast (base): monthly income {fc['monthly_income']:.2f}, "
            f"monthly expense {fc['monthly_expense']:.2f}",
            lines,
        ]
    except Exception:
        pass
    return "\n".join(parts)


def _complete(context: str, question: str, max_tokens: int = 2048) -> str:
    provider = get_provider()
    api_key = get_api_key(provider)
    if not api_key:
        raise AIError(
            f"No API key for provider '{provider}'. "
            f"Run: cfo ai config --api-key ... --provider {provider}"
        )
    model = get_ai_model(provider) or PROVIDER_DEFAULT_MODEL[provider]
    return complete(provider, api_key, model, SYSTEM_PROMPT, context, question, max_tokens)


def analyze(focus: str = "all", date_from=None, date_to=None) -> str:
    if focus not in VALID_FOCUS:
        raise AIError(f"Invalid focus '{focus}'. Choose from: {', '.join(VALID_FOCUS)}")
    scope = "all areas" if focus == "all" else focus
    question = (
        f"Analyze my finances focusing on {scope}. Highlight the largest drivers, notable "
        "trends across months, and the overall financial health. Keep it under 250 words."
    )
    return _complete(build_context(date_from, date_to), question)


def anomalies(threshold: float = 2.0, date_from=None, date_to=None) -> str:
    if threshold <= 0:
        raise AIError("--threshold must be greater than zero.")
    question = (
        f"Using the monthly series above, identify anomalies: months whose expenses or income "
        f"deviate from the mean by more than {threshold} standard deviations (z-score). "
        "List each anomaly with the month, the figure, and a brief likely explanation. "
        "If none exceed the threshold, say so explicitly."
    )
    return _complete(build_context(date_from, date_to), question)


def suggest(goal: str = "reduce-expenses", date_from=None, date_to=None) -> str:
    if goal not in VALID_GOALS:
        raise AIError(f"Invalid goal '{goal}'. Choose from: {', '.join(VALID_GOALS)}")
    question = (
        f"Suggest 3-5 concrete, prioritized actions to {goal.replace('-', ' ')}, grounded in the "
        "data above. For each, reference the relevant figure and the expected impact."
    )
    return _complete(build_context(date_from, date_to), question)
