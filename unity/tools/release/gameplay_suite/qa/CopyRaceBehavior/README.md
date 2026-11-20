# Deterministic source-exact copied-asset failure simulator

This is a private standalone .NET 8 unit simulation, NOT the Unity Editor. It uses an exact extracted CopySampleToCustomerPath method body from the HPR seller source and minimal fake UnityEngine/UnityEditor objects. It creates only disposable private test files under its own specified scratch folder. It is intended to verify that failed CopyAsset operations can leave a destination, that successful copies are preserved on subsequent failure, that a destination occupied between preflight and copy is noticed before the second CopyAsset call, and that no automatic deletion occurs.

The harness is intentionally separate from the source under test; it must never be shipped in the .unitypackage. A genuine Unity 6.6 Editor validation, including concurrent importers and VCS hooks, remains mandatory.
