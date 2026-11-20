# Private no-product Editor startup control

This is independent QA and is never included in the buyer archive. It creates a
new Unity project through the installed Editor, adds one static private observer,
lets startup / optional two Play sessions run, and records native process exits,
assembly absence, actual graphics API, observed time and original-file preservation.
It never imports HPR. Use the real-package workflow driver separately for that.

Run `run_clean_control.py --help` through an owner resource-broker job with CPU,
memory and wall-time caps. Every output must be a NEW folder under the private
marketplace runtime; never replay a completed or uncertain project. `--graphics`
requires an explicitly owned Xvfb display and observed OpenGLCore; use software
Mesa to avoid other owners' GPU work. `--input-system` explicitly configures the
official 1.20.1 package only in this new control and completes native resolution
before hashing originals. `--play-cycles --disable-domain-reload` observes two
sessions. `--settle-before-play` records at least twenty Edit seconds first.

CONTROL_VALID is validity of the experiment, not an error-free Console verdict.
Read search_exception_seen independently, inspect the actual associated stack,
and do not equate a healthy startup-only control with a Play-mode workflow.
Read the dated startup-control report for six real native results and limitations.
