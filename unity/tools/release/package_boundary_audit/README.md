
### Safe upgrades and scan responsiveness — development follow-up

The second unpublished candidate increment adds path/GUID identity snapshots,
strict same-root comparison of old versus new versions, and fail-closed
reporting for removed assets, changed GUIDs, moved paths and added assets.
The built-in Unity Editor progress panel is cancelable; canceled or truncated
scans cannot be reported clean. Real prefab/asset rename, deliberate GUID
replacement and negative snapshot fixtures belong to the private native QA
rather than buyer archives. This is a static preflight only, **not** automatic
upgrade repair or certification of runtime/serialized-reference compatibility.

The actual normal GUI layout, keyboard interaction, responsive resizing and
marketing screenshots still need non-batch human-visible native Editor testing.
See `qa/UI_CONTRACT.md`; never use an invented editor capture or claim seller
approval based only on source or batchmode tests.
