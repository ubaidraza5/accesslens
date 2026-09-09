"""
Checks for separation of duties conflicts, cases where one person holds
two permissions that are supposed to be kept apart so that no single
person can both create and approve the same action unchecked.

The conflict list below is a starting set of the pairings most audit
frameworks ask about. It is intentionally readable as plain text so it
is easy to extend without touching the matching logic.
"""

from collections import defaultdict
from itertools import combinations
from typing import List

from access_parser import AccessRecord
from finding import Finding, Severity

CONFLICTING_PERMISSION_PAIRS = [
    ("Payment Processor", "Payment Approver"),
    ("Invoice Creator", "Invoice Approver"),
    ("Vendor Setup", "Payment Approver"),
    ("User Provisioner", "Access Approver"),
    ("Code Deploy", "Code Review Approver"),
    ("Payroll Processor", "Payroll Approver"),
    ("Purchase Requester", "Purchase Approver"),
]


def _conflict_pair_for(perm_a: str, perm_b: str):
    a = perm_a.strip().lower()
    b = perm_b.strip().lower()
    for left, right in CONFLICTING_PERMISSION_PAIRS:
        left_l, right_l = left.lower(), right.lower()
        if (left_l == a and right_l == b) or (left_l == b and right_l == a):
            return (left, right)
    return None


def analyze(records: List[AccessRecord]) -> List[Finding]:
    findings: List[Finding] = []
    active = [r for r in records if not r.is_terminated]

    by_person = defaultdict(list)
    for r in active:
        by_person[r.email].append(r)

    for email, person_records in by_person.items():
        permissions = list({r.permission for r in person_records})
        if len(permissions) < 2:
            continue
        for perm_a, perm_b in combinations(permissions, 2):
            pair = _conflict_pair_for(perm_a, perm_b)
            if pair is None:
                continue
            name = person_records[0].name or email
            systems = sorted(
                {r.system for r in person_records if r.permission in (perm_a, perm_b)}
            )
            findings.append(
                Finding(
                    code="SOD_CONFLICT",
                    severity=Severity.CRITICAL,
                    message=(
                        f"{name} holds both {perm_a} and {perm_b}, one "
                        "person should not be able to both create and "
                        "approve the same kind of action."
                    ),
                    subject=email,
                    evidence={
                        "permission_a": perm_a,
                        "permission_b": perm_b,
                        "systems": systems,
                    },
                    recommendation=(
                        f"Remove one side of this pairing from {name}, or "
                        "add a compensating control such as a second "
                        "approver, so the same person cannot do both steps."
                    ),
                )
            )

    return findings
