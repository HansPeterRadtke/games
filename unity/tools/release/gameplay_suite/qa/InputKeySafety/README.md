# Focused native integrated-suite keyboard regression

This private QA code tests the actual archived HprSuiteUnityInputSource public
IsPressed/WasPressed APIs. It is not shipped in the buyer archive and does not
simulate OS keyboard input. Run only through an owned, bounded resource-broker job
against a new private project copy. No GUI software-terms interaction is performed.

The create-only driver requires an explicit template, installed Editor, archive
checksum and fresh private output. A successful matching actual-native import
receipt may reuse an exact imported template after verifying all 55 product scripts.
Otherwise it launches a separate native archive import before staging the probe.
Source templates stay unchanged; protected customer files and exact product source
are checked after execution. Output inside the template or outside private runtime
is refused. Only the copied project's domain-reload-off flags are configured before
its baseline; the original project settings are never changed.

The probe waits for settled startup, opens an unsaved empty scene, enters Play mode
and queues Input System KeyboardState events. A raw held-key and key-down control
must be active for every observation. It tests six positive mappings (A, Alpha1,
LeftControl, Return, KeypadEnter, Keypad0), three intentional keyboard exclusions
(None, Mouse0, JoystickButton0) and three undefined serialized KeyCode values
(18, 50000, -1). On the tested version, undefined legacy value 18 numerically aliases
new-system Key.D; the probe validates that precondition rather than assuming it.

Acceptance requires all twelve distinct case names, independently fixed positive/
negative expectations, actual native held/edge controls, matching mapped results,
no exceptions and native exit zero. Project/source preservation and all 55 archived
scripts also gate PASS. A fabricated all-false control receipt is rejected. The
probe removes only its own simulated device and restores the process-local Input
System settings before leaving Play mode and exiting.

The first Edit-mode attempt failed its positive controls. It is retained as an
inadequate harness attempt, not a valid product negative control. Corrected Play-mode
red and green results have the exact same final probe source. Their outcomes and
archive identities are recorded in the dated November 7 report. No physical device,
URP visuals, Player build, exhaustive keyboard layout, legacy key event behavior or
commercial readiness follows from this focused test.
