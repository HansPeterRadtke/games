# HPR Input Compatibility Audit — internal candidate

The **Input Compatibility Audit** is an Editor-only, read-only preflight for projects migrating between Unity's legacy Input Manager and the newer Input System. It does **not** convert, repair, or modify project assets. The only permitted write is an optional JSON report that you explicitly export to a new file.

## Use in Unity

After importing the package, open **Tools > HPR > Input Compatibility Audit**. Choose **Scan input compatibility (read only)** to inspect the current project. The window reports whether the global input mode is **Legacy only**, **New only**, **Both**, or **Unknown**, and which Input System package version is declared in `Packages/manifest.json`. It lists potentially incompatible runtime C# API calls in `Assets`, with source file and line. Click a source finding to open that script at the reported line. **Export report as JSON** is disabled until a scan has run; selecting it opens a save dialog and refuses to overwrite an existing report.

The scanner recognizes common old `UnityEngine.Input` methods and properties, plus local `using Alias = UnityEngine.Input;` aliases. It also checks potential newer Input System references under legacy-only settings. The branch analyzer handles `#if`, `#elif`, `#else`, `#endif`, Boolean `!`, `&&`, `||`, and parentheses, including known Unity input defines and unknown symbols. Known inactive and Editor-only code is excluded. Comments and multiline ordinary, verbatim, and raw string literals are masked. Possible calls in interpolated expressions are marked **REVIEW**, not asserted executable.

If any **custom active Build Profile** is selected, the scanner reports **Unknown** plus `ACTIVE_BUILD_PROFILE_OVERRIDE`: that profile may override the global settings, and Unity does not expose a stable public property for the effective input backend in this tested Editor version. Inspect **File > Build Profiles > Player Settings**, then run an actual Player test. The scanner never switches profiles or input backends.

## Limits and safety

This is a **heuristic**, not a Roslyn compiler, full dependency graph, runtime test, or guarantee of compatibility. It can miss project-wide `global using` aliases, reflection, dynamic calls, complex custom defines, C# embedded source, external UPM or DLL assemblies, and scene EventSystem components such as `StandaloneInputModule`. It can also report false positives. Unknown branches are flagged for review rather than automatically deemed safe. Each source file is limited to one megabyte, the scan to ten thousand scripts, and the visible finding list to one thousand entries; exceeded limits make the audit explicitly **INCOMPLETE**. No project settings, scenes, code, packages, or existing report files are changed by scanning.

Actual native validation was performed with Unity **6000.6.8f1**, including a URP project with the new Input System only. Earlier Unity versions, real graphical navigation, custom active-profile overrides on all target platforms, and independent buyer acceptance remain release gates. This file describes an **unpublished development candidate**. License, pricing, marketing assets, and marketplace approval have not been established.
