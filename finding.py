"""
Shared Finding and Severity types used by every analyzer in AccessLens.

Each analyzer inspects the parsed access records and returns a list of
Finding objects. The risk scorer then combines all findings into a single
verdict. Keeping this as one small shared module means every analyzer
speaks the same language, and the report generator never has to guess
what shape a finding is in.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class Severity(Enum):
    """How serious a finding is, ordered from least to most severe."""

    INFO = 0
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4

    @property
    def label(self) -> str:
        return self.name.title()


@dataclass
class Finding:
    """
    A single issue raised by an analyzer.

    code: short machine readable identifier, for example DORMANT_ACCOUNT
    severity: how serious the issue is
    message: one sentence, plain English explanation of the issue
    subject: the person or account the finding is about, for example an
        email address. None for a company wide finding that is not tied
        to one account.
    evidence: the raw facts backing the finding (dates, systems,
        permission levels) so an analyst can verify it without redoing
        the analysis by hand.
    recommendation: one sentence describing the suggested next action.
    """

    code: str
    severity: Severity
    message: str
    subject: Optional[str] = None
    evidence: dict = field(default_factory=dict)
    recommendation: str = ""

    def to_dict(self) -> dict:
        return {
            "code": self.code,
            "severity": self.severity.label,
            "message": self.message,
            "subject": self.subject,
            "evidence": self.evidence,
            "recommendation": self.recommendation,
        }
