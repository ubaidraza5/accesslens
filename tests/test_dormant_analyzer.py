from datetime import date

import dormant_analyzer
from access_parser import parse_access_file
from finding import Severity
from helpers import record, write_csv

AS_OF = date(2026, 9, 9)


def analyze(tmp_path, rows):
    path = write_csv(tmp_path / "in.csv", rows)
    return dormant_analyzer.analyze(parse_access_file(path), AS_OF)


def test_terminated_with_access_flagged_critical_when_privileged(tmp_path):
    findings = analyze(
        tmp_path,
        [record(employee_status="Terminated", permission="Admin")],
    )
    codes = [f.code for f in findings]
    assert "ORPHANED_TERMINATED_ACCESS" in codes
    f = next(f for f in findings if f.code == "ORPHANED_TERMINATED_ACCESS")
    assert f.severity == Severity.CRITICAL


def test_terminated_with_standard_access_flagged_high(tmp_path):
    findings = analyze(
        tmp_path,
        [record(employee_status="Terminated", permission="Standard User")],
    )
    f = next(f for f in findings if f.code == "ORPHANED_TERMINATED_ACCESS")
    assert f.severity == Severity.HIGH


def test_terminated_finding_has_email_as_subject(tmp_path):
    findings = analyze(
        tmp_path,
        [record(employee_status="Terminated", email="gone@example.com")],
    )
    f = findings[0]
    assert f.subject == "gone@example.com"


def test_active_account_recently_used_not_flagged(tmp_path):
    findings = analyze(
        tmp_path,
        [record(employee_status="Active", date_last_used="2026-09-01")],
    )
    assert findings == []


def test_dormant_account_flagged(tmp_path):
    findings = analyze(
        tmp_path,
        [record(employee_status="Active", date_last_used="2026-03-01")],
    )
    codes = [f.code for f in findings]
    assert "DORMANT_ACCOUNT" in codes


def test_dormant_privileged_account_is_high_severity(tmp_path):
    findings = analyze(
        tmp_path,
        [
            record(
                employee_status="Active",
                date_last_used="2026-03-01",
                permission="Admin",
            )
        ],
    )
    f = next(f for f in findings if f.code == "DORMANT_ACCOUNT")
    assert f.severity == Severity.HIGH


def test_dormant_standard_account_is_medium_severity(tmp_path):
    findings = analyze(
        tmp_path,
        [
            record(
                employee_status="Active",
                date_last_used="2026-03-01",
                permission="Standard User",
            )
        ],
    )
    f = next(f for f in findings if f.code == "DORMANT_ACCOUNT")
    assert f.severity == Severity.MEDIUM


def test_just_under_dormant_threshold_not_flagged(tmp_path):
    # 89 days before AS_OF, one day short of the 90 day threshold
    findings = analyze(
        tmp_path,
        [record(employee_status="Active", date_last_used="2026-06-12")],
    )
    codes = [f.code for f in findings]
    assert "DORMANT_ACCOUNT" not in codes


def test_never_used_recent_grant_not_flagged(tmp_path):
    findings = analyze(
        tmp_path,
        [
            record(
                employee_status="Active",
                date_granted="2026-09-01",
                date_last_used="",
            )
        ],
    )
    assert findings == []


def test_never_used_old_grant_flagged(tmp_path):
    findings = analyze(
        tmp_path,
        [
            record(
                employee_status="Active",
                date_granted="2026-06-01",
                date_last_used="",
            )
        ],
    )
    codes = [f.code for f in findings]
    assert "NEVER_USED_ACCOUNT" in codes


def test_never_used_finding_has_evidence(tmp_path):
    findings = analyze(
        tmp_path,
        [
            record(
                employee_status="Active",
                date_granted="2026-06-01",
                date_last_used="",
            )
        ],
    )
    f = findings[0]
    assert "days_since_grant" in f.evidence


def test_clean_records_produce_no_findings(tmp_path):
    findings = analyze(
        tmp_path,
        [
            record(email="a@example.com", date_last_used="2026-09-01"),
            record(email="b@example.com", date_last_used="2026-08-15"),
        ],
    )
    assert findings == []
