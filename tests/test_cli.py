from typer.testing import CliRunner

from pg_researcher.cli import app

runner = CliRunner()


def test_version_command() -> None:
    result = runner.invoke(app, ["version"])
    assert result.exit_code == 0
    assert result.stdout.strip() == "0.4.0"


def test_sources_validate_command() -> None:
    result = runner.invoke(app, ["sources", "validate"])
    assert result.exit_code == 0
    assert "valid:" in result.stdout


def test_sources_json_output() -> None:
    result = runner.invoke(app, ["sources", "list", "--json"])
    assert result.exit_code == 0
    assert '"id": "x_princeguttreal"' in result.stdout


def test_claim_validate_command() -> None:
    result = runner.invoke(app, ["claim", "validate", "examples/claims/minimal.json"])
    assert result.exit_code == 0
    assert "valid claim:" in result.stdout


def test_report_plan_validate_command() -> None:
    result = runner.invoke(app, ["report", "plan-validate", "examples/reporting/plan.json"])
    assert result.exit_code == 0
    assert "valid report plan:" in result.stdout


def test_report_validate_command() -> None:
    result = runner.invoke(app, ["report", "validate", "examples/reports/minimal.json"])
    assert result.exit_code == 0
    assert "valid report:" in result.stdout
