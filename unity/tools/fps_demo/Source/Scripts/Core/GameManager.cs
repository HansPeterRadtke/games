using System.Collections.Generic;
using System.IO;
using System.Linq;
using UnityEngine;
using UnityEngine.SceneManagement;

public class GameManager : MonoBehaviour
{
    public static GameManager Instance { get; private set; }

    [SerializeField] private PlayerController player;
    [SerializeField] private Camera mapCamera;
    [SerializeField] private GameUiController uiController;

    private readonly List<ISaveableEntity> saveables = new List<ISaveableEntity>();
    private RenderTexture mapTexture;
    private string savePath;
    private bool titleMenuVisible = true;
    private bool pauseVisible;
    private bool inventoryVisible;
    private bool mapVisible;
    private bool optionsVisible;
    private bool playerDead;

    public GameOptionsData CurrentOptions { get; private set; }
    public PlayerController Player => player;
    public bool AllowsGameplayInput => IsGameplayRunning && !pauseVisible && !inventoryVisible && !mapVisible && !optionsVisible;
    public bool IsGameplayRunning => !titleMenuVisible && !playerDead;

    private void Awake()
    {
        if (Instance != null && Instance != this)
        {
            Destroy(gameObject);
            return;
        }

        Instance = this;
        savePath = Path.Combine(Application.persistentDataPath, "fps_demo_save.json");
        if (player == null)
        {
            player = FindFirstObjectByType<PlayerController>();
        }
        if (mapCamera == null)
        {
            mapCamera = FindFirstObjectByType<MapCameraFollow>()?.GetComponent<Camera>();
        }
        if (uiController == null)
        {
            uiController = GetComponent<GameUiController>();
        }

        CurrentOptions = GameOptionsStore.Load();
        player?.ApplyOptions(CurrentOptions);
        BuildMapTexture();
        RegisterSaveables();
    }

    private void Start()
    {
        uiController.Initialize(this, mapTexture);
        uiController.ShowTitleMenu(true);
        RefreshHud();
        UpdateCursorAndTime();
    }

    private void OnDestroy()
    {
        if (mapTexture != null)
        {
            mapTexture.Release();
        }
        if (Instance == this)
        {
            Instance = null;
        }
    }

    public void BeginSession()
    {
        titleMenuVisible = false;
        playerDead = false;
        pauseVisible = false;
        inventoryVisible = false;
        mapVisible = false;
        optionsVisible = false;
        uiController.ShowTitleMenu(false);
        uiController.ShowPauseMenu(false);
        uiController.ShowInventory(false, string.Empty);
        uiController.ShowMap(false);
        uiController.ShowOptions(false);
        RefreshHud();
        UpdateCursorAndTime();
    }

    public void TogglePauseMenu()
    {
        if (titleMenuVisible || playerDead)
        {
            return;
        }

        pauseVisible = !pauseVisible;
        inventoryVisible = false;
        mapVisible = false;
        optionsVisible = false;
        uiController.ShowPauseMenu(pauseVisible);
        uiController.ShowInventory(false, string.Empty);
        uiController.ShowMap(false);
        uiController.ShowOptions(false);
        UpdateCursorAndTime();
    }

    public void ToggleInventory()
    {
        if (titleMenuVisible || playerDead)
        {
            return;
        }

        inventoryVisible = !inventoryVisible;
        pauseVisible = false;
        mapVisible = false;
        optionsVisible = false;
        uiController.ShowInventory(inventoryVisible, player.Inventory.BuildInventorySummary(player.WeaponSystem));
        uiController.ShowPauseMenu(false);
        uiController.ShowMap(false);
        uiController.ShowOptions(false);
        UpdateCursorAndTime();
    }

    public void ToggleMap()
    {
        if (titleMenuVisible || playerDead)
        {
            return;
        }

        mapVisible = !mapVisible;
        pauseVisible = false;
        inventoryVisible = false;
        optionsVisible = false;
        uiController.ShowMap(mapVisible);
        uiController.ShowPauseMenu(false);
        uiController.ShowInventory(false, string.Empty);
        uiController.ShowOptions(false);
        UpdateCursorAndTime();
    }

    public void ShowOptionsMenu(bool visible)
    {
        optionsVisible = visible;
        uiController.ShowOptions(visible);
        if (visible)
        {
            pauseVisible = false;
            inventoryVisible = false;
            mapVisible = false;
            uiController.ShowPauseMenu(false);
            uiController.ShowInventory(false, string.Empty);
            uiController.ShowMap(false);
        }
        UpdateCursorAndTime();
    }

    public void SaveGame()
    {
        if (player == null)
        {
            return;
        }

        RegisterSaveables();
        var saveData = new SaveGameData { player = player.CaptureSaveData() };
        foreach (var saveable in saveables)
        {
            saveData.entities.Add(saveable.CaptureState());
        }

        File.WriteAllText(savePath, JsonUtility.ToJson(saveData, true));
        NotifyStatus($"Saved to {savePath}");
    }

    public void LoadGame()
    {
        if (!File.Exists(savePath))
        {
            NotifyStatus("No save file found");
            return;
        }

        RegisterSaveables();
        var saveData = JsonUtility.FromJson<SaveGameData>(File.ReadAllText(savePath));
        if (saveData == null)
        {
            NotifyStatus("Save file unreadable");
            return;
        }

        BeginSession();
        player.RestoreFromSave(saveData.player);
        var lookup = saveData.entities.ToDictionary(x => x.id, x => x);
        foreach (var saveable in saveables)
        {
            if (lookup.TryGetValue(saveable.SaveId, out var state))
            {
                saveable.RestoreState(state);
            }
        }
        RefreshHud();
        NotifyStatus("Save loaded");
    }

    public void StartNewGame()
    {
        Time.timeScale = 1f;
        SceneManager.LoadScene(SceneManager.GetActiveScene().buildIndex);
    }

    public void ActivatePrimaryMenuAction()
    {
        if (playerDead)
        {
            StartNewGame();
            return;
        }

        BeginSession();
    }

    public void ExitGame()
    {
#if UNITY_EDITOR
        UnityEditor.EditorApplication.isPlaying = false;
#else
        Application.Quit();
#endif
    }

    public void HandlePlayerDeath()
    {
        playerDead = true;
        pauseVisible = false;
        inventoryVisible = false;
        mapVisible = false;
        optionsVisible = false;
        titleMenuVisible = true;
        uiController.ShowPauseMenu(false);
        uiController.ShowInventory(false, string.Empty);
        uiController.ShowMap(false);
        uiController.ShowOptions(false);
        uiController.ShowTitleMenu(true, "Mission Failed");
        UpdateCursorAndTime();
    }

    public void NotifyStatus(string message)
    {
        uiController.SetStatusMessage(message);
        RefreshHud();
    }

    public void SetInteractionPrompt(string prompt)
    {
        uiController.SetInteractionPrompt(prompt);
    }

    public void RefreshHud()
    {
        if (player == null || uiController == null)
        {
            return;
        }

        uiController.SetHudValues(player.Stats.Health, player.Stats.MaxHealth, player.Stats.Stamina, player.Stats.MaxStamina,
            player.WeaponSystem.CurrentSlot.DisplayName, player.WeaponSystem.CurrentSlot.GetAmmoLabel(),
            $"Medkits {player.Inventory.Medkits}  Keys {(player.Inventory.HasRedKey ? "R" : "-")}/{(player.Inventory.HasBlueKey ? "B" : "-")}");

        if (inventoryVisible)
        {
            uiController.ShowInventory(true, player.Inventory.BuildInventorySummary(player.WeaponSystem));
        }
        uiController.RefreshOptions(CurrentOptions);
    }

    public void ApplyOptions(GameOptionsData updatedOptions)
    {
        CurrentOptions = updatedOptions;
        player?.ApplyOptions(CurrentOptions);
        GameOptionsStore.Save(CurrentOptions);
        RefreshHud();
    }

    public string DescribeNearbyThreats(Vector3 position)
    {
        var enemies = FindObjectsByType<EnemyAgent>(FindObjectsInactive.Exclude, FindObjectsSortMode.None)
            .Where(enemy => enemy.IsAlive)
            .OrderBy(enemy => Vector3.Distance(enemy.transform.position, position))
            .Take(3)
            .ToArray();

        if (enemies.Length == 0)
        {
            return "Scanner: no nearby hostiles";
        }

        return "Scanner: " + string.Join(", ", enemies.Select(enemy => $"{enemy.name} {Vector3.Distance(enemy.transform.position, position):0}m"));
    }

    public void RebindAction(GameAction action, KeyCode key)
    {
        GameOptionsStore.SetBinding(CurrentOptions, action, key);
        ApplyOptions(CurrentOptions);
        NotifyStatus($"Bound {action.ToDisplayName()} to {key}");
    }

    private void RegisterSaveables()
    {
        saveables.Clear();
        foreach (var behaviour in FindObjectsByType<MonoBehaviour>(FindObjectsInactive.Include, FindObjectsSortMode.None))
        {
            if (behaviour is ISaveableEntity saveable)
            {
                saveables.Add(saveable);
            }
        }
    }

    private void BuildMapTexture()
    {
        if (mapCamera == null)
        {
            return;
        }

        mapTexture = new RenderTexture(1024, 1024, 16, RenderTextureFormat.ARGB32)
        {
            name = "FPSDemo_MapTexture"
        };
        mapTexture.Create();
        mapCamera.targetTexture = mapTexture;
        if (mapCamera.TryGetComponent<MapCameraFollow>(out var follow))
        {
            follow.SetTarget(player.transform);
        }
    }

    private void UpdateCursorAndTime()
    {
        bool blockGameplay = titleMenuVisible || pauseVisible || inventoryVisible || mapVisible || optionsVisible || playerDead;
        Time.timeScale = blockGameplay ? 0f : 1f;
        Cursor.lockState = blockGameplay ? CursorLockMode.None : CursorLockMode.Locked;
        Cursor.visible = blockGameplay;
    }

    public void AssignReferences(PlayerController playerController, Camera overheadMapCamera, GameUiController ui)
    {
        player = playerController;
        mapCamera = overheadMapCamera;
        uiController = ui;
    }
}
