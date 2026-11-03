# Existing-player ability installer: observed-screen contract

Screen: Attach one ability to an existing player (Unity 6000.6.7f1).
Mode: configuration, explicit scene action and reversible review.
Purpose: Decide whether the selected player, owned ability and existing resource
provider are ready, then attach or reverse only that scene change.

Primary questions and visible answers:
- Which object, owned ability and provider are selected? Three labelled native ObjectFields.
- Why is an action available or blocked? Visible contextual HelpBox and enabled states.
- What changes, is it saved, can I undo it? Action labels and scoped outcome text.
Secondary: Inspect the created runner in Unity's ordinary Inspector; inspect ability data.
Hidden: GUIDs, QA timings, resource-broker state and widget geometry stay outside the UI.
Trust state: Preview must not install anything; errors must remain visible; current selection
must match the acted-on object. Missing/stale references must disable or reject the action.
Actions: Preview is read-only. Attach is explicit and Undoable. Remove requires consequence
confirmation and Undo. Scene saving remains the buyer's deliberate action.
Representations: Native selection fields, wrapped explanatory text, contextual status and
normal Unity Inspector. No extra QA dashboard or synthetic product screenshots.
Rejected: clipped explanations/actions, hidden failure details, accidental scene saves,
a runner on the wrong actor, duplicated attachment, lost existing resource binding.
Acceptance: At minimum width and a wider window, inspect actual pixels and native layout;
exercise Attach with an observed X11 click and Undo/Redo with actual Editor shortcut input.
Observe the runner's serialized ability/provider/origin references, existing player fields,
scene dirty state and unchanged saved-scene bytes. Hash older assets/settings before/after.
Human-expert comprehension, physical keyboard, other themes/DPI and all input backends
remain separate gates. Software-GL Xvfb evidence is not a human buyer study.
