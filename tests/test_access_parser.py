from datetime import date

import pytest

from access_parser import AccessFileError, parse_access_file
from helpers import record, write_csv


def test_parses_valid_rows(tmp_path):
    path = write_csv(tmp_path / "in.csv", [record()])
    records = parse_access_file(path)
    assert len(records) == 1
    r = records[0]
    assert r.name == "Test Person"
    assert r.email == "test.person@example.com"
    assert r.department == "Finance"
    assert r.system == "Finance ERP"
    assert r.permission == "Standard User"
    assert r.date_granted == date(2025, 1, 1)
    assert r.date_last_used == date(2026, 8, 1)
    assert r.employee_status == "Active"
    assert r.manager == "Test Manager"


def test_parses_multiple_rows(tmp_path):
    path = write_csv(
        tmp_path / "in.csv",
        [record(email="a@example.com"), record(email="b@example.com")],
    )
    records = parse_access_file(path)
    assert len(records) == 2


def test_missing_file_raises(tmp_path):
    with pytest.raises(AccessFileError):
        parse_access_file(str(tmp_path / "does_not_exist.csv"))


def test_empty_file_raises(tmp_path):
    p = tmp_path / "empty.csv"
    p.write_text("")
    with pytest.raises(AccessFileError):
        parse_access_file(str(p))


def test_missing_columns_raises(tmp_path):
    p = tmp_path / "bad.csv"
    p.write_text("name,email\nAlice,alice@example.com\n")
    with pytest.raises(AccessFileError):
        parse_access_file(str(p))


def test_no_rows_raises(tmp_path):
    p = tmp_path / "headers_only.csv"
    p.write_text(",".join(
        [
            "name",
            "email",
            "department",
            "system",
            "permission",
            "date_granted",
            "date_last_used",
            "employee_status",
            "manager",
        ]
    ) + "\n")
    with pytest.raises(AccessFileError):
        parse_access_file(str(p))


def test_blank_date_last_used_is_none(tmp_path):
    path = write_csv(tmp_path / "in.csv", [record(date_last_used="")])
    records = parse_access_file(path)
    assert records[0].date_last_used is None


def test_unreadable_date_raises(tmp_path):
    path = write_csv(tmp_path / "in.csv", [record(date_granted="not a date")])
    with pytest.raises(AccessFileError):
        parse_access_file(path)


def test_alternate_date_formats_accepted(tmp_path):
    path = write_csv(tmp_path / "in.csv", [record(date_granted="31/01/2025")])
    records = parse_access_file(path)
    assert records[0].date_granted == date(2025, 1, 31)


def test_is_terminated_true(tmp_path):
    path = write_csv(tmp_path / "in.csv", [record(employee_status="Terminated")])
    records = parse_access_file(path)
    assert records[0].is_terminated is True


def test_is_terminated_case_insensitive(tmp_path):
    path = write_csv(tmp_path / "in.csv", [record(employee_status="terminated")])
    records = parse_access_file(path)
    assert records[0].is_terminated is True


def test_is_terminated_false_for_active(tmp_path):
    path = write_csv(tmp_path / "in.csv", [record(employee_status="Active")])
    records = parse_access_file(path)
    assert records[0].is_terminated is False


def test_is_privileged_true_for_admin(tmp_path):
    path = write_csv(tmp_path / "in.csv", [record(permission="Admin")])
    records = parse_access_file(path)
    assert records[0].is_privileged is True


def test_is_privileged_true_for_full_control(tmp_path):
    path = write_csv(tmp_path / "in.csv", [record(permission="Full Control")])
    records = parse_access_file(path)
    assert records[0].is_privileged is True


def test_is_privileged_false_for_standard(tmp_path):
    path = write_csv(tmp_path / "in.csv", [record(permission="Standard User")])
    records = parse_access_file(path)
    assert records[0].is_privileged is False


def test_days_since_last_use(tmp_path):
    path = write_csv(tmp_path / "in.csv", [record(date_last_used="2026-01-01")])
    records = parse_access_file(path)
    assert records[0].days_since_last_use(date(2026, 1, 31)) == 30


def test_days_since_last_use_none_when_never_used(tmp_path):
    path = write_csv(tmp_path / "in.csv", [record(date_last_used="")])
    records = parse_access_file(path)
    assert records[0].days_since_last_use(date(2026, 1, 31)) is None


def test_days_since_granted(tmp_path):
    path = write_csv(tmp_path / "in.csv", [record(date_granted="2026-01-01")])
    records = parse_access_file(path)
    assert records[0].days_since_granted(date(2026, 2, 1)) == 31


def test_row_numbers_start_at_two(tmp_path):
    path = write_csv(
        tmp_path / "in.csv",
        [record(email="a@example.com"), record(email="b@example.com")],
    )
    records = parse_access_file(path)
    assert records[0].row_number == 2
    assert records[1].row_number == 3
