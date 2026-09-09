"""
Parses an access export CSV into a list of AccessRecord objects.

AccessLens is designed around the kind of export almost any identity
system can produce, whether that is Active Directory, Okta, Azure AD, or
a cloud console user list. The expected columns are:

    name, email, department, system, permission, date_granted,
    date_last_used, employee_status, manager

date_last_used may be blank, which simply means the account has never
been used since it was granted. employee_status is expected to be either
Active or Terminated, matched case insensitively.
"""

import csv
from dataclasses import dataclass
from datetime import date, datetime
from typing import List, Optional


REQUIRED_COLUMNS = [
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


class AccessFileError(Exception):
    """Raised when the input CSV is missing columns or cannot be read."""


@dataclass
class AccessRecord:
    name: str
    email: str
    department: str
    system: str
    permission: str
    date_granted: Optional[date]
    date_last_used: Optional[date]
    employee_status: str
    manager: str
    row_number: int

    @property
    def is_terminated(self) -> bool:
        return self.employee_status.strip().lower() == "terminated"

    @property
    def is_privileged(self) -> bool:
        keywords = ("admin", "owner", "root", "superuser", "full control")
        return any(k in self.permission.strip().lower() for k in keywords)

    def days_since_last_use(self, as_of: date) -> Optional[int]:
        if self.date_last_used is None:
            return None
        return (as_of - self.date_last_used).days

    def days_since_granted(self, as_of: date) -> Optional[int]:
        if self.date_granted is None:
            return None
        return (as_of - self.date_granted).days


def _parse_date(value: str, row_number: int, column: str) -> Optional[date]:
    value = (value or "").strip()
    if not value:
        return None
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y"):
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            continue
    raise AccessFileError(
        f"Row {row_number}: could not read the date '{value}' in column "
        f"'{column}'. Use YYYY-MM-DD, for example 2026-01-31."
    )


def parse_access_file(path: str) -> List[AccessRecord]:
    """Reads an access export CSV and returns a list of AccessRecord."""
    try:
        with open(path, newline="", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            if reader.fieldnames is None:
                raise AccessFileError("The file is empty.")
            missing = [c for c in REQUIRED_COLUMNS if c not in reader.fieldnames]
            if missing:
                raise AccessFileError(
                    "The file is missing required columns: "
                    + ", ".join(missing)
                    + ". Expected columns are: "
                    + ", ".join(REQUIRED_COLUMNS)
                )
            records = []
            for i, row in enumerate(reader, start=2):
                records.append(
                    AccessRecord(
                        name=(row.get("name") or "").strip(),
                        email=(row.get("email") or "").strip(),
                        department=(row.get("department") or "").strip(),
                        system=(row.get("system") or "").strip(),
                        permission=(row.get("permission") or "").strip(),
                        date_granted=_parse_date(
                            row.get("date_granted", ""), i, "date_granted"
                        ),
                        date_last_used=_parse_date(
                            row.get("date_last_used", ""), i, "date_last_used"
                        ),
                        employee_status=(row.get("employee_status") or "").strip(),
                        manager=(row.get("manager") or "").strip(),
                        row_number=i,
                    )
                )
    except FileNotFoundError:
        raise AccessFileError(f"Could not find the file '{path}'.")
    except UnicodeDecodeError:
        raise AccessFileError(
            "Could not read the file as text. Save it as a plain CSV file "
            "and try again."
        )

    if not records:
        raise AccessFileError("The file has no access records in it.")

    return records
