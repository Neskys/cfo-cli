"""Exchange-rate fetching, 24h SQLite cache, and conversion helpers.

Rates come from open.er-api.com (free, no key). Fetched rates are cached for 24h;
if the network is unavailable, a stale cached rate is used as a fallback.
"""

from datetime import datetime, timedelta

from cfo.storage.database import get_connection, init_db

API_URL = "https://open.er-api.com/v6/latest/{base}"
CACHE_TTL = timedelta(hours=24)


class CurrencyError(Exception):
    """Validation, fetch, or lookup failure surfaced to the CLI as a clean message."""


def _fetch_rates(base: str) -> dict:
    """Fetch the latest rates for `base` from the API. Network call."""
    try:
        import httpx

        resp = httpx.get(API_URL.format(base=base), timeout=10.0)
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:  # import / network / HTTP / JSON errors
        raise CurrencyError(f"Failed to fetch exchange rates: {e}")
    if data.get("result") != "success":
        raise CurrencyError(f"Rate API error: {data.get('error-type', 'unknown')}")
    return data["rates"]


def refresh_rates(base: str) -> dict:
    """Fetch rates for `base` and store them in the cache."""
    base = base.upper()
    rates = _fetch_rates(base)
    now = datetime.utcnow().isoformat(sep=" ", timespec="seconds")
    init_db()
    with get_connection() as conn:
        conn.executemany(
            "INSERT OR REPLACE INTO exchange_rates "
            "(base_currency, quote_currency, rate, fetched_at) VALUES (?, ?, ?, ?)",
            [(base, q.upper(), float(r), now) for q, r in rates.items()],
        )
    return rates


def _ensure_rates(base: str, refresh: bool = False) -> None:
    """Refresh the cache for `base` if missing or older than the TTL.

    On a failed fetch, keep any existing (stale) cache as an offline fallback.
    """
    init_db()
    with get_connection() as conn:
        latest = conn.execute(
            "SELECT MAX(fetched_at) AS f FROM exchange_rates WHERE base_currency = ?", (base,)
        ).fetchone()["f"]
    fresh = latest and (datetime.utcnow() - datetime.fromisoformat(latest) < CACHE_TTL)
    if refresh or not fresh:
        try:
            refresh_rates(base)
        except CurrencyError:
            if latest is None:
                raise CurrencyError(
                    f"No exchange rates for {base} and unable to fetch them (offline?)."
                )


def get_rate(from_cur: str, to_cur: str, refresh: bool = False) -> float:
    from_cur, to_cur = from_cur.upper(), to_cur.upper()
    if from_cur == to_cur:
        return 1.0
    _ensure_rates(from_cur, refresh)
    with get_connection() as conn:
        row = conn.execute(
            "SELECT rate FROM exchange_rates WHERE base_currency = ? AND quote_currency = ?",
            (from_cur, to_cur),
        ).fetchone()
    if not row:
        raise CurrencyError(f"No exchange rate available for {from_cur} → {to_cur}.")
    return row["rate"]


def convert(amount: float, from_cur: str, to_cur: str, refresh: bool = False) -> float:
    return amount * get_rate(from_cur, to_cur, refresh)


def get_all_rates(base: str, refresh: bool = False):
    base = base.upper()
    _ensure_rates(base, refresh)
    with get_connection() as conn:
        return conn.execute(
            "SELECT quote_currency, rate, fetched_at FROM exchange_rates "
            "WHERE base_currency = ? ORDER BY quote_currency",
            (base,),
        ).fetchall()


def to_base_rows(rows, base: str, amount_field="amount", currency_field="currency"):
    """Return rows as dicts with amounts converted to `base` (currency set to base)."""
    out = []
    for r in rows:
        d = dict(r)
        d[amount_field] = convert(d[amount_field], d[currency_field], base)
        d[currency_field] = base
        out.append(d)
    return out


def collapse_to_base(grouped, base: str) -> dict:
    """Collapse rows (key, currency, amount, count) into {key: (amount_in_base, count)}."""
    acc: dict = {}
    for r in grouped:
        amount, count = acc.get(r["key"], (0.0, 0))
        acc[r["key"]] = (amount + convert(r["amount"], r["currency"], base), count + r["count"])
    return acc
