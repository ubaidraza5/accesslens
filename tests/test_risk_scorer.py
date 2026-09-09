from finding import Finding, Severity
from risk_scorer import score_findings


def f(severity, subject=None, code="TEST"):
    return Finding(code=code, severity=severity, message="msg", subject=subject)


def test_no_findings_gives_clean_level():
    report = score_findings([])
    assert report.company_score == 0
    assert report.company_level == "Clean"
    assert report.total_findings == 0


def test_single_low_finding_gives_low_level():
    report = score_findings([f(Severity.LOW)])
    assert report.company_level == "Low"
    assert report.company_score == 2


def test_single_critical_finding_gives_high_level():
    # one critical issue floors the company level at High even though
    # the raw point total alone would only reach Medium
    report = score_findings([f(Severity.CRITICAL)])
    assert report.company_level == "High"
    assert report.company_score == 20


def test_three_critical_findings_reach_critical_level():
    report = score_findings(
        [f(Severity.CRITICAL, code="A"), f(Severity.CRITICAL, code="B"), f(Severity.CRITICAL, code="C")]
    )
    assert report.company_score == 60
    assert report.company_level == "Critical"


def test_score_is_capped_at_100():
    findings = [f(Severity.CRITICAL) for _ in range(10)]
    report = score_findings(findings)
    assert report.company_score == 100


def test_findings_by_severity_counts():
    findings = [f(Severity.HIGH), f(Severity.HIGH), f(Severity.LOW)]
    report = score_findings(findings)
    assert report.findings_by_severity["High"] == 2
    assert report.findings_by_severity["Low"] == 1


def test_accounts_grouped_by_subject():
    findings = [
        f(Severity.HIGH, subject="a@example.com"),
        f(Severity.MEDIUM, subject="a@example.com"),
        f(Severity.LOW, subject="b@example.com"),
    ]
    report = score_findings(findings)
    subjects = {a.subject for a in report.accounts}
    assert subjects == {"a@example.com", "b@example.com"}
    a_account = next(a for a in report.accounts if a.subject == "a@example.com")
    assert a_account.score == 15
    assert a_account.level == "High"


def test_company_wide_findings_have_no_subject():
    findings = [f(Severity.HIGH, subject=None)]
    report = score_findings(findings)
    assert report.accounts == []
    assert report.total_findings == 1


def test_accounts_sorted_highest_score_first():
    findings = [
        f(Severity.LOW, subject="low@example.com"),
        f(Severity.CRITICAL, subject="crit@example.com"),
        f(Severity.MEDIUM, subject="med@example.com"),
    ]
    report = score_findings(findings)
    subjects_in_order = [a.subject for a in report.accounts]
    assert subjects_in_order == ["crit@example.com", "med@example.com", "low@example.com"]


def test_account_name_lookup_used_when_provided():
    findings = [f(Severity.LOW, subject="a@example.com")]
    report = score_findings(findings, record_names={"a@example.com": "Alice Example"})
    assert report.accounts[0].name == "Alice Example"


def test_account_name_falls_back_to_email():
    findings = [f(Severity.LOW, subject="a@example.com")]
    report = score_findings(findings)
    assert report.accounts[0].name == "a@example.com"


def test_account_findings_sorted_most_severe_first():
    findings = [
        f(Severity.LOW, subject="a@example.com", code="LOW_ONE"),
        f(Severity.CRITICAL, subject="a@example.com", code="CRIT_ONE"),
    ]
    report = score_findings(findings)
    account = report.accounts[0]
    assert account.findings[0].code == "CRIT_ONE"


def test_thresholds_medium_boundary():
    # a score of 12 sits below the Medium cutoff of 15, so it should
    # still read as Low
    findings = [f(Severity.MEDIUM), f(Severity.MEDIUM), f(Severity.LOW)]
    report = score_findings(findings)
    assert report.company_score == 12
    assert report.company_level == "Low"


def test_thresholds_medium_at_cutoff():
    # a score of exactly 15 should read as Medium
    findings = [f(Severity.MEDIUM), f(Severity.MEDIUM), f(Severity.MEDIUM)]
    report = score_findings(findings)
    assert report.company_score == 15
    assert report.company_level == "Medium"
