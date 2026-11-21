using UnityEngine;
// PRIVATE test-only runtime ScriptableObject; never shipped in a buyer package.
// Runtime assembly is essential: the Editor-only fixture failed on reload in an
// earlier independent buyer QA, so preserve m_Script serialization truthfully.
public sealed class HprCaseOnlyReferenceHolder : ScriptableObject
{
    public TextAsset referenced;
}
