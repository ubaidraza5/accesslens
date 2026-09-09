# Development Notes

A record of the real problems I ran into while building AccessLens, and how
I solved each one. I am keeping this because these are exactly the kind of
issues that come up in a real access review or audit engagement, catching
them here was good practice, and it is honest to show the working, not just
the finished result.

## A single critical issue was not being scored as urgent enough

The scoring model gives every finding a weight based on its severity, and
adds them up into a score out of 100 for the whole company. Early on, a
company export with exactly one Critical finding, for example one
terminated employee still holding admin access, only scored high enough to
read as Medium overall, because a single finding's weight was not large
enough on its own to cross the Critical or High point thresholds.

That is the wrong answer for a reviewer. One account left over from a
departed employee is a real problem on the day it is found, it should
never be filed under Medium just because nothing else is wrong yet.

The fix was to add a severity floor on top of the point total. Any
Critical finding now pulls the whole company level up to at least High,
and multiple Critical findings, or enough total points, still push it all
the way to Critical. The point total and the floor are combined by taking
whichever reads more severe, so volume and severity both get a say instead
of one hiding the other. I added a dedicated test for this exact case, a
single Critical finding, to make sure the floor logic never regresses.

## The score looked right but was unreadable in the browser demo

The browser demo shows the company score as a circular gauge, a colored
ring with the number in the middle. Once I tested it with a Critical
result, the ring filled the whole circle with red, and the number in the
middle disappeared, because I had set the number's text color to the same
red as the ring behind it. It was correct data, rendered invisibly.

I fixed this by turning the gauge into a proper donut shape, a colored
ring with a plain white circle cut out of the middle, and put the number
on that white circle instead of directly on the color. The fix took a
small CSS change, wrapping the number in its own inner circle element with
a white background, but I only caught it because I actually looked at a
screenshot of a Critical result instead of just trusting the numbers.

## A mistyped separator silently broke the privilege check in the browser version

The JavaScript version of the privilege check groups people by their
department and system, so it can tell if one person stands out compared to
their team. To build a unique key for each group, I combined department
and system into one string, and meant to put a clear separator between
them, but a stray character ended up in the file instead, so two
completely different groups, like IT and Console versus ITC and onsole,
could end up sharing the same key by accident.

This is the kind of bug that does not throw an error, it just quietly
produces a slightly wrong grouping, which is worse than a crash because
nothing tells you to go look for it. I caught it by comparing the raw
bytes of the file, not just what an editor displayed, since the stray
character did not render as anything visible. Once I saw it in a hex dump
I replaced it with an explicit, visible separator and re ran the parity
check described below to confirm the JavaScript and Python versions still
agreed on every test case.

## The JavaScript demo and the Python tool could have quietly drifted apart

AccessLens ships two implementations of the same analysis, a Python
command line tool and a JavaScript version that runs in the browser demo.
Keeping the logic identical by hand, across two languages, is exactly the
kind of thing that drifts over time as one side gets a small fix the other
does not.

Rather than trust that by eye, I wrote a small Node.js script that pulls
the exact script block shipped inside the web demo, runs it against the
same fixture files the Python test suite uses, and checks that both sides
produce the same score, the same risk level, and the same count of
findings at every severity. That script now runs in continuous
integration on every change, so the two versions cannot silently disagree
without the build failing.

## The automated tests failed for a result that was actually correct

The command line tool is designed to exit with a nonzero status when the
overall result is High or Critical risk, on purpose, so it can be used as
a pass or fail gate in another script or pipeline. When I first wired up
continuous integration, the test steps that ran the tool against the
sample company, which is deliberately Critical, immediately failed the
build, because the automation platform treats any nonzero exit code as a
failed step by default.

The tool was behaving exactly as designed, the test around it was wrong.
I fixed the affected steps to expect that nonzero exit and treat it as a
pass, while still failing the build if the tool ever unexpectedly returned
success on a Critical export, which would indicate a real regression in
the scoring logic. It is a good example of a test needing to understand
what correct behavior actually looks like, rather than assuming success
always means a zero exit code.

## GitHub Pages did not go live on the first push

After pushing the site for the first time, the live demo returned a
site not found page. The repository setting for GitHub Pages defaults to
Deploy from a branch, with no branch chosen, which leaves Pages disabled
even once a deployment workflow exists and runs successfully. The fix was
switching that setting to GitHub Actions as the source, after which the
next push deployed normally. I now check that setting immediately after
creating a new repository, rather than after wondering why the site is not
loading.

## What this adds up to

None of these were exotic problems, a scoring edge case, a rendering bug
only visible with the right data, a typo that produced no error message, a
test that assumed the wrong thing, and a repository setting that is easy
to miss. That is a fairly accurate picture of what real review and audit
work looks like too, most issues are not dramatic, they are small,
specific, and only found by actually checking the output rather than
assuming it is right.
