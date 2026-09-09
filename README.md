# AccessLens

AccessLens reviews an identity and access export and tells you, in plain
language, which accounts need attention and why. The same review also
produces a full technical breakdown for a security or audit analyst, built
from the exact same analysis, so the two views can never disagree with each
other.

Live demo: https://ubaidraza5.github.io/accesslens
Source code: https://github.com/ubaidraza5/accesslens

## What it looks for

AccessLens checks an access export against four common review areas.

Dormant and orphaned access looks for accounts that have not been used in a
long time, and for access that is still active even though the employee
record shows they have already left the company.

Excess privilege looks for a person who holds a much higher level of access
than everyone else on their team, and for a system where too many people
hold admin rights at once.

Separation of duties looks for a person who holds two permissions that are
supposed to be kept apart, for example being able to both create and
approve the same payment.

Ownership and review checks that every account has a manager listed, and
flags access that has not been reviewed in over a year.

Every issue found is called a finding. Each finding carries a plain
sentence explaining what is wrong, the evidence behind it, a recommended
next step, and a severity from Info up to Critical. Findings are combined
into a single score out of 100 for the whole company, and a score for each
account.

## Two ways to read the same report

Simple mode is written for anyone in the business. It names the accounts
that need attention first and explains what is wrong in a sentence, with no
jargon and no codes.

Analyst mode shows the full technical picture, every finding, the evidence
behind it, and the severity breakdown, grouped by account and by the
system wide issues that are not tied to a single person.

Both modes are generated from one shared analysis pass, there is no second
pass or separate logic that could tell a different story.

## Try it without installing anything

Open the live demo, load one of the two sample companies, and press Run
review. Nothing you paste or upload is ever sent anywhere, the whole
analysis runs in your own browser using the JavaScript port of the same
engine described below.

## Running it from the command line

AccessLens needs only the Python standard library, there is nothing to
install for normal use.

```bash
python main.py your_access_export.csv
```

This prints the plain language summary. For the full technical view:

```bash
python main.py your_access_export.csv --mode analyst
```

To also save the full report as JSON:

```bash
python main.py your_access_export.csv --json report.json
```

The command exits with a nonzero status when the overall risk comes back
High or Critical, which makes it easy to use as a gate in an automated
pipeline.

## The input file

AccessLens reads a CSV export with these columns.

| Column | What goes in it |
|---|---|
| name | The person's full name |
| email | Their email address, used as the unique account identifier |
| department | The team or department they belong to |
| system | The system or application this row grants access to |
| permission | The permission or role granted, for example Admin or Standard User |
| date_granted | The date the access was granted, YYYY MM DD |
| date_last_used | The date the access was last used, left blank if never used |
| employee_status | Active or Terminated |
| manager | The manager who owns or approved this access |

Each row is one person's access to one system. A person with access to
three systems appears as three rows. This matches the shape of a typical
export from Active Directory, Okta, Azure AD, or a cloud provider's
console.

Real exports rarely use these exact column names, so AccessLens also
accepts a set of common alternates without needing the file renamed by
hand first. Full Name, Employee Name, User Name, and Display Name are
all read as name, and a file with separate First Name and Last Name
columns has them combined into one name automatically. Email Address is
read as email. Dept, Team, Business Unit, and Division are read as
department. Application, App, Resource, Platform, and System Name are
read as system. Role, Access Level, Permission Level, and Entitlement
are read as permission. Grant Date and Granted Date are read as
date_granted. Last Used, Last Login, and Last Activity are read as
date_last_used. Status and Account Status are read as employee_status.
Manager Name and Supervisor are read as manager. Matching ignores case
and treats underscores the same as spaces, so DEPARTMENT, Department,
and department all work.

This only covers naming, not meaning. A file still needs to actually
carry the underlying concepts AccessLens reviews, who has access, to
what, at what permission level, whether they are still employed, and
who owns that access. A visitor log or a physical access record, for
example, is a different kind of data entirely and will still be
rejected, with a message naming exactly which columns are missing.

A sample export with a full set of realistic, deliberately planted issues
lives at `tests/fixtures/sample_company_access.csv`, and a clean export
with no issues at all lives at `tests/fixtures/clean_company_access.csv`.
Both use entirely fictional people and a fictional company, no real
company data is included anywhere in this project.

## Project layout

```
access_parser.py       reads the CSV and builds AccessRecord objects
finding.py              the shared Finding and Severity types
dormant_analyzer.py     dormant and orphaned access checks
privilege_analyzer.py   excess privilege and admin concentration checks
sod_analyzer.py         separation of duties conflict checks
ownership_analyzer.py   missing manager and overdue review checks
risk_scorer.py          combines findings into account and company scores
report_generator.py     renders the simple, analyst, and JSON reports
main.py                 the command line entry point
web/index.html          the browser based demo, a JavaScript port of the engine
scripts/verify_web_demo.js   checks the web demo agrees with the Python engine
tests/                  the pytest suite and sample fixtures
docs/                   the walkthrough and supporting documentation
```

## Testing

```bash
pip install -r requirements-dev.txt
pytest
```

The web demo has its own check, which extracts the exact script shipped in
`web/index.html` and runs it against the same fixture files the Python
tests use, confirming both engines produce the same score, level, and
finding counts.

```bash
node scripts/verify_web_demo.js
```

Both checks run automatically in CI on every change, and the browser demo
only deploys once they both pass.

## Development notes

`DEVELOPMENT_NOTES.md` records the real problems found while building
this project, and how each one was fixed, from a scoring edge case to a
GitHub Pages setting that needed changing before the live demo would
load.

## Security and privacy

See `SECURITY.md`. In short, nothing pasted or uploaded to the browser
demo ever leaves the page, and the CLI only ever reads the file you point
it at.

## License

MIT, see `LICENSE`.

## Author

Built by Ubaid Raza Ansari, GRC and IAM Analyst, MSc Cyber Security, NCSC
Certified.
