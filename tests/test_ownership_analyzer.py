from datetime import date

import ownership_analyzer
from access_parser import parse_access_file
from finding import Severity
from helpers import record, write_csv

AS_OF = date(2026, 9, 9)


def analyze(tmp_path, rows):
    path = write_csv(tmp_path / "in.csv", rows)
    return ownership_analyzer.analyze(parse_access_file(path), AS_OF)


def test_missing_manager_flagged(tmp_path):
    findings = analyze(tmp_path, [record(manager="")])
    codes = [f.code for f in findings]
    assert "NO_MANAGER_LISTED" in codes


def test_missing_manager_severity_is_medium(tmp_path):
    findings = analyze(tmp_path, [record(manager="")])
    f = next(f for f in findings if f.code == "NO_MANAGER_LISTED")
    assert f.severity == Severity.MEDIUM


def test_manager_present_not_flagged_for_ownership(tmp_path):
    findings = analyze(
        tmp_path, [record(manager="Someone", date_granted="2026-08-01")]
    )
    codes = [f.code for f in findings]
    assert "NO_MANAGER_LISTED" not in codes


def test_terminated_account_skipped_entirely(tmp_path):
    findings = analyze(
        tmp_path,
        [record(manager="", employee_status="Terminated")],
    )
    assert findings == []


def test_recent_grant_not_flagged_for_recertification(tmp_path):
    findings = analyze(tmp_path, [record(date_granted="2026-08-01")])
    codes = [f.code for f in findings]
    assert "RECERTIFICATION_OVERDUE" not in codes


def test_old_grant_flagged_for_recertification(tmp_path):
    findings = analyze(tmp_path, [record(date_granted="2024-01-01")])
    codes = [f.code for f in findings]
    assert "RECERTIFICATION_OVERDUE" in codes


def test_recertification_severity_is_low(tmp_path):
    findings = analyze(tmp_path, [record(date_granted="2024-01-01")])
    f = next(f for f in findings if f.code == "RECERTIFICATION_OVERDUE")
    assert f.severity == Severity.LOW


def test_can_produce_both_findings_at_once(tmp_path):
    findings = analyze(
        tmp_path,
        [record(manager="", date_granted="2024-01-01")],
    )
    codes = {f.code for f in findings}
    assert codes == {"NO_MANAGER_LISTED", "RECERTIFICATION_OVERDUE"}


def test_clean_record_produces_no_findings(tmp_path):
    findings = analyze(
        tmp_path,
        [record(manager="Someone", date_granted="2026-08-01")],
    )
    assert findings == []
