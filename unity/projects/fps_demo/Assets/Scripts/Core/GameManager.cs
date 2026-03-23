using System.Collections.Generic;
using System.IO;
using System.Linq;
using UnityEngine;
using UnityEngine.SceneManagement;
using System.Collections;

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
    private bool autoStartRequested;
    private bool smokeTestRequested;
    private bool autoOpenMapRequested;
    private bool autoOpenInventoryRequested;
    private bool combatDisabledRequested;
    private bool waitingForCleanMenuInput;
    private bool waitingForMenuPointerMotion;
    private Vector2 titleMenuPointerOrigin;
    private float titleMenuShownRealtime;
    private float sessionStartTime;
    private bool combatHold;

    public GameOptionsData CurrentOptions { get; private set; }
    public PlayerController Player => player;
    public bool AllowsGameplayInput => IsGameplayRunning && !pauseVisible && !inventoryVisible && !mapVisible && !optionsVisible;
    public bool IsGameplayRunning => !titleMenuVisible && !playerDead;
    public bool IsMapVisible => mapVisible;
    public bool IsInventoryVisible => inventoryVisible;
    public bool IsPauseVisible => pauseVisible;
    public bool IsCombatLive => IsGameplayRunning && !combatDisabledRequested && !combatHold && Time.time >= sessionStartTime + 0.5f;

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
            player = FindAnyObjectByType<PlayerController>();
        }
        if (mapCamera == null)
        {
            mapCamera = FindAnyObjectByType<MapCameraFollow>()?.GetComponent<Camera>();
        }
        if (uiController == null)
        {
            uiController = GetComponent<GameUiController>();
        }

        CurrentOptions = GameOptionsStore.Load();
        string commandLine = string.Join(" ", System.Environment.GetCommandLineArgs());
        autoStartRequested = commandLine.Contains("-autostart");
        smokeTestRequested = commandLine.Contains("-smoketest");
        autoOpenMapRequested = commandLine.Contains("-openmap");
        autoOpenInventoryRequested = commandLine.Contains("-openinventory");
        combatDisabledRequested = commandLine.Contains("-combatdisabled");
        player?.ApplyOptions(CurrentOptions);
        BuildMapTexture();
        RegisterSaveables();
    }

    private void Start()
    {
        uiController.Initialize(this, mapTexture);
        if (autoStartRequested || smokeTestRequested)
        {
            BeginSession();
            if (autoOpenMapRequested)
            {
                ToggleMap();
            }
            else if (autoOpenInventoryRequested)
            {
                ToggleInventory();
            }
        }
        else
        {
            ShowInitialTitleMenu();
            StartCoroutine(EnforceInitialTitleMenu());
        }

        if (smokeTestRequested)
        {
            StartCoroutine(RunSmokeTest());
            StartCoroutine(ForceQuitSmokeTestAfterDelay());
        }
    }

    private void Update()
    {
        if (titleMenuVisible)
        {
            if (waitingForCleanMenuInput)
            {
                if (Input.GetKey(KeyCode.Return) || Input.GetKey(KeyCode.KeypadEnter) || Input.GetMouseButton(0) || Input.GetMouseButton(1) || Input.GetMouseButton(2))
                {
                    return;
                }

                waitingForCleanMenuInput = false;
            }

            if (waitingForMenuPointerMotion)
            {
                if (Time.realtimeSinceStartup - titleMenuShownRealtime < 1.5f)
                {
                    return;
                }

                if (((Vector2)Input.mousePosition - titleMenuPointerOrigin).sqrMagnitude < 6400f)
                {
                    return;
                }

                waitingForMenuPointerMotion = false;
            }

            if (!waitingForCleanMenuInput && !waitingForMenuPointerMotion)
            {
                uiController.SetMenuInteractable(true);
            }

            if (optionsVisible)
            {
                return;
            }

            if (!waitingForCleanMenuInput && (Input.GetKeyDown(KeyCode.Return) || Input.GetKeyDown(KeyCode.KeypadEnter)))
            {
                ActivatePrimaryMenuAction();
            }
        }

        if (combatHold && IsGameplayRunning && Time.time >= sessionStartTime + 12f)
        {
            combatHold = false;
            NotifyStatus("Combat live");
        }
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

    private void OnApplicationQuit()
    {
    }

    public void BeginSession()
    {
        waitingForCleanMenuInput = false;
        waitingForMenuPointerMotion = false;
        titleMenuVisible = false;
        playerDead = false;
        pauseVisible = false;
        inventoryVisible = false;
        mapVisible = false;
        optionsVisible = false;
        sessionStartTime = Time.time;
        combatHold = true;
        uiController.ShowTitleMenu(false);
        uiController.ShowPauseMenu(false);
        uiController.ShowInventory(false, null);
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
        uiController.ShowInventory(false, null);
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
        uiController.ShowInventory(inventoryVisible, player.Inventory.BuildInventoryTabs(player.WeaponSystem));
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
        if (mapVisible)
        {
            mapCamera.GetComponent<MapCameraFollow>()?.ResetView();
        }
        uiController.ShowMap(mapVisible);
        uiController.ShowPauseMenu(false);
        uiController.ShowInventory(false, null);
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
            uiController.ShowInventory(false, null);
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
        if (titleMenuVisible && waitingForCleanMenuInput)
        {
            return;
        }

        if (playerDead)
        {
            StartNewGame();
            return;
        }

        BeginSession();
    }

    public void MarkCombatReady()
    {
        if (!combatHold)
        {
            return;
        }

        combatHold = false;
        NotifyStatus("Combat live");
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
        uiController.ShowInventory(false, null);
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
            uiController.ShowInventory(true, player.Inventory.BuildInventoryTabs(player.WeaponSystem));
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
        var enemies = FindObjectsByType<EnemyAgent>(FindObjectsInactive.Exclude)
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
        foreach (var behaviour in FindObjectsByType<MonoBehaviour>(FindObjectsInactive.Include))
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

    private void ShowInitialTitleMenu()
    {
        titleMenuVisible = true;
        pauseVisible = false;
        inventoryVisible = false;
        mapVisible = false;
        optionsVisible = false;
        playerDead = false;
        waitingForCleanMenuInput = true;
        waitingForMenuPointerMotion = true;
        titleMenuPointerOrigin = Input.mousePosition;
        titleMenuShownRealtime = Time.realtimeSinceStartup;
        uiController.ShowPauseMenu(false);
        uiController.ShowInventory(false, null);
        uiController.ShowMap(false);
        uiController.ShowOptions(false);
        uiController.ShowTitleMenu(true);
        uiController.SetMenuInteractable(false);
        RefreshHud();
        UpdateCursorAndTime();
    }

    private IEnumerator EnforceInitialTitleMenu()
    {
        yield return new WaitForSecondsRealtime(0.2f);
        if (autoStartRequested || smokeTestRequested)
        {
            yield break;
        }

        ShowInitialTitleMenu();
    }

    private IEnumerator RunSmokeTest()
    {
        yield return null;
        yield return null;

        NotifyStatus("Smoke test: session started");
        player.WeaponSystem.SelectSlot(1);
        player.WeaponSystem.TriggerCurrent(player);
        yield return new WaitForSecondsRealtime(0.2f);

        player.WeaponSystem.SelectSlot(2);
        player.WeaponSystem.TriggerCurrent(player);
        yield return new WaitForSecondsRealtime(0.2f);

        player.WeaponSystem.SelectSlot(3);
        player.WeaponSystem.TriggerCurrent(player);
        yield return new WaitForSecondsRealtime(0.2f);

        ToggleInventory();
        yield return new WaitForSecondsRealtime(0.2f);
        uiController.SelectInventoryTab(InventoryTab.Keys);
        yield return new WaitForSecondsRealtime(0.1f);
        ToggleInventory();

        ToggleMap();
        yield return new WaitForSecondsRealtime(0.2f);
        mapCamera.GetComponent<MapCameraFollow>()?.Pan(new Vector2(8f, -6f));
        mapCamera.GetComponent<MapCameraFollow>()?.Zoom(1f);
        yield return new WaitForSecondsRealtime(0.1f);
        ToggleMap();

        TogglePauseMenu();
        yield return new WaitForSecondsRealtime(0.2f);
        TogglePauseMenu();

        FindObjectsByType<PickupItem>(FindObjectsInactive.Include)
            .FirstOrDefault(pickup => pickup.gameObject.activeInHierarchy)?
            .Interact(player);
        yield return new WaitForSecondsRealtime(0.1f);

        FindObjectsByType<DoorController>(FindObjectsInactive.Include)
            .FirstOrDefault()?
            .Interact(player);
        yield return new WaitForSecondsRealtime(0.1f);

        SaveGame();
        yield return new WaitForSecondsRealtime(0.1f);
        LoadGame();
        yield return new WaitForSecondsRealtime(0.2f);

        NotifyStatus("Smoke test completed");
        yield return new WaitForSecondsRealtime(0.3f);
        ExitGame();
    }

    private IEnumerator ForceQuitSmokeTestAfterDelay()
    {
        yield return new WaitForSecondsRealtime(8f);
        if (!smokeTestRequested)
        {
            yield break;
        }

        NotifyStatus("Smoke test timeout exit");
        ExitGame();
    }
}
