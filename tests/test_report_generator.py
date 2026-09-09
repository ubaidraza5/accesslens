import json

from finding import Finding, Severity
from report_generator import render_analyst, render_json, render_simple
from risk_scorer import score_findings


def f(severity, subject=None, code="TEST", message="something happened"):
    return Finding(code=code, severity=severity, message=message, subject=subject)


def test_simple_report_clean_when_no_findings():
    report = score_findings([])
    text = render_simple(report, company_name="Acme")
    assert "CRITICAL" not in text
    assert "Acme looks well managed" in text


def test_simple_report_mentions_company_name():
    report = score_findings([f(Severity.CRITICAL, subject="a@example.com")])
    text = render_simple(report, company_name="Acme Corp")
    assert "Acme Corp" in text


def test_simple_report_does_not_include_finding_codes():
    report = score_findings(
        [f(Severity.CRITICAL, subject="a@example.com", code="SOD_CONFLICT")]
    )
    text = render_simple(report)
    assert "SOD_CONFLICT" not in text


def test_simple_report_shows_top_risk_accounts():
    report = score_findings(
        [f(Severity.CRITICAL, subject="a@example.com", message="a has a problem")]
    )
    text = render_simple(report)
    assert "a has a problem" in text


def test_simple_report_limits_to_five_accounts():
    findings = [
        f(Severity.CRITICAL, subject=f"user{i}@example.com")
        for i in range(8)
    ]
    report = score_findings(findings)
    text = render_simple(report)
    shown = sum(1 for i in range(8) if f"user{i}@example.com" in text)
    assert shown <= 5


def test_analyst_report_includes_finding_codes():
    report = score_findings(
        [f(Severity.CRITICAL, subject="a@example.com", code="SOD_CONFLICT")]
    )
    text = render_analyst(report)
    assert "SOD_CONFLICT" in text


def test_analyst_report_includes_score_and_level():
    report = score_findings([f(Severity.CRITICAL, subject="a@example.com")])
    text = render_analyst(report)
    assert "Critical" in text
    assert "20" in text


def test_analyst_report_includes_evidence():
    finding = Finding(
        code="DORMANT_ACCOUNT",
        severity=Severity.HIGH,
        message="msg",
        subject="a@example.com",
        evidence={"days_unused": 120},
    )
    report = score_findings([finding])
    text = render_analyst(report)
    assert "days_unused" in text
    assert "120" in text


def test_analyst_report_includes_company_wide_section():
    finding = Finding(
        code="ADMIN_CONCENTRATION",
        severity=Severity.HIGH,
        message="too many admins",
        subject=None,
    )
    report = score_findings([finding])
    text = render_analyst(report)
    assert "COMPANY WIDE FINDINGS" in text
    assert "ADMIN_CONCENTRATION" in text


def test_json_report_is_valid_json():
    report = score_findings([f(Severity.CRITICAL, subject="a@example.com")])
    payload = json.loads(render_json(report))
    assert payload["company_level"] == "High"
    assert payload["total_findings"] == 1
    assert payload["accounts"][0]["subject"] == "a@example.com"


def test_json_report_round_trips_evidence():
    finding = Finding(
        code="TEST",
        severity=Severity.LOW,
        message="msg",
        subject="a@example.com",
        evidence={"key": "value"},
        recommendation="do the thing",
    )
    report = score_findings([finding])
    payload = json.loads(render_json(report))
    finding_payload = payload["accounts"][0]["findings"][0]
    assert finding_payload["evidence"] == {"key": "value"}
    assert finding_payload["recommendation"] == "do the thing"
