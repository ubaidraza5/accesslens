"""
Checks that every active account has someone accountable for it. Access
that nobody owns cannot be reviewed properly, there is no one to ask
whether it is still needed, so a missing manager is a finding in its own
right even before looking at what the access actually is.
"""

from datetime import date
from typing import List

from access_parser import AccessRecord
from finding import Finding, Severity

STALE_REVIEW_DAYS = 365


def analyze(records: List[AccessRecord], as_of: date) -> List[Finding]:
    findings: List[Finding] = []

    for r in records:
        if r.is_terminated:
            continue

        if not r.manager:
            findings.append(
                Finding(
                    code="NO_MANAGER_LISTED",
                    severity=Severity.MEDIUM,
                    message=(
                        f"{r.name or r.email} has {r.permission} access to "
                        f"{r.system} with no manager listed to approve or "
                        "review it."
                    ),
                    subject=r.email,
                    evidence={"system": r.system, "permission": r.permission},
                    recommendation=(
                        "Assign an owner for this account so it can be "
                        "included in the next access review."
                    ),
                )
            )

        days_since_grant = r.days_since_granted(as_of)
        if days_since_grant is not None and days_since_grant >= STALE_REVIEW_DAYS:
            findings.append(
                Finding(
                    code="RECERTIFICATION_OVERDUE",
                    severity=Severity.LOW,
                    message=(
                        f"{r.name or r.email}'s {r.permission} access to "
                        f"{r.system} was granted {days_since_grant} days ago "
                        "and does not appear to have been reviewed since."
                    ),
                    subject=r.email,
                    evidence={
                        "system": r.system,
                        "permission": r.permission,
                        "date_granted": str(r.date_granted),
                        "days_since_grant": days_since_grant,
                    },
                    recommendation=(
                        "Include this access in the next recertification "
                        "cycle, most frameworks expect a review at least "
                        "once a year."
                    ),
                )
            )

    return findings
