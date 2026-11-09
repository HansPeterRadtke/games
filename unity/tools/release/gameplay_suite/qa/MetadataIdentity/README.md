# Private native same-GUID importer control

NativeMetadataIdentityFixture.Run is a negative-control fixture, never shipped in
the product archive. It refuses any project except the hardcoded disposable task
copy and refuses an existing result. It requires the packaged ability runner to
be an actual imported MonoBehaviour with default execution order. Through public
MonoImporter APIs it sets order 123, saves metadata, verifies the GUID is stable
and writes a separate native receipt. It never rewrites source or repairs metadata.

The native experiment must first prove that the exact pinned archive is installed,
snapshot all original project/customer bytes and stage this file only under the
copy's Editor folder. Run through a bounded owned broker job. Require native exit
zero and then independently compare all bytes: only the target vendor .meta may
change, plus the newly created private fixture .meta. The old verifier should
incorrectly pass; the fixed verifier must reject the changed metadata despite all
161 GUIDs remaining intact. The full upgrade preview must block the customized
vendor install. Retain this negative fixture unchanged as evidence.

The native .meta change is intentional QA, not a buyer migration or product fix.
No original game, archive, publisher action, graphical consent or rendered
acceptance is involved. See the November 9 metadata identity report for outcomes,
strict-byte-comparison limits and private artifacts. Do not replay a finished job.
