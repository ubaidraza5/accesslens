"""
Looks at how privileged access is spread across each system and each
department, and flags two patterns that reviewers are usually asked to
justify: one person holding admin rights when nobody else on their team
does, and a system where far too many people hold admin rights at all.
"""

from collections import defaultdict
from typing import List

from access_parser import AccessRecord
from finding import Finding, Severity

ADMIN_CONCENTRATION_THRESHOLD = 0.30
MIN_GROUP_SIZE_FOR_OUTLIER_CHECK = 3


def analyze(records: List[AccessRecord]) -> List[Finding]:
    findings: List[Finding] = []
    active = [r for r in records if not r.is_terminated]

    findings.extend(_find_privilege_outliers(active))
    findings.extend(_find_admin_concentration(active))
    return findings


def _find_privilege_outliers(records: List[AccessRecord]) -> List[Finding]:
    findings = []
    groups = defaultdict(list)
    for r in records:
        groups[(r.department, r.system)].append(r)

    for (department, system), members in groups.items():
        if len(members) < MIN_GROUP_SIZE_FOR_OUTLIER_CHECK:
            continue
        privileged = [m for m in members if m.is_privileged]
        standard = [m for m in members if not m.is_privileged]
        if privileged and standard and len(privileged) == 1:
            outlier = privileged[0]
            findings.append(
                Finding(
                    code="PRIVILEGE_OUTLIER",
                    severity=Severity.HIGH,
                    message=(
                        f"{outlier.name or outlier.email} is the only person "
                        f"in {department} with {outlier.permission} on "
                        f"{system}, everyone else on the team has standard "
                        "access."
                    ),
                    subject=outlier.email,
                    evidence={
                        "department": department,
                        "system": system,
                        "permission": outlier.permission,
                        "peer_count": len(standard),
                    },
                    recommendation=(
                        f"Ask {outlier.manager or 'the manager on file'} to "
                        "confirm this elevated access is still needed, or "
                        "reduce it to match the rest of the team."
                    ),
                )
            )
    return findings


def _find_admin_concentration(records: List[AccessRecord]) -> List[Finding]:
    findings = []
    by_system = defaultdict(list)
    for r in records:
        by_system[r.system].append(r)

    for system, members in by_system.items():
        if len(members) < MIN_GROUP_SIZE_FOR_OUTLIER_CHECK:
            continue
        privileged = [m for m in members if m.is_privileged]
        share = len(privileged) / len(members)
        if share >= ADMIN_CONCENTRATION_THRESHOLD:
            findings.append(
                Finding(
                    code="ADMIN_CONCENTRATION",
                    severity=Severity.HIGH,
                    message=(
                        f"{len(privileged)} of {len(members)} people with "
                        f"access to {system} hold admin level permission, "
                        f"that is {round(share * 100)} percent of everyone "
                        "with access."
                    ),
                    subject=None,
                    evidence={
                        "system": system,
                        "privileged_count": len(privileged),
                        "total_count": len(members),
                        "privileged_users": [
                            p.email for p in privileged
                        ],
                    },
                    recommendation=(
                        f"Review admin access to {system} as a group and "
                        "confirm each person still needs full rights rather "
                        "than a lower level role."
                    ),
                )
            )
    return findings
