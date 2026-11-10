# Save slot integrity in the gameplay sample

On the previous private package, a save to `slot.json` overwrote an existing
`slot.json.writing` and moved it away. A second save with a multibyte string
could replace the last checkpoint with JSON too large for the loader to read.
The Unity 6000.6.7f1 negative control reproduced both defects. Its runtime
test exited one and recorded false for neighboring file preservation, oversized
UTF-8 rejection and previous slot preservation.

The storage helper now exclusively creates a fresh file in the destination
directory for each writer. It checks the encoded byte count before writing
and publishes a complete file by move or replacement. The loader reads a
bounded snapshot through one open file handle. The demo's save and load
actions report invalid data through their normal failure return and HUD.
The public methods and schema version three are unchanged.

## Verification

The exact private QA package has SHA-256
`2e8b5fdf0b10c7a267d1680176a67c831a695c4aea922647fa076eedca45acc9`.
Only the playground controller and snapshot storage payloads differ from the
prior pinned package. All 161 metadata entries retain their original bytes.

Both Unity 6000.4.0f1 (legacy input project) and 6000.6.7f1 (new Input
System project) imported the final package into separate disposable copies.
Each import and runtime process exited zero. The existing runtime smoke
validator passed all eleven groups. Its new save checks cover an existing
neighbor, UTF-8 sizes at the limit and one byte beyond, Unicode roundtrip,
two concurrent writes to a new slot, refusal of an empty slot through the
controller, and temporary file cleanup. The existing checks exercise the
encounter, disk and memory restore, invalid state and malformed JSON.
The private six point six control still produced its existing UAC0005
analyzer warnings during import.

Independent post-run comparison verified 133 asset payloads and 161 paths,
GUIDs and complete metadata payloads in both imported copies. All 433 tracked
input files in the six point six source project and all 550 in the six point
four source project retained their original hashes. The two intended vendor
scripts were the only existing files changed in either disposable copy.

The Python Unity suite initially had three failures that also reproduced at
the parent commit. The mock package importer had discarded every metadata
field except the GUID, preventing its PlayMode gate tests from reaching the
intended stage. The fixture now reads the actual archive metadata. A separate
negative control keeps the GUID and changes importer data, then checks that
the worker refuses to start the mock PlayMode run. All 335 tests passed with
`python3 -m unittest discover -s tests -p 'test_unity_*.py' -v`.

Nitro retains the private package, baseline and final native logs, receipts,
project hash inventories, imported package audits and regression logs under
`/data/var/marketplace-account-setup/hpr-save-slot-integrity-20261110/`.
The supported scope here is local filesystem behavior in Linux batch Editors.
The private package still needs broader Player and URP verification, graphical
buyer-workflow evaluation, independent buyer validation and reconciliation
with the dirty commercial worktree before release.
