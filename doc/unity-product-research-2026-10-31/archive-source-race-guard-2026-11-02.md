# Unity private archive source-integrity race — 2 November 2026

An independent audit of the private deterministic Unity QA archive builder found a concrete time-of-check/time-of-use weakness. The builder hashed the frozen and proposed source trees before reading replacement C-sharp assets, but did not verify that the later bytes still matched those earlier hashes. A concurrent source edit could therefore produce an archive different from the source version that was originally verified.

A new test-first regression in `tests/test_unity_private_qa_archive_build.py` uses its own disposable input files, simulates a source edit immediately after inventory, and requires a ValueError **before any output archive is created**. It failed against the prior builder and then passed after a targeted correction.

The updated builder re-hashes both the frozen baseline and the proposed replacement source content at the exact point of reading each authorized asset, and refuses the build if either differs from its initial snapshot. All **eleven** isolated archive-builder tests now pass. No owner/other-agent source files were modified.

A completely new read-only QA rebuild from the real frozen Unity source and the seven approved proposal files succeeded. It was compared byte-for-byte against the earlier, separately stored candidate and produced the identical SHA-256 `1d565d600baefa1decf62ea44452f5976706e15b93effbbfa63beafef8c22ad0`. The archive contains **161 assets**, with exactly seven reviewed source/doc payload substitutions. The new, independent test receipts are preserved under `/data/tmp/hpr-unity-seven-source-postrace-check-20261102`.

This is static archive provenance, not a native Unity Editor import or Play-mode acceptance. The already-running resource-broker job remains responsible for the outstanding URP/new-input test. Marketing, human buyer value and Unity publisher acceptance remain **NO-GO**. No publication or purchase occurred.
