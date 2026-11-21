# Package Boundary Inspector — desktop Editor screen-question contract

Mode: **audit**. The user is a Unity publisher deciding whether an explicitly
selected package folder has known dependencies not included in its export.

Primary questions visible without scrolling: What folder am I checking? Did
this scan finish or remain incomplete? How many known external asset/package
references must I review before shipping? A clean **resolved-reference** scan
must never be described as a complete clean-install certification.

Secondary questions: Which authored asset depends on which external asset?
What should I disclose or include? Which Unity Registry/third-party packages
need independent install/license checks? The detailed per-asset findings belong
in a scroll region; raw JSON is manual export only.

Trust states: No root selected; ready to scan; scan running with meaningful
counted-assets progress and user cancellation; completed with findings;
completed with no *resolved* external references; incomplete due to scan cap,
error or cancellation. Scan status, dataset scope and limitations must remain
visible even if the list is long. No automatic scanning at import/editor launch.

Actions: Choose source folder using Unity object selection; read-only Scan;
cancel an ongoing lengthy scan; optional export to a **new** JSON file. No
asset modifications, automatic fixes, destructive actions, network activity,
package installs, uploads, prompts for credentials, or telemetry.

Acceptance: Native Unity 2022 LTS and Unity 6 independent imported archives;
positive external-prefab dependencies; negative contained dependency; scan
truncation; canceled run; create-only export. GUI min-window, long-path
truncation, progress responsiveness, error/empty/ready states, resized layout,
keyboard and manual screenshot inspection remain **unverified** until genuine
non-batch graphical Editor access and calibrated visual checks are available.
Never substitute an invented or black screenshot for this acceptance.
