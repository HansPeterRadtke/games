using UnityEngine;

public static class GameOptionsStore
{
    private const string PlayerPrefsKey = "fps_demo_options";

    public static GameOptionsData Load()
    {
        if (!PlayerPrefs.HasKey(PlayerPrefsKey))
        {
            return GameOptionsData.CreateDefault();
        }

        var json = PlayerPrefs.GetString(PlayerPrefsKey, string.Empty);
        if (string.IsNullOrWhiteSpace(json))
        {
            return GameOptionsData.CreateDefault();
        }

        var data = JsonUtility.FromJson<GameOptionsData>(json);
        return data ?? GameOptionsData.CreateDefault();
    }

    public static void Save(GameOptionsData data)
    {
        PlayerPrefs.SetString(PlayerPrefsKey, JsonUtility.ToJson(data));
        PlayerPrefs.Save();
    }

    public static KeyCode GetBinding(GameOptionsData options, GameAction action)
    {
        options ??= GameOptionsData.CreateDefault();
        return action switch
        {
            GameAction.MoveForward => options.moveForward,
            GameAction.MoveBackward => options.moveBackward,
            GameAction.MoveLeft => options.moveLeft,
            GameAction.MoveRight => options.moveRight,
            GameAction.Jump => options.jump,
            GameAction.Run => options.run,
            GameAction.Interact => options.interact,
            GameAction.Inventory => options.inventory,
            GameAction.Map => options.map,
            GameAction.Pause => options.pause,
            GameAction.Flashlight => options.flashlight,
            GameAction.Reload => options.reload,
            _ => KeyCode.None
        };
    }

    public static void SetBinding(GameOptionsData options, GameAction action, KeyCode key)
    {
        if (options == null)
        {
            return;
        }

        switch (action)
        {
            case GameAction.MoveForward: options.moveForward = key; break;
            case GameAction.MoveBackward: options.moveBackward = key; break;
            case GameAction.MoveLeft: options.moveLeft = key; break;
            case GameAction.MoveRight: options.moveRight = key; break;
            case GameAction.Jump: options.jump = key; break;
            case GameAction.Run: options.run = key; break;
            case GameAction.Interact: options.interact = key; break;
            case GameAction.Inventory: options.inventory = key; break;
            case GameAction.Map: options.map = key; break;
            case GameAction.Pause: options.pause = key; break;
            case GameAction.Flashlight: options.flashlight = key; break;
            case GameAction.Reload: options.reload = key; break;
        }
    }

    public static void Apply(GameOptionsData options, Camera playerCamera)
    {
        options ??= GameOptionsData.CreateDefault();
        if (!Application.isPlaying)
        {
            return;
        }

        if (playerCamera != null)
        {
            playerCamera.fieldOfView = options.fieldOfView;
        }

        AudioListener.volume = Mathf.Clamp01(options.masterVolume);
        QualitySettings.SetQualityLevel(Mathf.Clamp(options.qualityLevel, 0, QualitySettings.names.Length - 1), true);
    }
}
