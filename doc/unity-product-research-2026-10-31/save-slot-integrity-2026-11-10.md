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
Those runs cover local filesystem behavior in Linux batch Editors.

## Standalone Linux Player

The private fixture in `unity/tools/release/gameplay_suite/qa/SaveSlotPlayer/`
builds the shipped showcase scene using the installed Linux Editor. It places
its Editor builder and runtime probe in a disposable clone after checking the
installed archive against its SHA-256. The probe calls the same save and load
methods as the demo buttons. Fresh Player processes use an isolated Unity
profile and the normal default slot path. The harness compares the JSON on
disk with the state observed by the writer and the reader.

To reproduce on Nitro, run `run_player.py` through the resource broker with
`--template` pointing at a verified imported project, `--archive` and
`--sha256` identifying its exact package, `--editor` naming the installed
Unity executable, and `--output` naming a fresh directory. The run retains
the Player build, Unity logs, two private profiles and a JSON result.

On November 10 the native Unity 6000.6.7f1 Linux build succeeded with the
new Input System. The first Player started at 100 health with six rounds,
took one hit, fired one round and saved. A second Player started at 100 and
six, loaded the default slot, and restored 92 health and five rounds. The
saved JSON independently contained 92 and five. Loading preserved its bytes
and the neighboring `.writing` file. A third Player loaded deliberately
truncated JSON in a separate profile. The game refused the load, kept 100
health and six rounds, and left the damaged slot intact. All three processes
exited zero.

All 435 template files and all 437 staged input files matched their pre-build
hashes. Unity added only three fixture metadata files. The complete vendor
package verification still passed for 161 asset paths after the build. All
335 repository Unity tests passed. The logs, result and built file hashes are
in `/data/var/marketplace-account-setup/hpr-save-player-20261110-night/attempt-final/`.

All three headless Player runs logged a camera frustum diagnostic with
non-finite screen coordinates. Its cause and its behavior with a graphics
device remain open. The build also emitted known analyzer warnings from the
private Editor control. This result covers the Linux showcase save workflow.
URP, rendered buyer usability, independent buyer validation and reconciliation
with the commercial worktree remain open.

The [November 11 pointer-aim regression](showcase-pointer-aim-2026-11-11.md) traced the camera diagnostic to a non-finite pointer and verified the correction in both Linux input backends.
