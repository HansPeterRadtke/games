# HPR Combined FBX Animation Import Audit — original Unity Editor candidate

## Documentation and first-use workflow

Open **Tools > HPR > Combined Animation Import Audit** to run both read-only
checks on your project's imported `.fbx` files. It combines the original HPR
FBX Clip Identity and FBX Source Take Visibility tools, included with this
first-party bundle under their own original stable Unity asset GUIDs.
First click **Try included original healthy and warning examples**. It runs
three non-mutating checks on first-party training FBXs and demonstrates a
healthy local-ID scan, a default source-take import, and a genuinely saved
Unity import with one unreferenced original Blender action. This action does
not count the examples as customer files. Then click **Scan all customer FBX
models**, review separate ID and source-take
statuses, and optionally export a new JSON report. The exporter refuses to
overwrite existing reports. A fresh project containing only the bundled
original Blender examples correctly reports **NO_CUSTOMER_FBX_MODELS_SCANNED**;
those vendor FBXs are not customer assets and do not count as a clean scan.

ID collisions require investigation in a disposable project. Missing source
takes may already have a native **Import Unreferenced Takes** button in newer
Unity versions or can be added manually in the Model Importer Animation tab.
This product never modifies importers, tries to repair clip IDs, changes
source FBXs, accesses the network or guesses a supposedly safe replacement.

Limitations: a clean targeted result does NOT prove animation playback, lack
of missing scripts, GUID fileID stability, future Unity versions, or
compatibility of all sampled import settings. No real project source is
altered by either built-in scanner. Scan size is capped and the user can
cancel; incomplete scans must not be treated as successful. The tool is
Editor-only; no optional package or render pipeline is required for the
scanner itself. Original samples are simple educational cubes, not
photorealistic game art. The optional genuine demonstration scene is not a
screenshot of the combined window.

The combined report is a convenience layer over two independent first-party
scanners. They must remain part of the installed package, not replaced by
unverified third-party lookalikes or silently added as optional dependencies.
The original sample FBXs retain their stable Unity GUIDs; the package exports
the three whole roots together to avoid missing assemblies.

This is a private producer candidate. Software-terms GUI consent and actual
human-visible window review, licensing rights, truthful screenshots,
pricing, willingness to pay and any Asset Store publication are not yet
approved. It must not be sold or described as a fully tested retail product
without independent real author/buyer native Unity QA and the seller's
separate authorization.
