# HPR Define Matrix — Unity Build Profile script defines

**Status:** Original privately tested commercial candidate. **NOT PUBLISHED, NOT APPROVED FOR RESALE.** This Editor-only tool reports differences in explicitly configured scripting symbols across saved Unity Build Profiles. It does not compile or build a Player, change the active profile, add packages, access the network, track users or alter any Unity project setting. It contains no runtime components.

## One-minute workflow

In a Unity 6.1 or newer project that already has Build Profiles, import this archive and open **Tools > HPR > Define Matrix**. Click **Rescan saved Build Profiles**, then select a reference profile and another profile. The table shows which additional symbols are shared, present only in the reference or present only in the other profile. Use **Show differences only** and **Filter symbol** to inspect the relevant code paths. Use **Export a NEW CSV comparison** to create a review file; existing files are never replaced. The CSV includes project paths, so review it before sharing with anyone. When a profile changes, click Rescan again.

For an independent sample, create two Build Profiles in Unity via **File > Build Profiles**. In the Scripting Defines section, add `RELEASE_BUILD` in one and `DEMO_BUILD` in the other; add `FEATURE_SHARED` in both. The tool should report one shared symbol and one unique symbol per profile. The sample is *instructional*, not an automatic modification or fixture included in the buyer archive.

## Compare with an earlier approved release

After reviewing a current saved Build Profile, choose **Save live define reference**
and select a *new* `.hpr-defines` file outside the entire Unity project directory. Store this approved snapshot alongside your release evidence. When
preparing a later revision, open the same window and choose **Load saved
define reference**. It compares the earlier declared symbols with a current
profile without changing any Build Profile, project setting, active target, or
existing reference file. The display and CSV show the saved time and warn if
the historical asset identifier differs from the selected current profile.
Use **Return to live profile comparison** to compare two current profiles.

A saved define reference does *not* prove that the original release was
published or that its compiled Player used exactly those symbols. It does not
include Player Settings, command-line overrides or external response-file
defines. Only explicit declarations from one saved Build Profile are
preserved. The tool cannot establish which Unity project an untrusted
reference belongs to; review its provenance yourself. Snapshots are bounded,
validated on load and never overwrite an existing file.

## Exact scope and limitations

This is a **configuration comparison**, not a project validator or proof that a final Player contains a particular feature. It reads `BuildProfile.scriptingDefines` using documented Unity APIs. Those symbols are *additive* to the Player Settings and global compiler response files, but this tool deliberately does **not** report effective or compiled symbols from those other scopes. Build command-line extra defines and active build state also affect compilation and are not analyzed. A difference may be intentional, for example free demo versus paid release. The tool does not label either choice as wrong.

Only saved, AssetDatabase-addressable `BuildProfile` assets under `Assets` plus any asset-backed active profile are scanned. An active unsaved profile is marked unreadable. Invalid or repeated symbols are reported as warnings, without editing them; scanner failure is displayed explicitly. Supports at most 256 profiles and 4096 declared symbols per profile. Unity 2022 and 6.0 are not supported by this build. Unity 6.1 API availability does **not** mean that the product has been independently tested in every such version. Source-only and Unity-native tests are recorded separately in the producer's private evidence. This package's rendering pipeline has no effect on its Editor-only code; that does not certify every Editor/platform combination.

The supplied demonstration is a textual first-use walkthrough. There are no included art assets, dependencies, generated scenes or Build Profile presets, so importing it cannot change your build configuration. Future upgrades should preserve the included stable Unity `.meta` GUID identifiers.

## AI disclosure and licence

AI-assisted coding and documentation were used to develop this original first-party tool. Human review and Unity-native isolated tests are required before marketing or release. Any later Asset Store listing must accurately declare the tool's origin, AI assistance, tested platforms and actual limitations. See LICENSE.md for the **private prerelease-only** status and ThirdPartyNotices.md for the no-external-dependency declaration. The publisher and the sole shared seller must approve the correct commercial licence, official compatibility version and current Unity Asset Store requirements before submission.
