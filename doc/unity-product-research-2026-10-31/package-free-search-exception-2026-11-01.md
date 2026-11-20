# Unity 6.6 Editor Search indexer exception — package-free control

November 1, 2026. No claims about a Unity engine patch or exact root cause.

Earlier actual Unity six point six Play mode logs for HPR v14 recorded
`ArgumentOutOfRangeException` with a stack in
`UnityEditor.Search.SearchDatabase.EnumerateAll` and
`UnityEditor.Search.SearchInit.IndexationOnStartup`. Gameplay tests still
passed. A cleanroom package-import compile that did not enter Play mode did
not reproduce the exception. Until this control it was possible that the
HPR scripts or Editor integration were contributing to startup failure.

## Independent control

A **new, isolated copy** of a real Unity 6000.6.7f1 customer fixture was
taken **after HPR uninstallation**. This project had no
`Assets/HPRGameplaySuite` directory or remaining vendor source scripts.
The original controller, scene, prefab, serialized settings and project
configuration remained present. No application, licensing, publishing, or
other original source files were modified by the QA script.

A private Editor-only test, `HprPackageFreeSearchIndexerProbe.cs`, opened
the original non-HPR customer scene, entered real Unity Play mode and
verified the customer player still existed. A fresh Unity process exited
zero, writing a receipt with:

- `vendor_root_absent=PASS`
- `unrelated_customer_scene_valid=PASS`
- `real_unity_editor_play_mode=PASS`

The same log independently contained
`ArgumentOutOfRangeException: Index was out of range` from the same
`UnityEditor.Search.SearchDatabase` indexer stack at Play-mode startup.
There were zero C# compile errors. Full original machine evidence:
`/data/tmp/hpr-caltask33-20261101-0903/package-free-playmode-search-20261101.unity.log`
and `package-free-playmode-search-20261101.txt`.

## Interpretation

The failure **reproduces without HPR source**, ruling out a necessary
dependency on the installed HPR suite for this particular occurrence.
It remains possible that unrelated Unity Editor version, local search
index/database state, headless Editor operation or other packages/settings
contribute. No one of those causes has been independently isolated.

Do not treat this package-free reproduction as proof that every future HPR
Editor log is clean, nor hide actual package-origin exceptions. The
separate Unity HPR gameplay checks themselves passed; this indexer problem
is retained as an **independent Editor environment diagnostic**, with a
suggested follow-up of reproducing on a completely fresh package-free
Unity 6.6 project with indexation and GUI state controlled. Do not delete
or rewrite earlier negative logs.
