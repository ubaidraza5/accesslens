"""
Turns a list of findings into a single risk picture, both for the
company as a whole and for each individual account. The same weights
are used everywhere so the two views can never disagree with each
other, only zoom in or out.
"""

from collections import defaultdict
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from finding import Finding, Severity

SEVERITY_WEIGHT = {
    Severity.INFO: 0,
    Severity.LOW: 2,
    Severity.MEDIUM: 5,
    Severity.HIGH: 10,
    Severity.CRITICAL: 20,
}

COMPANY_THRESHOLDS = [
    (60, "Critical"),
    (35, "High"),
    (15, "Medium"),
    (1, "Low"),
]

ACCOUNT_THRESHOLDS = [
    (20, "Critical"),
    (10, "High"),
    (5, "Medium"),
    (1, "Low"),
]

LEVEL_ORDER = ["Clean", "Low", "Medium", "High", "Critical"]

# A single finding of a given severity puts a floor under the company
# wide level, so one critical issue can never be buried by a Medium
# label just because the total point count is still low.
COMPANY_FLOOR_FOR_SEVERITY = {
    Severity.CRITICAL: "High",
    Severity.HIGH: "Medium",
}


def _level_for(score: int, thresholds) -> str:
    for cutoff, label in thresholds:
        if score >= cutoff:
            return label
    return "Clean"


def _more_severe(a: str, b: str) -> str:
    return a if LEVEL_ORDER.index(a) >= LEVEL_ORDER.index(b) else b


@dataclass
class AccountRisk:
    subject: str
    name: str
    score: int
    level: str
    findings: List[Finding] = field(default_factory=list)


@dataclass
class RiskReport:
    company_score: int
    company_level: str
    total_findings: int
    findings_by_severity: Dict[str, int]
    findings: List[Finding]
    accounts: List[AccountRisk]


def score_findings(
    findings: List[Finding],
    record_names: Optional[Dict[str, str]] = None,
) -> RiskReport:
    record_names = record_names or {}

    raw_company_score = sum(SEVERITY_WEIGHT[f.severity] for f in findings)
    company_score = min(100, raw_company_score)
    company_level = _level_for(company_score, COMPANY_THRESHOLDS)
    for finding in findings:
        floor = COMPANY_FLOOR_FOR_SEVERITY.get(finding.severity)
        if floor:
            company_level = _more_severe(company_level, floor)

    by_severity: Dict[str, int] = defaultdict(int)
    for f in findings:
        by_severity[f.severity.label] += 1

    by_subject: Dict[str, List[Finding]] = defaultdict(list)
    for f in findings:
        if f.subject:
            by_subject[f.subject].append(f)

    accounts = []
    for subject, subject_findings in by_subject.items():
        raw = sum(SEVERITY_WEIGHT[f.severity] for f in subject_findings)
        score = min(100, raw)
        level = _level_for(score, ACCOUNT_THRESHOLDS)
        accounts.append(
            AccountRisk(
                subject=subject,
                name=record_names.get(subject, subject),
                score=score,
                level=level,
                findings=sorted(
                    subject_findings, key=lambda f: -f.severity.value
                ),
            )
        )

    accounts.sort(key=lambda a: -a.score)

    return RiskReport(
        company_score=company_score,
        company_level=company_level,
        total_findings=len(findings),
        findings_by_severity=dict(by_severity),
        findings=sorted(findings, key=lambda f: -f.severity.value),
        accounts=accounts,
    )
