# Showcase pointer aiming in the Linux Player

On November 11, the standalone showcase logged a camera warning whenever the new Input System reported an available mouse with non-finite coordinates. In the headless Player both coordinates were NaN. In a rendered Player a custom input source could trigger the same warning with a single NaN or infinity. The showcase now checks the position at the point shared by the native and injected input sources, before it calls `Camera.ScreenPointToRay`. Missing or invalid positions leave the character facing its previous direction. The next valid position can turn the character immediately.

## Native regression

The baseline was the exact private [save-slot candidate](save-slot-integrity-2026-11-10.md). Its previously built Player produced one frustum warning with null graphics and zero with software OpenGL during a normal save. A frame-by-frame probe on the same package produced thirteen warnings headless and eight with OpenGL. The headless count included five from the native mouse. Disabling the showcase, reporting an absent pointer, or supplying finite coordinates produced zero warnings. An initial rendered diagnostic timed out waiting for window focus. The completed rendered baseline used the same binary with its private window focused.

Both Unity 6000.4.0f1 with legacy input and 6000.6.7f1 with the new Input System imported the corrected package and built its actual showcase scene. Each Player passed six headless and ten rendered cases. Invalid input left the character's orientation intact. In the rendered cases, real X11 mouse movements to opposite sides of the character reached each input backend and turned the character toward both targets. None of the four Player logs contained the camera warning. The rendered tests used Mesa software OpenGL at 960 by 540 in the Built-in Render Pipeline.

The private candidate changed one packaged C# payload. All 161 asset identities and metadata files matched after each import and build. Its SHA-256 is `5d0f9d0732ac439a817080d2103e636e2f60e32552f812b83709c9c142e46eb3`. The source templates retained their original 435 and 552 files. Evidence is under `/data/var/marketplace-account-setup/hpr-showcase-camera-20261111/` on Nitro.

## Gameplay and buyer controls

A separate Unity 6000.6.7f1 build contained the shipped showcase and an Editor-only builder, with no runtime test probe. In a 1280 by 720 software-rendered window, the real Pause and Reset buttons worked. The Enemy attacks button took the player from 100 health to 92. Moving the desktop mouse onto the training target and pressing F reduced enemy health from 60 to 45 and ammunition from six to five. Aiming at empty floor and pressing F again reduced ammunition to four and left enemy health at 45. The rendered HUD shows each transition.

The first optical check sampled a frame still showing a live enemy after a Pause click. Waiting for the rendered state on the very same executable confirmed the button works. A private experiment with additional button handling was discarded. The regression now exercises a canceled drag, Pause and Resume on the existing controls. All three passed on the new Input System. Together with the pointer cases, this gives 19 passing cases on 6000.6.7f1 and 16 on 6000.4.0f1. The three extra button cases were run on 6000.6.7f1.

The optical walkthrough stopped before clicking Save when text recognition misread the button. A capacity request for a fresh walkthrough was denied. A separate request for another legacy stock Player build was also denied. The save evidence comes from the packaged save fixture. Its writer stored 92 health and five rounds, its cold reader restored those values, and its damaged-slot reader kept 100 health and six rounds. All three exited zero without a frustum warning. The slot and its neighboring file passed their independent byte checks.

The null-graphics and software OpenGL configurations have distinct display requirements. With no display server, the 6000.6.7f1 Player passed the six headless cases. The 6000.4.0f1 legacy Player crashed before its first case without X. An independent 6000.4.0f1 empty scene with no suite code reproduced the same native crash between Awake and the first Update. The identical empty-scene binary completed eight frames under Xvfb with the null graphics device. The runner provides a private X display in both configurations.

## Release source comparison

The repository passed 340 Unity checks. A private integration copy with all fourteen existing commercial-worktree edits applied passed 342. The original commercial files kept their byte hashes.

The current release builder can account for 132 of the 133 packaged file payloads from source. Of those 132, 125 match byte for byte. The seven differences are the ability resource adapter, the showcase scene builder, the Integration Guide, the three top-level guides and the abilities module README. The tested package scopes material saves to owned assets and rechecks sample copy destinations before creating files. Those protections differ from the current commercial source. The eighth file, the selected-ability installer, has an exact source copy under `qa/AbilityDefinitionSafety/`, but the release builder does not stage it. Its metadata is also absent from the staging sources. The other 160 metadata files match byte for byte. Source reconciliation is needed before a fresh commercial export can be treated as the tested package.

## Reproduce the pointer checks

Use a disposable project imported from the pinned package. Check it with `qa/unity_imported_archive_identity.py`. The paths below are relative to `unity/tools/release/gameplay_suite`.

1. Copy `qa/SaveSlotPlayer/SaveSlotPlayerBuild.cs` into the disposable project's `Assets/Editor/` and `qa/PointerAim/PointerAimPlayerProbe.cs` into a new private folder under `Assets/`. Keep both outside the vendor package.
2. Create an empty output directory. Set `HPR_SAVE_PLAYER_BINARY` to an unused absolute path inside it. Run the matching Editor with `-batchmode -nographics -quit -projectPath <copy> -executeMethod SaveSlotPlayerBuild.Run -logFile <build-log>`. Require exit zero and `HPR_SAVE_PLAYER_BUILD_PASS` in the log.
3. Run `python3 qa/PointerAim/run_pointer_player.py --binary <player> --output <new-results-directory>`. The runner uses Xvfb, xdotool and Mesa software OpenGL. It starts a private display and two fresh profiles. It checks the Player exit codes, every expected case, the final summary, and the full logs. The results directory retains the logs and `result.json`.

URP and independent buyer acceptance remain open.
