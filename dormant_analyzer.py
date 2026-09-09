"""
Looks for accounts that should probably not still have access at all,
either because nobody has used them in a long time or because the person
they belong to has already left.
"""

from datetime import date
from typing import List

from access_parser import AccessRecord
from finding import Finding, Severity

DORMANT_DAYS_THRESHOLD = 90
NEVER_USED_GRACE_DAYS = 30


def analyze(records: List[AccessRecord], as_of: date) -> List[Finding]:
    findings: List[Finding] = []

    for r in records:
        if r.is_terminated:
            findings.append(
                Finding(
                    code="ORPHANED_TERMINATED_ACCESS",
                    severity=Severity.CRITICAL
                    if r.is_privileged
                    else Severity.HIGH,
                    message=(
                        f"{r.name or r.email} is marked as terminated but "
                        f"still has {r.permission} access to {r.system}."
                    ),
                    subject=r.email,
                    evidence={
                        "system": r.system,
                        "permission": r.permission,
                        "employee_status": r.employee_status,
                        "date_last_used": str(r.date_last_used)
                        if r.date_last_used
                        else "never",
                    },
                    recommendation=(
                        f"Remove {r.system} access for {r.name or r.email} "
                        "immediately, this account belongs to someone who "
                        "no longer works here."
                    ),
                )
            )
            continue

        days_unused = r.days_since_last_use(as_of)
        if days_unused is not None and days_unused >= DORMANT_DAYS_THRESHOLD:
            findings.append(
                Finding(
                    code="DORMANT_ACCOUNT",
                    severity=Severity.HIGH if r.is_privileged else Severity.MEDIUM,
                    message=(
                        f"{r.name or r.email} has not used {r.system} in "
                        f"{days_unused} days."
                    ),
                    subject=r.email,
                    evidence={
                        "system": r.system,
                        "permission": r.permission,
                        "date_last_used": str(r.date_last_used),
                        "days_unused": days_unused,
                    },
                    recommendation=(
                        f"Confirm with {r.manager or 'the manager on file'} "
                        f"whether {r.name or r.email} still needs {r.system}, "
                        "and remove the access if not."
                    ),
                )
            )
            continue

        if r.date_last_used is None:
            days_since_grant = r.days_since_granted(as_of)
            if (
                days_since_grant is not None
                and days_since_grant >= NEVER_USED_GRACE_DAYS
            ):
                findings.append(
                    Finding(
                        code="NEVER_USED_ACCOUNT",
                        severity=Severity.MEDIUM,
                        message=(
                            f"{r.name or r.email} was granted {r.permission} "
                            f"on {r.system} {days_since_grant} days ago and "
                            "has never used it."
                        ),
                        subject=r.email,
                        evidence={
                            "system": r.system,
                            "permission": r.permission,
                            "date_granted": str(r.date_granted),
                            "days_since_grant": days_since_grant,
                        },
                        recommendation=(
                            f"Check whether {r.name or r.email} still needs "
                            f"this access, an account nobody has ever used "
                            "is a common sign of an unnecessary grant."
                        ),
                    )
                )

    return findings
