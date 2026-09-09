# Contributing

This started as a personal portfolio project, but suggestions and fixes
are welcome.

## Getting set up

```bash
git clone https://github.com/ubaidraza5/accesslens.git
cd accesslens
pip install -r requirements-dev.txt
pytest
```

All of that should pass with no setup beyond a normal Python install,
there are no third party runtime dependencies.

## Making a change

Keep each analyzer focused on one review area, the pattern used
throughout this project is a function that takes the parsed records and
returns a list of Finding objects, nothing more. If you are adding a new
kind of check, that usually means a new analyzer module rather than
adding logic to an existing one.

If your change affects the scoring or the analyzers, update
`web/index.html` to match, the JavaScript engine there is meant to behave
identically to the Python one. Running `node scripts/verify_web_demo.js`
after a change confirms the two still agree.

Add tests for anything you change. The existing suite is a good template,
each analyzer has its own test file under `tests/`, built around small
CSV rows constructed with the `record()` helper in `tests/helpers.py`.

## Before opening a pull request

```bash
pytest
node scripts/verify_web_demo.js
```

Both should pass. Please also keep documentation free of unnecessary
punctuation and jargon, the goal of this project is that a non specialist
can read the plain report and understand exactly what to do next.

## Reporting a bug

Open an issue with the CSV row (with any real names replaced) that
triggered the unexpected result, and what you expected to see instead.
That is normally enough to reproduce and fix the problem quickly.
