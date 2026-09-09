import privilege_analyzer
from access_parser import parse_access_file
from finding import Severity
from helpers import record, write_csv


def analyze(tmp_path, rows):
    path = write_csv(tmp_path / "in.csv", rows)
    return privilege_analyzer.analyze(parse_access_file(path))


def test_lone_admin_among_standard_peers_flagged_outlier(tmp_path):
    rows = [
        record(email="a@example.com", permission="Admin"),
        record(email="b@example.com", permission="Standard User"),
        record(email="c@example.com", permission="Standard User"),
    ]
    findings = analyze(tmp_path, rows)
    codes = [f.code for f in findings]
    assert "PRIVILEGE_OUTLIER" in codes
    f = next(f for f in findings if f.code == "PRIVILEGE_OUTLIER")
    assert f.subject == "a@example.com"
    assert f.severity == Severity.HIGH


def test_group_below_minimum_size_not_checked(tmp_path):
    rows = [
        record(email="a@example.com", permission="Admin"),
        record(email="b@example.com", permission="Standard User"),
    ]
    findings = analyze(tmp_path, rows)
    assert findings == []


def test_all_standard_no_outlier(tmp_path):
    rows = [
        record(email="a@example.com", permission="Standard User"),
        record(email="b@example.com", permission="Standard User"),
        record(email="c@example.com", permission="Standard User"),
    ]
    findings = analyze(tmp_path, rows)
    assert findings == []


def test_all_admin_no_outlier_but_concentration_flagged(tmp_path):
    rows = [
        record(email="a@example.com", permission="Admin"),
        record(email="b@example.com", permission="Admin"),
        record(email="c@example.com", permission="Admin"),
    ]
    findings = analyze(tmp_path, rows)
    codes = [f.code for f in findings]
    assert "PRIVILEGE_OUTLIER" not in codes
    assert "ADMIN_CONCENTRATION" in codes


def test_admin_concentration_below_threshold_not_flagged(tmp_path):
    rows = [
        record(email="a@example.com", permission="Admin", department="IT", system="X"),
        record(email="b@example.com", permission="Standard User", department="IT", system="X"),
        record(email="c@example.com", permission="Standard User", department="IT", system="X"),
        record(email="d@example.com", permission="Standard User", department="IT", system="X"),
        record(email="e@example.com", permission="Standard User", department="IT", system="X"),
    ]
    findings = analyze(tmp_path, rows)
    codes = [f.code for f in findings]
    assert "ADMIN_CONCENTRATION" not in codes


def test_admin_concentration_at_threshold_flagged(tmp_path):
    rows = [
        record(email="a@example.com", permission="Admin", department="IT", system="X"),
        record(email="b@example.com", permission="Standard User", department="IT", system="X"),
        record(email="c@example.com", permission="Standard User", department="Sales", system="X"),
    ]
    findings = analyze(tmp_path, rows)
    f = next(f for f in findings if f.code == "ADMIN_CONCENTRATION")
    assert f.evidence["system"] == "X"
    assert f.evidence["total_count"] == 3


def test_terminated_accounts_excluded(tmp_path):
    rows = [
        record(email="a@example.com", permission="Admin", employee_status="Terminated"),
        record(email="b@example.com", permission="Standard User"),
        record(email="c@example.com", permission="Standard User"),
    ]
    findings = analyze(tmp_path, rows)
    assert findings == []


def test_outlier_grouped_by_department_and_system(tmp_path):
    rows = [
        record(email="a@example.com", permission="Admin", department="Sales", system="CRM"),
        record(email="b@example.com", permission="Standard User", department="Sales", system="CRM"),
        record(email="c@example.com", permission="Standard User", department="Sales", system="CRM"),
        # Different system, should not affect the CRM group above
        record(email="d@example.com", permission="Admin", department="Sales", system="Email"),
        record(email="e@example.com", permission="Admin", department="Sales", system="Email"),
    ]
    findings = analyze(tmp_path, rows)
    outlier_subjects = [f.subject for f in findings if f.code == "PRIVILEGE_OUTLIER"]
    assert outlier_subjects == ["a@example.com"]


def test_admin_concentration_lists_privileged_users_in_evidence(tmp_path):
    rows = [
        record(email="a@example.com", permission="Admin", department="IT", system="X"),
        record(email="b@example.com", permission="Admin", department="IT", system="X"),
        record(email="c@example.com", permission="Standard User", department="Sales", system="X"),
    ]
    findings = analyze(tmp_path, rows)
    f = next(f for f in findings if f.code == "ADMIN_CONCENTRATION")
    assert set(f.evidence["privileged_users"]) == {"a@example.com", "b@example.com"}
