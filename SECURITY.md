# Security

## How AccessLens handles your data

The command line tool only ever reads the file path you give it. It does
not open a network connection, does not phone home, and does not write
anything to disk unless you pass `--json` to ask for a saved report.

The browser demo runs entirely on your own device. The CSV you paste or
upload is read by JavaScript already loaded in the page and is never sent
to a server, there is no backend for this project at all, the whole
analysis, scoring, and report rendering happens in your browser. You can
verify this by opening your browser's network panel while using the demo,
or by reading the source directly in `web/index.html`.

## What kind of data this tool is meant for

AccessLens is built to review identity and access exports, records that
typically contain names, email addresses, and the systems and permission
levels a person holds. Treat this the same way you would treat any other
export from your identity systems, only run it against data you are
authorized to review, and only through channels your organization
approves of. The live demo is convenient for testing with sample data or
your own export on your own machine, but if your organization requires
reviews to happen inside a specific approved environment, run the command
line tool there instead.

## Reporting a security issue

If you find a security problem in this project, please open an issue on
GitHub describing the problem. As this is an independent portfolio
project rather than a commercial product, there is no formal disclosure
program, but any report will be looked at and addressed.

## Dependencies

The Python package uses only the standard library, there are no third
party runtime dependencies to track for vulnerabilities. The test suite
depends on pytest, listed in `requirements-dev.txt`. The browser demo
uses no external libraries at all, everything it needs is written into
`web/index.html`.
