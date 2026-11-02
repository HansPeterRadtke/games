# Broker-supervised, CPU-admitted Unity 6.6 URP/new-input acceptance

Date: November 2, 2026. Nitro. This is **private QA**, not a seller
submission or a product update. The owner product branch remains
concurrently dirty; this task uses only the independent QA branch and
private, unique scratch projects.

## Actual problem

The frozen internal 161-asset selected-installer archive passed Unity 6.6
Built-in cleanroom and Unity 6.4 source import. It has NOT passed the
same archive's Unity 6.6 URP 17.6 plus new-only Input System 1.20.1
pipeline. Previous real Editor attempts timed out during Unity/Bee
assembly postprocessing **before** HPR source was imported, including
a package-free project created without a Unity Library cache.
Customer source and settings remained unchanged. Logs and snapshots
are preserved.

The central Raspi resource broker has reliable per-machine inventory,
atomic logical CPU/RAM/GPU leases and a local Linux job supervisor;
its default timer does NOT start/stop any program. It does not guarantee
CPU time. Actual Nitro sampled roughly 99 percent CPU activity across
eight logical cores, load around thirty and ten-second CPU some-pressure
around seventy percent. The current reserved CPU count was zero:
nominal schedulable cores are NOT physical idle cores. Trading, model,
browser and 3D processes are not owned by this Unity QA task and may
not be interrupted. A fresh secure miniature central broker reservation
and release were separately performed successfully; its grant does
not negate the observed CPU contention.

## Independent CPU-admitted retry worker

The new QA-only source is
`unity/tools/release/gameplay_suite/qa/unity_urp_broker_retry.py`
with test-first regression at
`tests/test_unity_urp_broker_retry.py`.
The initial test failed because the module did not exist. Seven
deterministic tests then passed, including resource gating, two
consecutive samples, source immutability, unique project staging,
refusal of unsafe symlinks, pinned archive SHA-256 and private atomic
status writes. Combined with prior checks this yields seventy
passing Python tests at this source revision. These are NOT
proof that real Unity's URP pipeline passed.

The worker is intended for explicit local launch through the EXISTING
owner-managed `resource-broker-job` supervisor (not a
separate Cloudflare/service endpoint). It first polls the actual Linux
CPU affinity, one-minute load and ten-second CPU pressure, deferring
every ordinary high-load sample without reserving CPU or GPU capacity.
It also refuses a sample while another real Unity Editor process is
running. Two consecutive acceptable readings are required.

Only when the CPU is genuinely less congested does it refresh the
central broker's Nitro report and request an actual secure, short-lived
logical RAM/CPU lease. A rejected or unverified grant is recorded
and NOT circumvented. Its one-use control token is saved only under
a private non-Git path, not included in status or this document.

If admitted, the worker creates exactly ONE **brand-new disposable
Unity project** from the pinned Unity 6.6 project settings, Packages
manifest/lock and URP renderer/volume assets, explicitly excluding the
historical Library cache and the HPR vendor source. It first opens
Unity without HPR, then snapshots the resulting nonvendor project
files, imports the exact immutable archived .unitypackage, and hashes
the pre-existing files again. It must detect the exact exported
selected-installer source. Only after a successful import will it add
private QA scripts and run the actual Unity Editor URP + new-only
Input System Play mode fixture, checking the real Keyboard frame
receipt, URP renderer activation and imported arena camera.

Each phase has a distinct durable log and exit-code receipt. A failed
or timed-out import is **NOT rerun in its same uncertain project**.
A failed test, a broker denial, archive mismatch, unsafe filesystem
path or unknown external effect ends in an explicit report for human
inspection, rather than a bypass or an invented success. The broker
only controls this task's own registered cgroup; no unowned process is
paused, killed or reprioritized.

## Actual activation and current status

A read-only run verified the real frozen release's checksum, detected
eight cores, nearly four runnable tasks per core and CPU pressure
around seventy percent. The decision was explicitly
`wait_for_cpu`, with **zero reservations made**. The
central lease service was independently proven working by one
tiny secure reserve/release transaction. An actual supervised retry
job should be launched only after this source is tested and committed;
its run-state and status must be independently checked, and only then
may it be described as running.

The broker job's initial waiting stage is intentionally low-CPU and
does not claim to make Unity faster under saturation. Its sole
purpose is to avoid repeating the known timeout while retaining
a safe, reproducible future acceptance window.

## Release and business status

Even if the exact URP test eventually passes, the current internal
archive remains NOT APPROVED / NOT PUBLISHED. Real experienced
developer comparison, source-level usability and visual design
review, actual dependent-game migration and safe uninstall, verified
AI provenance and publisher review remain open. No publication,
account, price or purchase operation is authorized by the QA worker.
