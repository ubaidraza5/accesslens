#!/usr/bin/env python3
"""
AccessLens command line interface.

Usage:
    python main.py records.csv
    python main.py records.csv --mode analyst
    python main.py records.csv --json report.json
    python main.py records.csv --as-of 2026-09-01
"""

import argparse
import sys
from datetime import date, datetime

from access_parser import AccessFileError, parse_access_file
import dormant_analyzer
import privilege_analyzer
import sod_analyzer
import ownership_analyzer
from risk_scorer import score_findings
import report_generator


def run_analysis(path: str, as_of: date):
    records = parse_access_file(path)

    findings = []
    findings.extend(dormant_analyzer.analyze(records, as_of))
    findings.extend(privilege_analyzer.analyze(records))
    findings.extend(sod_analyzer.analyze(records))
    findings.extend(ownership_analyzer.analyze(records, as_of))

    record_names = {r.email: r.name or r.email for r in records}
    report = score_findings(findings, record_names)
    return report


def main():
    parser = argparse.ArgumentParser(
        prog="accesslens",
        description="Review an identity and access export for common access risks.",
    )
    parser.add_argument("file", help="Path to the access export CSV file")
    parser.add_argument(
        "--mode",
        choices=["simple", "analyst"],
        default="simple",
        help="Report style, simple for a plain language summary, analyst "
        "for the full technical breakdown (default: simple)",
    )
    parser.add_argument(
        "--json",
        metavar="PATH",
        help="Also write the full report as JSON to this path",
    )
    parser.add_argument(
        "--as-of",
        metavar="YYYY-MM-DD",
        help="Treat this date as today when checking for dormant access "
        "(default: the current date)",
    )
    parser.add_argument(
        "--company",
        default="This company",
        help="Company name to use in the simple report",
    )

    args = parser.parse_args()

    if args.as_of:
        try:
            as_of = datetime.strptime(args.as_of, "%Y-%m-%d").date()
        except ValueError:
            print(f"error: could not read --as-of date '{args.as_of}', use YYYY-MM-DD", file=sys.stderr)
            sys.exit(2)
    else:
        as_of = date.today()

    try:
        report = run_analysis(args.file, as_of)
    except AccessFileError as e:
        print(f"error: {e}", file=sys.stderr)
        sys.exit(1)

    if args.mode == "simple":
        print(report_generator.render_simple(report, company_name=args.company))
    else:
        print(report_generator.render_analyst(report))

    if args.json:
        with open(args.json, "w", encoding="utf-8") as f:
            f.write(report_generator.render_json(report))
        print(f"\nFull JSON report written to {args.json}", file=sys.stderr)

    if report.company_level in ("High", "Critical"):
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
