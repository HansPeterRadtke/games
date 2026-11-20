# HPR Animator Contract Audit — separate original Unity tool candidate

A read-only Unity Editor scanner for stale or type-incompatible Animator Controller parameter references, motivated by actual animator refactor issues. All vendor source lies in `Assets/HPRAnimatorContract/`; `qa/` is private and must never be packaged. The exporter includes only the vendor folder and Unity GUID metadata. The tool makes no modifications or automatic repairs.

Native QA is `qa/HprAnimatorContractNativeQa.cs` in a new disposable Unity project; it creates test controllers in that disposable project, confirms missing condition/type mismatch/stale speed and a clean controller, runs the whole-project scanner, and verifies the scan does not alter source bytes. Run patched Unity Editor `-executeMethod HprAnimatorContractNativeQa.Run` with a fresh `HPR_ANIM_QA_OUT` path. Export via `-executeMethod HprAnimatorContractExport.Run` and a fresh `HPR_ANIM_PACKAGE_OUT` path. Then import the exported `.unitypackage` in a separate new Unity project and repeat native QA; keep all raw logs outside Git.

Manual graphical Editor workflow and screenshots are blocked by Unity Editor Software Terms unless the owner authorizes acceptance. A successful headless test does not certify buyer usability, graphical polish or commercial viability. No license or store submission has been approved.
