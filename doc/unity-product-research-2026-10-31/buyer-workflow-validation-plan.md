# HPR Unity Suite — expert developer onboarding, Editor UX and validation contract

Dated 2026-10-31. **Research design**, not built UI or claimed user-tested result. Based on owner Infra GUI, configuration and programming rules, original Unity 6 UI Toolkit/ScriptableObject/C# style guides and observed competing Unity tools. The purpose is to define **what an actual buyer needs** before another C# refactor.

## Actual targeted buyer

A developer with years of Unity/C# experience and an already functioning game or tool, with personal controller, inventory, scene organization and version-control conventions. They are not seeking a replacement character engine or a scripted 'hello world'. They may use URP, old/new Input System or an existing Asset Store framework and may have uncommitted editor work; loss of unsaved scenes, conflicting scripts or surprise asset changes is unacceptable.

The buyer's purchase decision is based on whether their next developer task becomes *measurably quicker, safer and easier to maintain*, not raw module count. A hypothetical beginner who can follow our built-in arena but cannot insert the code into a real project is insufficient validation.

## First-use contract: ordered decisions, not a dashboard full of diagnostics

**Entry (under ten seconds after an import completes):** opening `Tools > HPR > Gameplay Suite` should reveal one short, scannable surface with the actual imported version, current Unity version, active render pipeline and input handling, and explicit buttons for `Open demo`, `Configure in my game`, `Validate project compatibility`, `Read docs`. Do **not** create a modal popup automatically on Unity launch/import. Navigation to the product from the existing Inspector and Project Browser should be discoverable.

**Read-only compatibility check:** first question is 'Will this interfere with my project?'. The diagnosis must check duplicate assemblies, colliding package paths/GUIDs, Unity/package versions, unsupported input backend and render pipeline, existing scene references, and data schema/asset collisions. It must not modify the project or install any Registry package. Findings need seriousness (blocker/warning/information), affected asset(s), evidence and recommended action with 'Open affected asset' and 'Copy report' controls. All scans display honest progress or indeterminate phase; cancel is available for expensive discovery. Zero issues reported is **not** a claim of a successful game runtime test.

**Demo entry:** opening the demo must ask permission before switching from a dirty unsaved Editor scene. Default open operation is read-only. If demo sample assets are missing, offer a copy into a **new** destination, not blindly overwrite old files. Show a visible small 'what to try' path and the relationship of each gameplay action to the actual module API. A proper example must include ability, stats, inventory, combat, saving, interaction and world metadata with end-to-end causal states, not only geometric decoration.

**Configure into existing game:** expert developers should pick **which subset** of modules to integrate, rather than adding ten regardless of need. For each configurable module, display the relevant options in the normal Inspector with units, valid constraints, side effects, a link to minimal example and a one-click, reversible test fixture. Plug-in does not replace the existing controller/camera, invent global scene managers, or mutate unrelated prefabs/ScriptableObject definitions. A configuration preview and explicit Apply/Cancel should be used for bulk changes.

**Changes and verification:** after configuring an ability, show outcome instantly in the Inspector/demo, and offer a meaningful test rather than 'test succeeded' based on a compilation check alone. Report exact checks run, original selected assets, whether play entered, runtime transition observed, and any material unsupported target state. Advanced source/test API is linked nearby, but not forced into the primary editor experience.

**Safe update/uninstall:** detect existing HPR version with an API/serialization migration preview. Preserve customized assets, user copies and prefabs. Never overwrite without explicit confirmed scope. Give an audit/diff and rollback instructions; uninstall must not delete any user-owned scene or unrelated package. Long background work must not become owner-invisible.

## Per-module configuration contracts (proposed, not implemented)

Store gameplay *definition* data in ScriptableObject assets; use separate per-session runtime state and schema-versioned storage. Changing a tuning field in Play Mode should have predictable semantics and not silently persist unintended runtime modifications into source assets.

Player movement config: speed **meters per second**, default and allowed domain documented; camera/aim policy; collision layers; old/new input provider. Validation includes engine backend availability and mutually exclusive input modes.

Interaction config: proximity radius **meters**, raycast/nearby mode, layer/occlusion mask, priority/selection behavior and prompt formatting. Distance tie-break and error feedback documented.

Weapon config: damage amount **points**, fire interval **seconds**, range **meters**, magazine/reserve max **count**, projectile or hitscan mode, spread angular units, collision layers and damage/ally filtering. Never silently treat a missing range as unlimited/zero. Validate derived constraints and saved ammo bounds.

Enemy config: named deterministic strategy, chase and attack range **meters**, move speed **meters/second**, attack cooldown **seconds**, obstruction mode, attack behavior and time policy. Mark pathfinding as 'not provided' until shipped with real tests.

Ability config: resource cost **stamina points**, cooldown **seconds**, optional target group, radius **meters**, effect registry with supported effect types, ability activation state and failure reasons. Each additional effect type must be supported by tests and an example.

Inventory config: known item IDs, uniqueness, item max stack/capacity and quantity **count**, unknown item recovery and serialized key/version identity. A failed operation must leave quantities unchanged, and events should report results rather than implied success.

Save config: explicit schema, slot name, path policy, local/cloud capabilities (unsupported controls disabled), backup/atomic replacement platform checks, migrations, maximum payload bytes and corruption response. A confirmation message must distinguish memory snapshot, on-disk write, and restored state.

Every field must specify the semantic owner, default, range, units, cross-constraints, change likelihood and persistence/override policy; only expose values customers plausibly need. Example: `attackRangeMeters <= chaseRangeMeters` for the demo chase configuration unless a documented alternative mode is selected.

## Unity Editor implementation design constraints

- Use public Unity editor APIs, not internal reflection, for tool integration. Prefer normal `SerializedObject` / `SerializedProperty` binding where Unity's Undo, prefab overrides and multi-object editing are supported; never directly set serialized fields in an inspector callback if doing so bypasses Undo or constraints.
- UI Toolkit: UXML is structure, USS reusable style, C# is event/data handling. Keep a semantic namespace/prefix for USS classes to avoid collisions with user assets. Avoid hardcoded pixel layout and UI-specific business logic. Use `ListView` virtualization for scalable item collections, and observed-data binding rather than redraw-every-frame polling when possible.
- If the Unity Editor executes any costly project scan, provide progress with determinate count only if measurable, cancellation, and an explicit completed/partial/failed result. Recording source progress should never be fabricated from guesses.
- Error text: identify what failed, what the system tried, evidence/location, and the smallest safe correction. Explain missing dependency or incompatible setting specifically rather than claiming user mistake or simply logging an exception.
- Release/preview: separate Editor and Runtime assemblies; expose optional samples and tests without injecting dependencies into runtime. Keep the code usable without the editor panel where possible, and test without external GUI state.
- Cross-version: no obsolete public APIs in current target; a build must compile and operate on both installed Unity 6.4 and 6.6, including domain reload disabled. URP compatibility tests must actually render the demo and confirm material/shader support, not just compile.
- Dark/light theme, narrower docked Inspector, high-DPI scaling, keyboard navigation, large font mode and cross-platform source paths must be exercised with real screenshots and interactions. No unchecked focus/keyboard trapping.

## Measurable acceptance with expert users

Recruit a small diverse sample (initial target eight experienced Unity developers; even fewer can reveal usability defects but cannot establish market size), with existing C# projects and differing pipelines/input backends. They are not coached through our code.

Use three tasks: integrate a damage event without replacing the player, configure a new ScriptableObject-based ability, and restore a complete encounter then safely undo the integration. Compare with equivalent open-source/Asset Store alternatives on the **same project and actual Editor version**, record observed time to working behavior, error recovery, source edits, lost changes, support/documentation visits, and number of unintentional project modifications. Price/intent questions follow concrete successful tasks; do not infer conversion from subjective enthusiasm.

Hard pass thresholds proposed for testing, not measured: no unexpected original asset mutations; first demo plays after clean import on documented target setup; an engineer can complete a documented new ability/interaction without editing HPR internal source; failed configuration is surfaced with a valid correction and no partial state; canceled bulk operations leave exact pre-operation files; all claimed paths work on the supported Unity/input/render combinations; installer and help are discoverable without instructions from the experimenter.

Collect qualitative observation: what they expected a button to do, wrong guesses, surprising constraints, repeated clicks, skipped warnings, how they resolved errors, whether they trusted backups. Annotate design changes with exact source user task and follow-up measured effects, per Infra GUI testing rules. Do not claim UX success until this happens.

## Benchmark competitors and separate non-goals

Reference direct products: TopDown Engine and Game Creator 2 for broad gameplay workflow; Ability System Kit and Ultimate Inventory System for focused module depth; Modular Conveyor Belt System for low-price editor polish and guided scenes; Unity official Asset Store Publishing Tools / Test Framework for first-party validation; PackageLens and Release Check Pro for project import/diagnostics. Do not recreate every feature. A competitive tool should win at one sharply defined task, not feature count.

Non-goals without a defensible product decision: full RPG engine, massive content library, generic event bus as SKU, general-purpose save framework, automatic user-project mass rewrites, dependency installation without explicit permission, AI agents in the buyer runtime, expensive enterprise digital-twin physics, all-platform compatibility claims without tests.

Buyer workflow remains a proposed hypothesis until real human and Editor acceptance; no source code or buyer assets were created based on this specification alone.
