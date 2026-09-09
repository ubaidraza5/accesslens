"""
Turns a RiskReport into readable output, either a plain language summary
for anyone in the business, or a full technical breakdown for an
analyst. Both modes are built from the exact same RiskReport, so they
can never tell two different stories about the same data.
"""

import json
from typing import List

from risk_scorer import AccountRisk, RiskReport

SEVERITY_ORDER = ["Critical", "High", "Medium", "Low", "Info"]


def _wrap(text: str, width: int = 78) -> str:
    words = text.split()
    lines: List[str] = []
    line = ""
    for word in words:
        if len(line) + len(word) + 1 > width:
            lines.append(line)
            line = word
        else:
            line = f"{line} {word}".strip()
    if line:
        lines.append(line)
    return "\n".join(lines)


def render_simple(report: RiskReport, company_name: str = "This company") -> str:
    lines = []
    lines.append("=" * 60)
    lines.append("ACCESSLENS REPORT, PLAIN LANGUAGE SUMMARY")
    lines.append("=" * 60)
    lines.append("")
    lines.append(f"Company reviewed: {company_name}")
    lines.append(f"Overall access risk: {report.company_level.upper()}")
    lines.append(f"Risk score: {report.company_score} out of 100")
    lines.append("")

    if report.company_level == "Clean" or report.total_findings == 0:
        lines.append(
            _wrap(
                f"{company_name} looks well managed. No significant access "
                "issues were found in this export."
            )
        )
        return "\n".join(lines)

    top_accounts = [a for a in report.accounts if a.level in ("Critical", "High")][:5]
    if top_accounts:
        lines.append("Accounts that need attention first:")
        lines.append("")
        for a in top_accounts:
            worst = a.findings[0]
            lines.append(f"  - {a.name} ({a.level} risk)")
            lines.append("    " + _wrap(worst.message, width=74).replace("\n", "\n    "))
            lines.append("")

    lines.append("What this means in plain terms:")
    lines.append("")
    counts = report.findings_by_severity
    if counts.get("Critical"):
        lines.append(
            _wrap(
                f"{counts['Critical']} issue(s) need action right away, these "
                "are things like access left behind after someone left the "
                "company, or one person able to both request and approve "
                "the same action."
            )
        )
        lines.append("")
    if counts.get("High"):
        lines.append(
            _wrap(
                f"{counts['High']} issue(s) are high priority, mostly "
                "unused accounts and admin access that stands out compared "
                "to the rest of a team."
            )
        )
        lines.append("")
    if counts.get("Medium") or counts.get("Low"):
        remainder = counts.get("Medium", 0) + counts.get("Low", 0)
        lines.append(
            _wrap(
                f"{remainder} smaller issue(s) are worth cleaning up but are "
                "not urgent, mostly access that has not been reviewed "
                "recently or accounts with no listed owner."
            )
        )
        lines.append("")

    lines.append(
        _wrap(
            "Recommended next step: share the accounts listed above with "
            "their managers and confirm whether the access is still needed."
        )
    )
    return "\n".join(lines)


def render_analyst(report: RiskReport) -> str:
    lines = []
    lines.append("=" * 60)
    lines.append("ACCESSLENS REPORT, ANALYST VIEW")
    lines.append("=" * 60)
    lines.append("")
    lines.append(f"Company risk score : {report.company_score} / 100")
    lines.append(f"Company risk level : {report.company_level}")
    lines.append(f"Total findings     : {report.total_findings}")
    lines.append("")
    lines.append("Findings by severity:")
    for label in SEVERITY_ORDER:
        count = report.findings_by_severity.get(label, 0)
        if count:
            lines.append(f"  {label:<10} {count}")
    lines.append("")

    lines.append("-" * 60)
    lines.append("ACCOUNTS BY RISK")
    lines.append("-" * 60)
    for a in report.accounts:
        lines.append("")
        lines.append(f"{a.name} <{a.subject}>  [{a.level}, score {a.score}]")
        for f in a.findings:
            lines.append(f"  [{f.severity.label}] {f.code}")
            lines.append("    " + _wrap(f.message, width=72).replace("\n", "\n    "))
            if f.evidence:
                for k, v in f.evidence.items():
                    lines.append(f"      evidence: {k} = {v}")
            if f.recommendation:
                lines.append(
                    "    recommendation: "
                    + _wrap(f.recommendation, width=64).replace("\n", "\n                    ")
                )

    company_wide = [f for f in report.findings if f.subject is None]
    if company_wide:
        lines.append("")
        lines.append("-" * 60)
        lines.append("COMPANY WIDE FINDINGS")
        lines.append("-" * 60)
        for f in company_wide:
            lines.append("")
            lines.append(f"[{f.severity.label}] {f.code}")
            lines.append("  " + _wrap(f.message, width=74).replace("\n", "\n  "))
            if f.evidence:
                for k, v in f.evidence.items():
                    lines.append(f"    evidence: {k} = {v}")
            if f.recommendation:
                lines.append(
                    "  recommendation: "
                    + _wrap(f.recommendation, width=68).replace("\n", "\n                  ")
                )

    return "\n".join(lines)


def render_json(report: RiskReport) -> str:
    payload = {
        "company_score": report.company_score,
        "company_level": report.company_level,
        "total_findings": report.total_findings,
        "findings_by_severity": report.findings_by_severity,
        "findings": [f.to_dict() for f in report.findings],
        "accounts": [
            {
                "subject": a.subject,
                "name": a.name,
                "score": a.score,
                "level": a.level,
                "findings": [f.to_dict() for f in a.findings],
            }
            for a in report.accounts
        ],
    }
    return json.dumps(payload, indent=2)
