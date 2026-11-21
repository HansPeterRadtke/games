using UnityEngine;

// Private customer-owned runtime test script, never included in any vendor
// release archive. A normal Assembly-CSharp script must retain its GUID and
// serialized .asset reference across an Editor restart and vendor upgrade.
public sealed class HprRealUpgradeBuyerReference : ScriptableObject
{
    public UnityEngine.Object vendorReadme;
}
