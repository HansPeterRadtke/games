// Private QA runtime script, staged only in a disposable Linux Player build.
#if UNITY_STANDALONE_LINUX && !UNITY_EDITOR
using System;
using System.IO;
using HPR.GameplaySuite;
using UnityEngine;
using UnityEngine.SceneManagement;

public sealed class SaveSlotPlayerProbe : MonoBehaviour
{
    [Serializable]
    private class Observation
    {
        public string phase;
        public string version;
        public string scene;
        public string slot;
        public float initialHealth;
        public int initialAmmo;
        public float finalHealth;
        public int finalAmmo;
    }

    [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.AfterSceneLoad)]
    private static void StartProbe()
    {
        new GameObject(nameof(SaveSlotPlayerProbe)).AddComponent<SaveSlotPlayerProbe>();
    }

    private void Start()
    {
        try
        {
            Run();
            Application.Quit(0);
        }
        catch (Exception error)
        {
            Debug.LogException(error);
            Application.Quit(1);
        }
    }

    private static void Run()
    {
        var game = UnityEngine.Object.FindAnyObjectByType<HprGameplaySuitePlayground>();
        Require(game && game.enabled && game.ServicesAvailable, "Packaged showcase did not initialize");
        var observation = new Observation
        {
            phase = Environment.GetEnvironmentVariable("HPR_SAVE_PLAYER_PHASE"),
            version = Application.unityVersion,
            scene = SceneManager.GetActiveScene().path,
            slot = Path.GetFullPath(game.SavePath),
            initialHealth = game.PlayerHealth,
            initialAmmo = game.MagazineAmmo
        };
        string privateRoot = Environment.GetEnvironmentVariable("XDG_CONFIG_HOME");
        Require(!string.IsNullOrWhiteSpace(privateRoot) && Path.IsPathRooted(privateRoot) &&
            observation.slot.StartsWith(Path.GetFullPath(privateRoot) + "/", StringComparison.Ordinal),
            "The default slot is outside the private Player profile");
        Require(observation.scene == "Assets/HPRGameplaySuite/Demo/GameplaySuiteShowcase.unity" &&
            !game.HasCheckpoint, "Expected a fresh showcase encounter");

        string neighbor = observation.slot + ".writing";
        if (observation.phase == "write")
        {
            Require(!File.Exists(observation.slot), "The writer needs an empty profile");
            Directory.CreateDirectory(Path.GetDirectoryName(observation.slot));
            using (var marker = new StreamWriter(new FileStream(neighbor, FileMode.CreateNew)))
                marker.Write("private neighboring file");

            game.SetAutomaticEnemy(false);
            Require(game.EnemyAttack() && game.Fire(), "Expected an enemy attack and a fired round");
            Require(game.SaveToDisk(), "The normal save action failed");
        }
        else if (observation.phase == "read")
        {
            Require(game.LoadFromDisk() && game.HasCheckpoint, "The normal load action failed");
        }
        else if (observation.phase == "reject")
        {
            Require(!game.LoadFromDisk() && !game.HasCheckpoint, "Malformed slot was accepted");
        }
        else
        {
            throw new InvalidOperationException("Unknown Player test phase");
        }

        Require(File.ReadAllText(neighbor) == "private neighboring file", "Neighbor changed");
        observation.finalHealth = game.PlayerHealth;
        observation.finalAmmo = game.MagazineAmmo;
        if (observation.phase == "reject")
            Require(observation.finalHealth == observation.initialHealth && observation.finalAmmo == observation.initialAmmo,
                "Malformed slot changed live state");
        else
            Require(observation.finalHealth > 0f && observation.finalHealth < observation.initialHealth &&
                observation.finalAmmo == observation.initialAmmo - 1, "Expected damaged health and one spent round");
        Debug.Log("HPR_SAVE_PLAYER_OBSERVATION " + JsonUtility.ToJson(observation));
    }

    private static void Require(bool condition, string message)
    {
        if (!condition) throw new InvalidOperationException(message);
    }
}
#endif
