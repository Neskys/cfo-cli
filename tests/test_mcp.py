"""Tests for the MCP server commands and services."""

from typer.testing import CliRunner

from cfo.cli.main import app
from cfo.core.config import set_mcp_read_write, get_mcp_read_write
from cfo.services import mcp_server
from cfo.services.budget import create_budget
from cfo.services.expense import add_expense
from cfo.storage.database import get_connection, init_db

runner = CliRunner()


def test_mcp_config(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))

    # Check default config is read-only
    assert get_mcp_read_write() is False

    # Toggle read-write
    result = runner.invoke(app, ["mcp", "config", "--read-write"])
    assert result.exit_code == 0
    assert get_mcp_read_write() is True

    # Toggle back to read-only
    result = runner.invoke(app, ["mcp", "config", "--read-only"])
    assert result.exit_code == 0
    assert get_mcp_read_write() is False


def test_mcp_start_readonly_mode_by_default(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))

    # Mock start_server so we don't start the actual blocking stdio loop
    monkeypatch.setattr(mcp_server, "start_server", lambda: None)

    result = runner.invoke(app, ["mcp", "start"])
    assert result.exit_code == 0
    assert "Read-Only mode" in result.output
    assert mcp_server.WRITE_ALLOWED is False


def test_mcp_start_readwrite_mode_via_flag(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))

    monkeypatch.setattr(mcp_server, "start_server", lambda: None)

    result = runner.invoke(app, ["mcp", "start", "--read-write"])
    assert result.exit_code == 0
    assert "Write access is enabled" in result.output
    assert mcp_server.WRITE_ALLOWED is True


def test_mcp_read_tools(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    init_db()

    # Pre-seed some data
    create_budget("Q3 2026", "quarterly")
    add_expense("software", 49.99, "EUR", budget_name="Q3 2026", note="Adobe")

    # Test expense_list tool
    res = mcp_server.expense_list(category="software")
    assert "49.99" in res
    assert "Software" in res
    assert "Adobe" in res

    # Test expense_summary tool
    res = mcp_server.expense_summary(budget_name="Q3 2026")
    assert "49.99" in res
    assert "Software" in res

    # Test budget tools
    res = mcp_server.budget_list()
    assert "Q3 2026" in res

    res = mcp_server.budget_view("Q3 2026")
    assert "Q3 2026" in res


def test_mcp_write_tools_safeguards(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    init_db()

    # Ensure write is disabled
    monkeypatch.setattr(mcp_server, "WRITE_ALLOWED", False)
    set_mcp_read_write(False)

    # Adding expense should fail
    res = mcp_server.expense_add(category="office", amount=15.0)
    assert "Error" in res
    assert "Write access is disabled" in res

    # Enable write access
    monkeypatch.setattr(mcp_server, "WRITE_ALLOWED", True)

    # Adding expense should now succeed
    res = mcp_server.expense_add(category="office", amount=15.0)
    assert "Success" in res
    assert "office" in res
    assert "15.00" in res

    # Verify DB entry was written
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM expenses WHERE category = 'office'").fetchone()
    assert row is not None
    assert row["amount"] == 15.0
