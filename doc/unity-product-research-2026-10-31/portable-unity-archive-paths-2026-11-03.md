# Cross-platform Unity .unitypackage asset-path safety

November 3, 2026. Source-level private QA; not a real Windows/macOS Unity Editor import or a commercial GO.

The previous static archive policy checked tar-member paths, HPR root, Unity metadata GUIDs, assembly definitions and exported source exclusions. However, it accepted paths that can import inconsistently across supported developer operating systems:

- Two assets differing only by filename case, which can collide on typical Windows/macOS case-insensitive filesystems.
- Two assets with Unicode-composed and decomposed versions of the same visible name, which can collide after filesystem normalization.
- Windows-reserved device basenames, including CON, NUL, AUX and COM1, even when an extension is appended.
- Windows-incompatible trailing spaces or dots in filename/folder segments. The previous pathname parser also stripped trailing spaces before checking them.

Four new tests reproduced these false passes against synthetic Unity tar-format packages. The read-only validator now rejects these names, checks casefold and Unicode normalization collisions, and strips only optional export line endings rather than arbitrary whitespace. It preserves actual Unity-supplied asset bytes, folder names and GUID metadata without extracting or changing any archive.

Both real private HPR binaries were rechecked against the stricter validator: the original frozen one-hundred-sixty-one-asset selected-installer archive and the new reviewed copy-race candidate both pass, each with ten valid assembly definitions, no imported test runners and no case/normalization portability conflicts. The actual new package maximum pathname size remains ninety bytes. Separate create-only JSON receipts with the real SHA-256 archive identities are stored under the owner-protected marketplace-account-setup QA evidence directory.

This is a static portability gate. Only real Unity Editor imports on the relevant platforms, with the verified exact candidate and protected customer project, can establish actual build/import success. Windows and macOS Editor tests have not been performed, and the Nitro URP/new-only-input test remains pending under resource-broker CPU admission.

Commercial decision remains NO-GO. No public submission, purchase, file deletion or owner project mutation occurred.
