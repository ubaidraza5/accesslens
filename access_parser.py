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

Real exports rarely use these exact header names, so a set of common
alternate names is also accepted for each column, matched without
regard to case, spacing, or underscores versus hyphens. If a file has
separate first name and last name columns instead of a single name
column, those two are combined automatically. See COLUMN_ALIASES below
for the full list of alternate names that are recognised.
"""

import csv
from dataclasses import dataclass
from datetime import date, datetime
from typing import Dict, List, Optional, Tuple


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

# Alternate header names accepted for each required column, in addition
# to the canonical name itself. Matching ignores case and treats spaces,
# underscores, and hyphens as the same character, so "Date_Granted",
# "date-granted", and "Grant Date" all resolve to date_granted.
COLUMN_ALIASES: Dict[str, List[str]] = {
    "name": ["full name", "employee name", "user name", "display name"],
    "email": ["email address", "e mail", "user email", "login email"],
    "department": ["dept", "team", "business unit", "division"],
    "system": ["application", "app", "resource", "platform", "system name", "app name"],
    "permission": ["role", "access level", "permission level", "entitlement", "access role"],
    "date_granted": ["grant date", "granted date", "access granted date", "date access granted"],
    "date_last_used": ["last used", "last login", "last activity", "last access", "last used date"],
    "employee_status": ["status", "account status", "user status"],
    "manager": ["manager name", "supervisor", "reports to"],
}

FIRST_NAME_ALIASES = ["first name", "first", "given name"]
LAST_NAME_ALIASES = ["last name", "last", "surname", "family name"]


def _normalize_header(header: str) -> str:
    header = header.strip().lower().replace("_", " ").replace("-", " ")
    return " ".join(header.split())


def _resolve_columns(
    fieldnames: List[str],
) -> Tuple[Dict[str, str], Optional[Tuple[str, str]]]:
    """Maps each canonical column to the actual header that supplies it.

    Returns the mapping, plus a (first name column, last name column)
    pair when name has to be built by combining two separate columns
    rather than coming from one column directly.
    """
    by_normalized = {}
    for field in fieldnames:
        by_normalized.setdefault(_normalize_header(field), field)

    resolved: Dict[str, str] = {}
    for canonical in REQUIRED_COLUMNS:
        candidates = [canonical.replace("_", " ")] + COLUMN_ALIASES.get(canonical, [])
        for candidate in candidates:
            if candidate in by_normalized:
                resolved[canonical] = by_normalized[candidate]
                break

    name_parts = None
    if "name" not in resolved:
        first_col = next(
            (by_normalized[a] for a in FIRST_NAME_ALIASES if a in by_normalized), None
        )
        last_col = next(
            (by_normalized[a] for a in LAST_NAME_ALIASES if a in by_normalized), None
        )
        if first_col and last_col:
            name_parts = (first_col, last_col)

    return resolved, name_parts


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

            resolved, name_parts = _resolve_columns(reader.fieldnames)
            missing = [
                c
                for c in REQUIRED_COLUMNS
                if c not in resolved and not (c == "name" and name_parts)
            ]
            if missing:
                raise AccessFileError(
                    "The file is missing required columns: "
                    + ", ".join(missing)
                    + ". Expected columns are: "
                    + ", ".join(REQUIRED_COLUMNS)
                )
            records = []
            for i, row in enumerate(reader, start=2):
                if name_parts:
                    first_col, last_col = name_parts
                    name_value = (
                        f"{(row.get(first_col) or '').strip()} "
                        f"{(row.get(last_col) or '').strip()}"
                    ).strip()
                else:
                    name_value = (row.get(resolved["name"]) or "").strip()
                records.append(
                    AccessRecord(
                        name=name_value,
                        email=(row.get(resolved["email"]) or "").strip(),
                        department=(row.get(resolved["department"]) or "").strip(),
                        system=(row.get(resolved["system"]) or "").strip(),
                        permission=(row.get(resolved["permission"]) or "").strip(),
                        date_granted=_parse_date(
                            row.get(resolved["date_granted"], ""), i, "date_granted"
                        ),
                        date_last_used=_parse_date(
                            row.get(resolved["date_last_used"], ""),
                            i,
                            "date_last_used",
                        ),
                        employee_status=(
                            row.get(resolved["employee_status"]) or ""
                        ).strip(),
                        manager=(row.get(resolved["manager"]) or "").strip(),
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
