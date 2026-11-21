# FBX Clip Identity Audit — native Unity Editor screen contract

Screen: FBX animation clip identity check. Mode: read-only diagnostic.
Primary user question: are any imported FBX models known to have duplicated
AnimationClip subasset internal IDs that could make clips unassignable?
Secondary questions: which original FBX path has it, which two clip names
share the numeric ID, what must be verified manually in a disposable project?

Primary view must always include: overall status, actual number of imported
FBX models scanned, affected-model count, number of duplicate IDs, and visible
INCOMPLETE/error state before any detailed rows. Scan starts only by explicit
user action; progress indicates inspected models and can be canceled. The
normal no-problems state is restricted to *checked serialized internal IDs*
and is not a guarantee that a model imports correctly or will stay safe after
reimport. An empty project must not be called a verified clean project.

Default UI avoids raw meta YAML or unbounded all-model tables. Only affected
or incomplete models appear in the scroll area; detailed full JSON is manual,
create-only export. Never overwrite user files or mutate FBX/metadata. The
model's output is always advisory and cannot fix IDs automatically.

Native acceptance: author and fresh consumer import in Unity 2022.3 and Unity
6.6, original Blender animation loaded, actual split clips with serialized
internal IDs, deliberate synthetic duplicate positive and distinct negative,
model-counting, cancellation, untouched user bytes and exact archive scope.

Graphical acceptance remaining until actually observed: real non-batch native
Editor window, at least 660 by 390 minimum size, non-clipped title/buttons,
readable status and long model paths, keyboard focus, responsive scan progress,
error and empty states, normal screenshot/crop brightness and useful content.
A consent/software-terms dialog must never be bypassed by this QA.

## Unsupported conclusions (internal training and seller guidance)

A result of `NO_FBX_MODELS_SCANNED` means the checked project had no eligible
FBX sources. A result without duplicate IDs covers only currently serialized
ModelImporter ID tables, not whether a model's animations imported correctly.
Unrecognized or ambiguous metadata is marked incomplete rather than passed.
This tool is *not* an automatic GUID fixer, animation resampler, FBX retargeter,
clip naming tool, or warranty against Unity-import bugs in future versions.
