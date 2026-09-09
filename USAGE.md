# Usage Guide

This page covers every way to run AccessLens, the command line tool and
the browser demo, along with the full list of options and what the output
means.

## Preparing your access export

Export your access records from whatever system holds them, Active
Directory, Okta, Azure AD, a cloud provider console, or a spreadsheet you
maintain by hand, and save it as a CSV file with these columns in any
order.

```
name, email, department, system, permission, date_granted, date_last_used, employee_status, manager
```

A few notes on the columns.

email should be the same value every time a given person appears, this is
how AccessLens tells that two rows belong to the same account.

date_granted and date_last_used should be written as YYYY MM DD, for
example 2026 03 15. Day first and month first formats are also accepted.
Leave date_last_used blank if the account has never been used since it was
granted.

employee_status should read Active or Terminated. Any other value is
treated as active, so make sure terminated staff are marked clearly, this
is one of the most important signals AccessLens looks for.

manager should be the name of the person accountable for this access. A
blank manager is itself flagged, since access nobody owns cannot be
reviewed properly.

## Running the command line tool

The simplest run reads a file and prints the plain language summary.

```bash
python main.py my_export.csv
```

### Choosing a report style

```bash
python main.py my_export.csv --mode simple
python main.py my_export.csv --mode analyst
```

Simple mode is the default, and is meant to be read by anyone in the
business. Analyst mode prints every finding with its evidence and is meant
for a security or audit reviewer who needs to verify the result.

### Saving a JSON report

```bash
python main.py my_export.csv --json report.json
```

This writes the full report, every finding, every account score, and the
company wide score, as JSON, which is useful for feeding into another
tool or dashboard.

### Naming the company in the simple report

```bash
python main.py my_export.csv --company "Example Holdings"
```

### Choosing the reference date

By default AccessLens compares every date against today. To review an
export as of a specific date, for example when checking a snapshot taken
in the past, pass:

```bash
python main.py my_export.csv --as-of 2026-06-01
```

### Reading the exit code

The command exits 0 when the overall risk level is Clean or Low, and 1
when it is High or Critical. This makes AccessLens easy to drop into a
script or a pipeline as a pass or fail gate.

## Using the browser demo

Open the live demo at https://ubaidraza5.github.io/accesslens and you
will see three ways to provide data: load one of the two built in sample
companies, upload your own CSV file, or paste CSV text directly into the
box.

Press Run review once you have data in the box. The results panel appears
below with an overall score, and a Simple and Analyst toggle at the top
right lets you switch between the two views instantly, without rerunning
the review.

Nothing you paste or upload in the browser demo is sent to a server, the
entire analysis runs using JavaScript already loaded on the page. You can
confirm this yourself by opening your browser's network panel while using
it, there is nothing to see there.

## Reading a finding

Every finding, in either report style, includes the same underlying
information.

A code identifies the type of issue, for example DORMANT_ACCOUNT or
SOD_CONFLICT, shown only in analyst mode.

A severity from Info up to Critical shows how serious the issue is.

A message explains the issue in one plain sentence.

Evidence, shown in analyst mode, lists the exact facts behind the finding,
dates, systems, and permission names, so a reviewer can check the result
without redoing the analysis.

A recommendation suggests the next concrete step to take.

## Understanding the score

Each finding carries a weight based on its severity, Critical findings
weigh the most, Info findings weigh nothing. An account's score is the sum
of its findings' weights, capped at 100. The company wide score works the
same way across every finding in the export. A single Critical finding
also puts a floor under the company level, so one serious issue can never
be hidden by a low overall point total.

| Level | Meaning |
|---|---|
| Clean | No issues found |
| Low | Minor cleanup worth doing, nothing urgent |
| Medium | Worth reviewing this cycle |
| High | Needs attention soon |
| Critical | Needs action right away |

## Getting help

```bash
python main.py --help
```
