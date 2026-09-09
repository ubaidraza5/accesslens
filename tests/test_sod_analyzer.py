import sod_analyzer
from access_parser import parse_access_file
from finding import Severity
from helpers import record, write_csv


def analyze(tmp_path, rows):
    path = write_csv(tmp_path / "in.csv", rows)
    return sod_analyzer.analyze(parse_access_file(path))


def test_known_conflict_pair_flagged(tmp_path):
    rows = [
        record(email="a@example.com", permission="Payment Processor"),
        record(email="a@example.com", permission="Payment Approver"),
    ]
    findings = analyze(tmp_path, rows)
    assert len(findings) == 1
    assert findings[0].code == "SOD_CONFLICT"
    assert findings[0].severity == Severity.CRITICAL
    assert findings[0].subject == "a@example.com"


def test_conflict_pair_order_does_not_matter(tmp_path):
    rows = [
        record(email="a@example.com", permission="Payment Approver"),
        record(email="a@example.com", permission="Payment Processor"),
    ]
    findings = analyze(tmp_path, rows)
    assert len(findings) == 1


def test_non_conflicting_permissions_not_flagged(tmp_path):
    rows = [
        record(email="a@example.com", permission="Standard User"),
        record(email="a@example.com", permission="Report Viewer"),
    ]
    findings = analyze(tmp_path, rows)
    assert findings == []


def test_single_permission_not_flagged(tmp_path):
    rows = [record(email="a@example.com", permission="Payment Processor")]
    findings = analyze(tmp_path, rows)
    assert findings == []


def test_conflict_across_different_people_not_flagged(tmp_path):
    rows = [
        record(email="a@example.com", permission="Payment Processor"),
        record(email="b@example.com", permission="Payment Approver"),
    ]
    findings = analyze(tmp_path, rows)
    assert findings == []


def test_terminated_person_excluded(tmp_path):
    rows = [
        record(
            email="a@example.com",
            permission="Payment Processor",
            employee_status="Terminated",
        ),
        record(
            email="a@example.com",
            permission="Payment Approver",
            employee_status="Terminated",
        ),
    ]
    findings = analyze(tmp_path, rows)
    assert findings == []


def test_all_known_conflict_pairs_are_detected(tmp_path):
    pairs = [
        ("Payment Processor", "Payment Approver"),
        ("Invoice Creator", "Invoice Approver"),
        ("Vendor Setup", "Payment Approver"),
        ("User Provisioner", "Access Approver"),
        ("Code Deploy", "Code Review Approver"),
        ("Payroll Processor", "Payroll Approver"),
        ("Purchase Requester", "Purchase Approver"),
    ]
    for i, (a, b) in enumerate(pairs):
        rows = [
            record(email=f"p{i}@example.com", permission=a),
            record(email=f"p{i}@example.com", permission=b),
        ]
        findings = analyze(tmp_path, rows)
        assert len(findings) == 1, f"expected a conflict for {a} + {b}"


def test_evidence_lists_affected_systems(tmp_path):
    rows = [
        record(email="a@example.com", permission="Payment Processor", system="ERP"),
        record(email="a@example.com", permission="Payment Approver", system="ERP"),
    ]
    findings = analyze(tmp_path, rows)
    assert findings[0].evidence["systems"] == ["ERP"]


def test_three_way_permissions_only_flags_the_conflicting_pair(tmp_path):
    rows = [
        record(email="a@example.com", permission="Payment Processor"),
        record(email="a@example.com", permission="Payment Approver"),
        record(email="a@example.com", permission="Report Viewer"),
    ]
    findings = analyze(tmp_path, rows)
    assert len(findings) == 1
