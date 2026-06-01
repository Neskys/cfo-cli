"""AI-powered financial insights via the Anthropic SDK (optional [ai] extra).

Only aggregated data is sent to Claude — never individual transaction rows.
The financial-context block is cached (prompt caching) so repeated calls within
a session reuse it cheaply.
"""

from cfo.core.config import get_api_key, get_base_currency

DEFAULT_MODEL = "claude-sonnet-4-6"

VALID_FOCUS = ("expenses", "income", "cashflow", "all")
VALID_GOALS = ("reduce-expenses", "increase-cashflow", "optimize-categories")

SYSTEM_PROMPT = (
    "You are a pragmatic CFO assistant for a freelancer or small team. "
    "You are given aggregated financial data (totals and breakdowns, never individual "
    "transactions). Base your answers strictly on that data, quantify with the figures "
    "provided, and be concise and actionable. If the data is empty or insufficient, say so."
)


class AIError(Exception):
    """Validation, configuration, or API failure surfaced to the CLI cleanly."""


def _client(api_key: str):
    try:
        import anthropic
    except ImportError:
        raise AIError("AI features need the 'anthropic' package. Install: pip install 'cfo-cli[ai]'")
    return anthropic.Anthropic(api_key=api_key)


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
    api_key = get_api_key()
    if not api_key:
        raise AIError("No API key configured. Run: cfo ai config --api-key sk-...")
    client = _client(api_key)
    # Stable instructions + cached context block; the volatile question goes in messages.
    system = [
        {"type": "text", "text": SYSTEM_PROMPT},
        {"type": "text", "text": context, "cache_control": {"type": "ephemeral"}},
    ]
    try:
        resp = client.messages.create(
            model=DEFAULT_MODEL,
            max_tokens=max_tokens,
            system=system,
            messages=[{"role": "user", "content": question}],
        )
    except AIError:
        raise
    except Exception as e:
        raise AIError(f"AI request failed: {e}")
    return "".join(b.text for b in resp.content if getattr(b, "type", None) == "text").strip()


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
