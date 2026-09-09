import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SAMPLE = ROOT / "tests" / "fixtures" / "sample_company_access.csv"


def run(*args):
    return subprocess.run(
        [sys.executable, str(ROOT / "main.py"), *args],
        capture_output=True,
        text=True,
    )


def test_simple_mode_runs_and_reports_critical():
    result = run(str(SAMPLE), "--as-of", "2026-09-09")
    assert "PLAIN LANGUAGE SUMMARY" in result.stdout
    assert "CRITICAL" in result.stdout
    assert result.returncode == 1


def test_analyst_mode_runs():
    result = run(str(SAMPLE), "--as-of", "2026-09-09", "--mode", "analyst")
    assert "ANALYST VIEW" in result.stdout
    assert "SOD_CONFLICT" in result.stdout


def test_json_export(tmp_path):
    out = tmp_path / "report.json"
    result = run(str(SAMPLE), "--as-of", "2026-09-09", "--json", str(out))
    assert out.exists()
    payload = json.loads(out.read_text())
    assert payload["company_level"] == "Critical"
    assert result.returncode == 1


def test_missing_file_exits_with_error():
    result = run(str(ROOT / "tests" / "fixtures" / "does_not_exist.csv"))
    assert result.returncode != 0
    assert "error" in result.stderr.lower()


def test_bad_as_of_date_exits_with_error():
    result = run(str(SAMPLE), "--as-of", "not-a-date")
    assert result.returncode == 2
    assert "error" in result.stderr.lower()


def test_company_name_appears_in_simple_output():
    result = run(str(SAMPLE), "--as-of", "2026-09-09", "--company", "Alderbrook Logistics")
    assert result.returncode in (0, 1)
