// Private compatibility smoke, not a physical keyboard or transition test.
using System;
using System.Collections;
using System.IO;
using UnityEngine;
using HPR.GameplaySuite;

public sealed class LegacyInputPlayerProbe : MonoBehaviour
{
    private IEnumerator Start()
    {
        for (int i = 0; i < 10; ++i) yield return null;
        int exitCode = 1;
        try
        {
#if ENABLE_LEGACY_INPUT_MANAGER && !ENABLE_INPUT_SYSTEM
            string receipt = Environment.GetEnvironmentVariable("HPR_LEGACY_PLAYER_RECEIPT");
            if (string.IsNullOrEmpty(receipt) || !Path.IsPathRooted(receipt) ||
                !receipt.StartsWith("/data/var/marketplace-account-setup/", StringComparison.Ordinal) || File.Exists(receipt))
                throw new InvalidOperationException("Fresh private legacy receipt required");
            var input = HprSuiteUnityInputSource.Instance;
            if (input.IsPressed(KeyCode.None) || input.WasPressed(KeyCode.None))
                throw new InvalidOperationException("An unbound key activated the legacy input source");
            File.WriteAllText(receipt, "unity=" + Application.unityVersion + "\n" +
                "legacy_only_player_started=PASS\n" +
                "unbound_key_held_is_false=PASS\n" +
                "unbound_key_edge_is_false=PASS\n");
            Debug.Log("HPR_LEGACY_PLAYER_SMOKE_PASS");
            exitCode = 0;
#else
            throw new InvalidOperationException("Legacy-only compile path required");
#endif
        }
        catch (Exception error) { Debug.LogException(error); }
        Application.Quit(exitCode);
    }
}
