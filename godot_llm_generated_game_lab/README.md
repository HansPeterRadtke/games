# Your Mom — Model-Generated Godot Game

The live build is served at `https://nitro.jonnyontherun.org/llm_game/`. The current public build ID is `your-mom-stableanimator-rvm-alpha-v6`.

The game is generated from the prompt “Your Mom” and currently contains a Dining Room scene, ten visible scene assets, thirty executable model-authored actions, stateful inventory and stats, collision-aware movement, interaction, attack and use behavior, and five player animation clips: idle, walk, interact, attack and use.

## Player animation pipeline

The player no longer uses independent SDXL frames or generic text-to-video motion. StableAnimator receives the reviewed full-body player reference plus explicit OpenPose/DWPose control sequences for each clip. The walk cycle is validated by DWPose with all seventeen body joints detected in every source frame, an ankle-separation range above 0.4 frame width and visible counter-swinging arms. AntelopeV2 and full-image identity checks reject identity drift.

Each StableAnimator clip is then processed as a sequence by the official Robust Video Matting MobileNetV3 model. RVM recurrent state is preserved across every frame in a clip. Foreground RGB and alpha are resized in premultiplied-alpha space with Lanczos4 before being placed into the fixed 288×384 runtime frame. Godot loads the PNG sprite sheets, which preserve 8-bit soft alpha. GIF files are only browser inspection previews because GIF transparency is binary.

The build rejects a player clip unless it has recurrent soft-alpha pixels, no alpha on the frame border, at least 98% of the visible mask in one connected silhouette, bounded foreground coverage, stable identity, the required clip-specific motion and a GIF preview mask matching the runtime sheet. Idle and walk must close their loops exactly; one-shot actions are not forced to loop.

## Current controls and gameplay

Use WASD or the arrow keys to move. Movement switches the player from idle to the reviewed seventeen-frame walk cycle and returns to idle when movement stops. Use E to interact, F to attack and Q to use an inventory item. The public browser verifier walks to the cookie plate, executes the model-authored pickup action, verifies the cookie enters inventory, executes the model-authored eat action, verifies the use animation and confirms that the cookie is consumed.

## Scene and transparency verification

The public scene review requires player, mother, dining table, chandelier, sideboard, curtains, wall surface, carpet, kitchen door and cookies to be visible and recognizable. It also rejects large white bars, rectangular source backgrounds, character halos, severe overlap and undersized objects. Focused public-player evidence verifies complete head, hands and feet; no white or dark halo; no uniform rectangular background or visible render-box boundary; and clean edges. The exact public runtime sheets are downloaded and audited frame by frame during verification.

Verification evidence is stored under `docs/verification/2026-07-30/`. Generation-only pose controls, contact sheets, tests and verification documents are excluded from the Web PCK; only runtime resources are packed.

## Build and verification

Run `tests/run_all.sh` for local contracts. Run `deploy/build-temporal-world.sh` on Nitro to validate the manifest, animation quality, action graph and Godot runtime, export the Web build and publish the reviewed public assets. Run `deploy/nitro-verify.sh` to compare local and public files and execute the Firefox/WebGL cold-start, walk, action, inventory, use and scene-evidence verification.

Godot Web export uses the official standard Godot 4.6.1 editor. The custom HTML loader pins PCK and WASM files to absolute `/llm_game/` routes and starts package download, WebAssembly initialization and scene startup sequentially.

