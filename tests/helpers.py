"""Small helpers shared by the test files, mainly for building throwaway
CSV files without repeating the same csv.writer boilerplate everywhere.
"""

import csv

COLUMNS = [
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


def write_csv(path, rows):
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=COLUMNS)
        writer.writeheader()
        for row in rows:
            full = {c: row.get(c, "") for c in COLUMNS}
            writer.writerow(full)
    return str(path)


def record(**overrides):
    base = {
        "name": "Test Person",
        "email": "test.person@example.com",
        "department": "Finance",
        "system": "Finance ERP",
        "permission": "Standard User",
        "date_granted": "2025-01-01",
        "date_last_used": "2026-08-01",
        "employee_status": "Active",
        "manager": "Test Manager",
    }
    base.update(overrides)
    return base
