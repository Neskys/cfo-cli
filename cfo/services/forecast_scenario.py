"""Custom forecast scenario and adjustment CRUD."""

from datetime import date as date_cls

from cfo.storage.database import get_connection, init_db
from cfo.core.models import VALID_ADJUSTMENT_TYPES
from cfo.services.forecast import ForecastError


def _validate_date(value: str) -> None:
    try:
        date_cls.fromisoformat(value)
    except ValueError:
        raise ForecastError(f"Invalid date '{value}'. Use YYYY-MM-DD format.")


def create_scenario(name, period_from, period_to) -> int:
    _validate_date(period_from)
    _validate_date(period_to)
    if period_to < period_from:
        raise ForecastError("--to must not be earlier than --from.")
    init_db()
    with get_connection() as conn:
        if conn.execute("SELECT id FROM forecast_scenarios WHERE name = ?", (name,)).fetchone():
            raise ForecastError(f"Scenario '{name}' already exists.")
        cur = conn.execute(
            "INSERT INTO forecast_scenarios (name, period_from, period_to) VALUES (?, ?, ?)",
            (name, period_from, period_to),
        )
        return cur.lastrowid


def list_scenarios():
    init_db()
    with get_connection() as conn:
        return conn.execute(
            "SELECT s.*, COUNT(a.id) AS adjustments FROM forecast_scenarios s "
            "LEFT JOIN forecast_adjustments a ON a.scenario_id = s.id "
            "GROUP BY s.id ORDER BY s.created_at DESC"
        ).fetchall()


def get_scenario(scenario_id: int) -> dict:
    init_db()
    with get_connection() as conn:
        scenario = conn.execute(
            "SELECT * FROM forecast_scenarios WHERE id = ?", (scenario_id,)
        ).fetchone()
        if not scenario:
            raise ForecastError(f"Scenario #{scenario_id} not found.")
        adjustments = conn.execute(
            "SELECT * FROM forecast_adjustments WHERE scenario_id = ? ORDER BY id",
            (scenario_id,),
        ).fetchall()
    return {"scenario": scenario, "adjustments": adjustments}


def delete_scenario(scenario_id: int) -> None:
    init_db()
    with get_connection() as conn:
        if not conn.execute(
            "SELECT id FROM forecast_scenarios WHERE id = ?", (scenario_id,)
        ).fetchone():
            raise ForecastError(f"Scenario #{scenario_id} not found.")
        conn.execute("DELETE FROM forecast_adjustments WHERE scenario_id = ?", (scenario_id,))
        conn.execute("DELETE FROM forecast_scenarios WHERE id = ?", (scenario_id,))


def add_adjustment(scenario_id, adj_type, category=None, factor=None, absolute_delta=None, note=None) -> int:
    adj_type = adj_type.lower()
    if adj_type not in VALID_ADJUSTMENT_TYPES:
        raise ForecastError(
            f"Invalid type '{adj_type}'. Choose from: {', '.join(VALID_ADJUSTMENT_TYPES)}"
        )
    if factor is None and absolute_delta is None:
        raise ForecastError("Provide at least --factor or --absolute-delta.")
    init_db()
    with get_connection() as conn:
        if not conn.execute(
            "SELECT id FROM forecast_scenarios WHERE id = ?", (scenario_id,)
        ).fetchone():
            raise ForecastError(f"Scenario #{scenario_id} not found.")
        cur = conn.execute(
            "INSERT INTO forecast_adjustments "
            "(scenario_id, type, category, factor, absolute_delta, note) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (scenario_id, adj_type, category, factor, absolute_delta, note),
        )
        return cur.lastrowid
