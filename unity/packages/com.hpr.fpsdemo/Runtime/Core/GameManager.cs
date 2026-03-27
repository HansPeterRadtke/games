using System.Collections.Generic;
using System.IO;
using System.Linq;
using UnityEngine;
using UnityEngine.SceneManagement;
using System.Collections;

public class GameManager : MonoBehaviour, IInputBindingsSource, IOptionsController, IEventBusSource, IGameplayStateSource, IStatusMessageSink, IInteractionPromptSink, IHudRefreshSink, IThreatScanner, IGameplayFlowCommands, IGameMenuCommands, IPlayerDeathHandler, IPlayerActorSource, IEnemyRegistry, ISkillTreeCommands, IQuestJournalSource, IDialogueFlowCommands, ISkillPointRewardSink, IQuestStateQuery, IInventoryItemUseCommands
{
    [SerializeField] private PlayerActorContext player;
    [SerializeField] private Camera mapCamera;
    [SerializeField] private GameUiController uiController;
    [SerializeField] private Transform saveableRoot;
    [SerializeField] private EventManager eventManager;
    [SerializeField] private GameStateValidator stateValidator;
    [SerializeField] private QuestManager questManager;
    [SerializeField] private List<ConsumableEffectData> consumableEffects = new List<ConsumableEffectData>();

    private readonly List<ISaveableEntity> saveables = new List<ISaveableEntity>();
    private readonly List<EnemyAgent> registeredEnemies = new List<EnemyAgent>();
    private readonly List<PickupItem> registeredPickups = new List<PickupItem>();
    private readonly List<DoorController> registeredDoors = new List<DoorController>();
    private readonly Dictionary<string, ConsumableEffectData> consumableLookup = new Dictionary<string, ConsumableEffectData>(System.StringComparer.Ordinal);
    private RenderTexture mapTexture;
    private string savePath;
    private bool titleMenuVisible = true;
    private bool pauseVisible;
    private bool inventoryVisible;
    private bool journalVisible;
    private bool skillsVisible;
    private bool mapVisible;
    private bool dialogueVisible;
    private bool optionsVisible;
    private bool playerDead;
    private bool autoStartRequested;
    private bool smokeTestRequested;
    private bool autoOpenMapRequested;
    private bool autoOpenInventoryRequested;
    private bool autoOpenOptionsRequested;
    private bool combatDisabledRequested;
    private bool optionsReturnToTitleMenu;
    private bool optionsReturnToPauseMenu;
    private bool waitingForCleanMenuInput;
    private bool waitingForMenuPointerMotion;
    private float titleMenuShownRealtime;
    private float sessionStartTime;
    private bool combatHold;
    private ActiveDialogueState activeDialogue;

    public GameOptionsData CurrentOptions { get; private set; }
    public IPlayerActor Player => player;
    public IGameEventBus EventBus => eventManager;
    public bool AllowsGameplayInput => IsGameplayRunning && !pauseVisible && !inventoryVisible && !journalVisible && !skillsVisible && !mapVisible && !dialogueVisible && !optionsVisible;
    public bool IsGameplayRunning => !titleMenuVisible && !playerDead;
    public bool IsMapVisible => mapVisible;
    public bool IsInventoryVisible => inventoryVisible;
    public bool IsJournalVisible => journalVisible;
    public bool IsSkillsVisible => skillsVisible;
    public bool IsDialogueVisible => dialogueVisible;
    public bool IsPauseVisible => pauseVisible;
    public bool IsOptionsVisible => optionsVisible;
    public bool IsCombatLive => IsGameplayRunning && !combatDisabledRequested && !combatHold && Time.time >= sessionStartTime + 0.5f;
    public bool HasSaveGame => !string.IsNullOrWhiteSpace(savePath) && File.Exists(savePath);
    public bool IsRebindingKey => uiController != null && uiController.IsRebindingKey;
    public bool IsQuestActive(string questId) => questManager != null && questManager.IsQuestActive(questId);
    public bool IsQuestCompleted(string questId) => questManager != null && questManager.IsQuestCompleted(questId);
    public bool IsObjectiveComplete(string questId, string objectiveId) => questManager != null && questManager.IsObjectiveComplete(questId, objectiveId);

    private sealed class ActiveDialogueState
    {
        public string NpcId;
        public string SpeakerName;
        public DialogueData DialogueData;
        public string CurrentNodeId;
    }

    private void Awake()
    {
        EnsureRuntimeBootstrapped();
        RebuildConsumableLookup();
        player?.MovementController.ApplyOptions(CurrentOptions);
        BuildMapTexture();
        RegisterSaveables();
    }

    private void EnsureRuntimeBootstrapped()
    {
        if (string.IsNullOrWhiteSpace(savePath))
        {
            savePath = Path.Combine(Application.persistentDataPath, "fps_demo_save.json");
        }

        CurrentOptions ??= GameOptionsStore.Load();
        eventManager = eventManager != null ? eventManager : GetComponent<EventManager>();
        if (eventManager == null)
        {
            eventManager = gameObject.AddComponent<EventManager>();
        }

        stateValidator = stateValidator != null ? stateValidator : GetComponent<GameStateValidator>();
        if (stateValidator == null)
        {
            stateValidator = gameObject.AddComponent<GameStateValidator>();
        }

        questManager = questManager != null ? questManager : GetComponent<QuestManager>();
        if (questManager == null)
        {
            questManager = gameObject.AddComponent<QuestManager>();
        }

        string commandLine = string.Join(" ", System.Environment.GetCommandLineArgs());
        autoStartRequested = commandLine.Contains("-autostart");
        smokeTestRequested = commandLine.Contains("-smoketest");
        autoOpenMapRequested = commandLine.Contains("-openmap");
        autoOpenInventoryRequested = commandLine.Contains("-openinventory");
        autoOpenOptionsRequested = commandLine.Contains("-openoptions");
        combatDisabledRequested = commandLine.Contains("-combatdisabled");
    }

    private void Start()
    {
        stateValidator?.Bind(EventBus);
        uiController.Initialize(this, mapTexture);
        BindRuntimeServicesToWorld();
        EventBus?.Subscribe<StatusMessageEvent>(HandleStatusMessageEvent);
        EventBus?.Subscribe<HudInvalidatedEvent>(HandleHudInvalidatedEvent);
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
            else if (autoOpenOptionsRequested)
            {
                ShowOptionsMenu(true);
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
                if (Time.realtimeSinceStartup - titleMenuShownRealtime < 0.35f)
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
        EventBus?.Unsubscribe<StatusMessageEvent>(HandleStatusMessageEvent);
        EventBus?.Unsubscribe<HudInvalidatedEvent>(HandleHudInvalidatedEvent);
        if (mapTexture != null)
        {
            mapTexture.Release();
        }
    }

    private void OnApplicationQuit()
    {
    }

    public void BeginSession()
    {
        ClearMenuInputGuards();
        titleMenuVisible = false;
        playerDead = false;
        sessionStartTime = Time.time;
        combatHold = true;
        activeDialogue = null;
        questManager?.ResetQuestState();
        HideAllMenus();
        RefreshHud();
        UpdateCursorAndTime();
    }

    public void ResumeSession()
    {
        if (titleMenuVisible || playerDead)
        {
            return;
        }

        ClearMenuInputGuards();
        activeDialogue = null;
        HideAllMenus();
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
        journalVisible = false;
        skillsVisible = false;
        mapVisible = false;
        dialogueVisible = false;
        optionsVisible = false;
        uiController.ShowPauseMenu(pauseVisible);
        uiController.ShowInventory(false, null);
        uiController.ShowJournal(false, null);
        uiController.ShowSkills(false, null, 0);
        uiController.ShowMap(false);
        uiController.ShowDialogue(false, null);
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
        journalVisible = false;
        skillsVisible = false;
        mapVisible = false;
        dialogueVisible = false;
        optionsVisible = false;
        uiController.ShowInventory(inventoryVisible, player.InventoryComponent.BuildInventoryTabs(player.WeaponSystemComponent));
        uiController.ShowPauseMenu(false);
        uiController.ShowJournal(false, null);
        uiController.ShowSkills(false, null, 0);
        uiController.ShowMap(false);
        uiController.ShowDialogue(false, null);
        uiController.ShowOptions(false);
        UpdateCursorAndTime();
    }

    public void ToggleJournal()
    {
        if (titleMenuVisible || playerDead || questManager == null)
        {
            return;
        }

        journalVisible = !journalVisible;
        pauseVisible = false;
        inventoryVisible = false;
        skillsVisible = false;
        mapVisible = false;
        dialogueVisible = false;
        optionsVisible = false;
        uiController.ShowPauseMenu(false);
        uiController.ShowInventory(false, null);
        uiController.ShowJournal(journalVisible, questManager.BuildJournalEntries());
        uiController.ShowSkills(false, null, 0);
        uiController.ShowMap(false);
        uiController.ShowDialogue(false, null);
        uiController.ShowOptions(false);
        UpdateCursorAndTime();
    }

    public void ToggleSkills()
    {
        if (titleMenuVisible || playerDead || player == null || uiController == null)
        {
            return;
        }

        skillsVisible = !skillsVisible;
        pauseVisible = false;
        inventoryVisible = false;
        journalVisible = false;
        mapVisible = false;
        dialogueVisible = false;
        optionsVisible = false;
        uiController.ShowSkills(skillsVisible, player.SkillTreeComponent.BuildEntries(), player.SkillTreeComponent.SkillPoints);
        uiController.ShowPauseMenu(false);
        uiController.ShowInventory(false, null);
        uiController.ShowJournal(false, null);
        uiController.ShowMap(false);
        uiController.ShowDialogue(false, null);
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
        journalVisible = false;
        skillsVisible = false;
        dialogueVisible = false;
        optionsVisible = false;
        if (mapVisible)
        {
            mapCamera.GetComponent<MapCameraFollow>()?.ResetView();
        }
        uiController.ShowMap(mapVisible);
        uiController.ShowPauseMenu(false);
        uiController.ShowInventory(false, null);
        uiController.ShowJournal(false, null);
        uiController.ShowSkills(false, null, 0);
        uiController.ShowDialogue(false, null);
        uiController.ShowOptions(false);
        UpdateCursorAndTime();
    }

    public void ShowOptionsMenu(bool visible)
    {
        if (visible)
        {
            ClearMenuInputGuards();
            optionsReturnToTitleMenu = titleMenuVisible;
            optionsReturnToPauseMenu = pauseVisible;
            optionsVisible = true;
            uiController.ShowOptions(true);
            pauseVisible = false;
            inventoryVisible = false;
            journalVisible = false;
            skillsVisible = false;
            mapVisible = false;
            dialogueVisible = false;
            uiController.ShowPauseMenu(false);
            uiController.ShowInventory(false, null);
            uiController.ShowJournal(false, null);
            uiController.ShowSkills(false, null, 0);
            uiController.ShowMap(false);
            uiController.ShowDialogue(false, null);
            UpdateCursorAndTime();
            return;
        }

        optionsVisible = false;
        uiController.ShowOptions(false);

        if (optionsReturnToTitleMenu)
        {
            ClearMenuInputGuards();
            uiController.ShowTitleMenu(true, playerDead ? "Mission Failed" : "Facility Sweep");
            uiController.SetMenuInteractable(true);
        }
        else if (optionsReturnToPauseMenu)
        {
            pauseVisible = true;
            uiController.ShowPauseMenu(true);
        }

        optionsReturnToTitleMenu = false;
        optionsReturnToPauseMenu = false;
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
        if (questManager != null)
        {
            saveData.player.questStates = questManager.CaptureState();
        }
        foreach (var saveable in saveables)
        {
            saveData.entities.Add(saveable.CaptureState());
        }

        File.WriteAllText(savePath, JsonUtility.ToJson(saveData, true));
        NotifyStatus($"Saved to {savePath}");
    }

    public bool TryUnlockSkill(string skillId)
    {
        if (player?.SkillTreeComponent == null || string.IsNullOrWhiteSpace(skillId))
        {
            return false;
        }

        bool unlocked = player.SkillTreeComponent.TryUnlock(skillId);
        if (unlocked)
        {
            player.RefreshAbilityUnlocks();
            RefreshHud();
        }

        return unlocked;
    }

    public void AwardSkillPoints(int amount, string reason)
    {
        if (player?.SkillTreeComponent == null || amount <= 0)
        {
            return;
        }

        player.SkillTreeComponent.AwardPoints(amount);
        if (!string.IsNullOrWhiteSpace(reason))
        {
            NotifyStatus($"{reason} reward secured");
        }
    }

    public List<QuestJournalEntryViewData> BuildJournalEntries()
    {
        return questManager != null ? questManager.BuildJournalEntries() : new List<QuestJournalEntryViewData>();
    }

    public bool StartDialogue(string npcId, string speakerName, DialogueData dialogueData)
    {
        if (dialogueVisible || dialogueData == null || uiController == null || titleMenuVisible || playerDead)
        {
            return false;
        }

        DialogueNodeData startNode = dialogueData.ResolveStartNode();
        if (startNode == null)
        {
            return false;
        }

        activeDialogue = new ActiveDialogueState
        {
            NpcId = npcId,
            SpeakerName = string.IsNullOrWhiteSpace(speakerName) ? startNode.SpeakerName : speakerName,
            DialogueData = dialogueData,
            CurrentNodeId = startNode.Id
        };
        dialogueVisible = true;
        pauseVisible = false;
        inventoryVisible = false;
        journalVisible = false;
        skillsVisible = false;
        mapVisible = false;
        optionsVisible = false;
        uiController.ShowPauseMenu(false);
        uiController.ShowInventory(false, null);
        uiController.ShowJournal(false, null);
        uiController.ShowSkills(false, null, 0);
        uiController.ShowMap(false);
        uiController.ShowOptions(false);
        uiController.ShowDialogue(true, BuildDialogueView());
        eventManager?.Publish(new DialogueStartedEvent
        {
            NpcId = npcId,
            DialogueId = dialogueData.Id,
            SpeakerName = activeDialogue.SpeakerName
        });
        UpdateCursorAndTime();
        return true;
    }

    public void SelectDialogueChoice(string choiceId)
    {
        if (!dialogueVisible || activeDialogue == null || activeDialogue.DialogueData == null)
        {
            return;
        }

        DialogueNodeData node = activeDialogue.DialogueData.GetNode(activeDialogue.CurrentNodeId);
        if (node == null)
        {
            CloseDialogue();
            return;
        }

        DialogueChoiceData choice = node.Choices?.FirstOrDefault(candidate => candidate != null && string.Equals(candidate.Id, choiceId, System.StringComparison.Ordinal));
        if (choice == null)
        {
            CompleteDialogue(node.Id);
            return;
        }

        if (!string.IsNullOrWhiteSpace(choice.StartQuestId))
        {
            questManager?.TryStartQuest(choice.StartQuestId);
        }

        if (!string.IsNullOrWhiteSpace(choice.StatusMessage))
        {
            NotifyStatus(choice.StatusMessage);
        }

        if (choice.ExitAfterChoice || string.IsNullOrWhiteSpace(choice.NextNodeId))
        {
            CompleteDialogue(node.Id);
            return;
        }

        DialogueNodeData nextNode = activeDialogue.DialogueData.GetNode(choice.NextNodeId);
        if (nextNode == null)
        {
            CompleteDialogue(node.Id);
            return;
        }

        activeDialogue.CurrentNodeId = nextNode.Id;
        uiController.ShowDialogue(true, BuildDialogueView());
        UpdateCursorAndTime();
    }

    public void CloseDialogue()
    {
        dialogueVisible = false;
        activeDialogue = null;
        uiController?.ShowDialogue(false, null);
        UpdateCursorAndTime();
        RefreshHud();
    }

    private DialogueViewData BuildDialogueView()
    {
        if (activeDialogue == null || activeDialogue.DialogueData == null)
        {
            return null;
        }

        DialogueNodeData node = activeDialogue.DialogueData.GetNode(activeDialogue.CurrentNodeId);
        if (node == null)
        {
            return null;
        }

        var view = new DialogueViewData
        {
            DialogueId = activeDialogue.DialogueData.Id,
            NpcId = activeDialogue.NpcId,
            SpeakerName = string.IsNullOrWhiteSpace(node.SpeakerName) ? activeDialogue.SpeakerName : node.SpeakerName,
            Body = node.Text,
            Choices = new List<DialogueChoiceViewData>()
        };

        foreach (DialogueChoiceData choice in node.Choices ?? new List<DialogueChoiceData>())
        {
            if (choice == null || string.IsNullOrWhiteSpace(choice.Text))
            {
                continue;
            }

            view.Choices.Add(new DialogueChoiceViewData
            {
                Id = string.IsNullOrWhiteSpace(choice.Id) ? choice.Text : choice.Id,
                Label = choice.Text
            });
        }

        return view;
    }

    private void CompleteDialogue(string finalNodeId)
    {
        if (activeDialogue?.DialogueData != null)
        {
            EventBus?.Publish(new DialogueCompletedEvent
            {
                NpcId = activeDialogue.NpcId,
                DialogueId = activeDialogue.DialogueData.Id,
                FinalNodeId = finalNodeId
            });
        }

        CloseDialogue();
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
        questManager?.RestoreState(saveData.player.questStates);
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
        if (Application.CanStreamedLevelBeLoaded("Bootstrap"))
        {
            SceneManager.LoadScene("Bootstrap");
            return;
        }

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

        if (titleMenuVisible && HasSaveGame)
        {
            LoadGame();
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
        journalVisible = false;
        skillsVisible = false;
        mapVisible = false;
        dialogueVisible = false;
        optionsVisible = false;
        activeDialogue = null;
        titleMenuVisible = true;
        uiController.ShowPauseMenu(false);
        uiController.ShowInventory(false, null);
        uiController.ShowJournal(false, null);
        uiController.ShowSkills(false, null, 0);
        uiController.ShowMap(false);
        uiController.ShowDialogue(false, null);
        uiController.ShowOptions(false);
        uiController.ShowTitleMenu(true, "Mission Failed");
        UpdateCursorAndTime();
    }

    public void NotifyStatus(string message)
    {
        Debug.Log($"[FPSDemo] {message}");
        uiController.SetStatusMessage(message);
        RefreshHud();
    }

    public void SetInteractionPrompt(string prompt)
    {
        uiController.SetInteractionPrompt(prompt);
    }

    public void RefreshHud()
    {
        if (player == null || uiController == null || !uiController.IsInitialized)
        {
            return;
        }

        var currentWeapon = player.WeaponSystemComponent.CurrentState;
        string resourceSummary = player.InventoryComponent.BuildHudSummary();
        string abilitySummary = player.AbilityComponent != null ? player.AbilityComponent.BuildHudSummary("Q", "C") : string.Empty;
        if (!string.IsNullOrWhiteSpace(abilitySummary))
        {
            resourceSummary = string.IsNullOrWhiteSpace(resourceSummary) ? abilitySummary : $"{resourceSummary}\n{abilitySummary}";
        }
        uiController.SetHudValues(player.StatsComponent.Health, player.StatsComponent.MaxHealth, player.StatsComponent.Stamina, player.StatsComponent.MaxStamina,
            currentWeapon?.Data?.DisplayName ?? "Unarmed", currentWeapon?.GetAmmoLabel() ?? string.Empty,
            resourceSummary);

        if (inventoryVisible)
        {
            uiController.ShowInventory(true, player.InventoryComponent.BuildInventoryTabs(player.WeaponSystemComponent));
        }
        if (journalVisible)
        {
            uiController.ShowJournal(true, questManager != null ? questManager.BuildJournalEntries() : new List<QuestJournalEntryViewData>());
        }
        if (skillsVisible)
        {
            uiController.ShowSkills(true, player.SkillTreeComponent.BuildEntries(), player.SkillTreeComponent.SkillPoints);
        }
        if (dialogueVisible)
        {
            uiController.ShowDialogue(true, BuildDialogueView());
        }
        uiController.RefreshOptions(CurrentOptions);
    }

    public void ApplyOptions(GameOptionsData updatedOptions)
    {
        CurrentOptions = updatedOptions;
        player?.MovementController.ApplyOptions(CurrentOptions);
        GameOptionsStore.Save(CurrentOptions);
        RefreshHud();
    }

    public string DescribeNearbyThreats(Vector3 position)
    {
        var enemies = registeredEnemies
            .Where(enemy => enemy != null && enemy.IsAlive && enemy.gameObject.activeInHierarchy)
            .OrderBy(enemy => Vector3.Distance(enemy.transform.position, position))
            .Take(3)
            .ToArray();

        if (enemies.Length == 0)
        {
            return "Scanner: no nearby hostiles";
        }

        return "Scanner: " + string.Join(", ", enemies.Select(enemy => $"{enemy.name} {Vector3.Distance(enemy.transform.position, position):0}m"));
    }


    public void RegisterEnemy(EnemyAgent enemy)
    {
        if (enemy != null && !registeredEnemies.Contains(enemy))
        {
            registeredEnemies.Add(enemy);
        }
    }

    public void UnregisterEnemy(EnemyAgent enemy)
    {
        if (enemy != null)
        {
            registeredEnemies.Remove(enemy);
        }
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
        registeredEnemies.Clear();
        registeredPickups.Clear();
        registeredDoors.Clear();
        if (saveableRoot == null)
        {
            return;
        }

        foreach (var behaviour in saveableRoot.GetComponentsInChildren<MonoBehaviour>(true))
        {
            if (behaviour is ISaveableEntity saveable)
            {
                saveables.Add(saveable);
            }

            if (behaviour is PickupItem pickup)
            {
                registeredPickups.Add(pickup);
            }

            if (behaviour is DoorController door)
            {
                registeredDoors.Add(door);
            }

            if (behaviour is EnemyAgent enemy)
            {
                registeredEnemies.Add(enemy);
            }
        }
    }

    private void BuildMapTexture()
    {
        if (mapCamera == null || player == null)
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
            follow.SetTarget(player.ActorTransform);
        }
    }

    private void UpdateCursorAndTime()
    {
        bool blockGameplay = titleMenuVisible || pauseVisible || inventoryVisible || journalVisible || skillsVisible || mapVisible || dialogueVisible || optionsVisible || playerDead;
        Time.timeScale = blockGameplay ? 0f : 1f;
        Cursor.lockState = blockGameplay ? CursorLockMode.None : CursorLockMode.Locked;
        Cursor.visible = blockGameplay;
    }

    public void AssignReferences(PlayerActorContext playerController, Camera overheadMapCamera, GameUiController ui, Transform rootWithSaveables)
    {
        EnsureRuntimeBootstrapped();
        player = playerController;
        mapCamera = overheadMapCamera;
        uiController = ui;
        saveableRoot = rootWithSaveables;
        stateValidator.Bind(eventManager);
        RegisterSaveables();
        BindRuntimeServicesToWorld();
    }

    public void ConfigureConsumables(IEnumerable<ConsumableEffectData> effects)
    {
        consumableEffects = effects?.Where(effect => effect != null && !string.IsNullOrWhiteSpace(effect.ItemId))
            .GroupBy(effect => effect.ItemId, System.StringComparer.Ordinal)
            .Select(group => group.First())
            .ToList() ?? new List<ConsumableEffectData>();
        RebuildConsumableLookup();
    }

    public bool TryUseInventoryItem(string itemId)
    {
        if (player?.InventoryComponent == null || string.IsNullOrWhiteSpace(itemId))
        {
            return false;
        }

        if (!consumableLookup.TryGetValue(itemId, out ConsumableEffectData effect) || effect == null)
        {
            NotifyStatus("This item cannot be used right now.");
            return false;
        }

        if (!player.InventoryComponent.HasItem(itemId))
        {
            NotifyStatus("Item not available.");
            return false;
        }

        if (!TryApplyConsumableEffect(effect))
        {
            NotifyStatus(string.IsNullOrWhiteSpace(effect.FailureStatus) ? "Item had no effect." : effect.FailureStatus);
            return false;
        }

        player.InventoryComponent.RemoveItem(itemId, 1);
        NotifyStatus(string.IsNullOrWhiteSpace(effect.SuccessStatus) ? "Item applied." : effect.SuccessStatus);
        RefreshHud();
        return true;
    }

    private void HandleStatusMessageEvent(StatusMessageEvent gameEvent)
    {
        if (gameEvent != null && !string.IsNullOrWhiteSpace(gameEvent.Message))
        {
            NotifyStatus(gameEvent.Message);
        }
    }

    private void HandleHudInvalidatedEvent(HudInvalidatedEvent gameEvent)
    {
        RefreshHud();
    }

    private void ShowInitialTitleMenu()
    {
        titleMenuVisible = true;
        pauseVisible = false;
        inventoryVisible = false;
        journalVisible = false;
        skillsVisible = false;
        mapVisible = false;
        dialogueVisible = false;
        optionsVisible = false;
        playerDead = false;
        activeDialogue = null;
        waitingForCleanMenuInput = true;
        waitingForMenuPointerMotion = true;
        titleMenuShownRealtime = Time.realtimeSinceStartup;
        uiController.ShowPauseMenu(false);
        uiController.ShowInventory(false, null);
        uiController.ShowJournal(false, null);
        uiController.ShowSkills(false, null, 0);
        uiController.ShowMap(false);
        uiController.ShowDialogue(false, null);
        uiController.ShowOptions(false);
        uiController.ShowTitleMenu(true);
        uiController.SetMenuInteractable(false);
        RefreshHud();
        UpdateCursorAndTime();
    }

    private void ClearMenuInputGuards()
    {
        waitingForCleanMenuInput = false;
        waitingForMenuPointerMotion = false;
        uiController?.SetMenuInteractable(true);
    }

    private void HideAllMenus()
    {
        titleMenuVisible = false;
        pauseVisible = false;
        inventoryVisible = false;
        journalVisible = false;
        skillsVisible = false;
        mapVisible = false;
        dialogueVisible = false;
        optionsVisible = false;
        activeDialogue = null;
        uiController.ShowTitleMenu(false);
        uiController.ShowPauseMenu(false);
        uiController.ShowInventory(false, null);
        uiController.ShowJournal(false, null);
        uiController.ShowSkills(false, null, 0);
        uiController.ShowMap(false);
        uiController.ShowDialogue(false, null);
        uiController.ShowOptions(false);
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
        yield return TryCapturePreview("smoke_hub_furniture.png", "PropsRoot/ThirdPartyArt/FurnitureMegaPack/Hub", new Vector3(-2.4f, 1.3f, -2.1f));
        yield return TryCapturePreview("smoke_security_furniture.png", "PropsRoot/ThirdPartyArt/FurnitureMegaPack/Security", new Vector3(-2.1f, 1.2f, -2.3f));
        stateValidator?.ResetCounters();
        float previousHealth = player.StatsComponent.Health;
        EventBus?.Publish(new DamageEvent
        {
            SourceRoot = player.ActorTransform.gameObject,
            TargetRoot = player.ActorTransform.gameObject,
            Amount = 9f,
            HitPoint = player.ActorTransform.position,
            HitDirection = Vector3.forward
        });
        yield return new WaitForSecondsRealtime(0.1f);
        stateValidator?.ValidatePlayerDamage(player.StatsComponent, previousHealth);

        stateValidator?.ResetCounters();
        player.WeaponSystemComponent.SelectSlot(1);
        int previousAmmo = player.WeaponSystemComponent.CurrentState != null ? player.WeaponSystemComponent.CurrentState.MagazineAmmo : 0;
        player.WeaponSystemComponent.TriggerCurrent(player);
        yield return new WaitForSecondsRealtime(0.2f);
        if (player.WeaponSystemComponent.CurrentState != null)
        {
            stateValidator?.ValidateWeaponFire(player.WeaponSystemComponent.CurrentState, previousAmmo);
        }

        player.WeaponSystemComponent.SelectSlot(2);
        player.WeaponSystemComponent.TriggerCurrent(player);
        yield return new WaitForSecondsRealtime(0.2f);

        player.WeaponSystemComponent.SelectSlot(3);
        player.WeaponSystemComponent.TriggerCurrent(player);
        yield return new WaitForSecondsRealtime(0.2f);

        ToggleInventory();
        yield return new WaitForSecondsRealtime(0.2f);
        uiController.SelectInventoryTab(InventoryTab.Keys);
        yield return new WaitForSecondsRealtime(0.1f);
        ToggleInventory();

        stateValidator?.ResetCounters();
        float healthBeforeMedkit = player.StatsComponent.Health;
        int medkitBeforeUse = player.InventoryComponent.GetQuantity("item_medkit");
        bool medkitUsed = TryUseInventoryItem("item_medkit");
        yield return new WaitForSecondsRealtime(0.1f);
        if (medkitUsed)
        {
            stateValidator?.ValidateConsumableUse(player.InventoryComponent, "item_medkit", medkitBeforeUse, player.StatsComponent, healthBeforeMedkit);
        }

        ToggleMap();
        yield return new WaitForSecondsRealtime(0.2f);
        mapCamera.GetComponent<MapCameraFollow>()?.Pan(new Vector2(8f, -6f));
        mapCamera.GetComponent<MapCameraFollow>()?.Zoom(1f);
        yield return new WaitForSecondsRealtime(0.1f);
        ToggleMap();

        TogglePauseMenu();
        yield return new WaitForSecondsRealtime(0.2f);
        TogglePauseMenu();

        DialogueNpcInteractable echoNpc = saveableRoot != null
            ? saveableRoot.GetComponentsInChildren<DialogueNpcInteractable>(true).FirstOrDefault(candidate => candidate != null && candidate.NpcId == "npc_echo")
            : null;
        if (echoNpc != null)
        {
            stateValidator?.ResetCounters();
            echoNpc.Interact(player);
            yield return new WaitForSecondsRealtime(0.1f);
            SelectDialogueChoice("echo_accept_security");
            yield return new WaitForSecondsRealtime(0.1f);
            stateValidator?.ValidateDialogueCompletion();
        }

        DialogueNpcInteractable valeNpc = saveableRoot != null
            ? saveableRoot.GetComponentsInChildren<DialogueNpcInteractable>(true).FirstOrDefault(candidate => candidate != null && candidate.NpcId == "npc_vale")
            : null;
        if (valeNpc != null)
        {
            stateValidator?.ResetCounters();
            valeNpc.Interact(player);
            yield return new WaitForSecondsRealtime(0.1f);
            SelectDialogueChoice("vale_accept_supply");
            yield return new WaitForSecondsRealtime(0.1f);
            stateValidator?.ValidateDialogueCompletion();
        }

        ToggleJournal();
        yield return new WaitForSecondsRealtime(0.15f);
        ToggleJournal();

        stateValidator?.ResetCounters();
        var firstPickup = registeredPickups.FirstOrDefault(candidate =>
            candidate != null &&
            candidate.gameObject.activeInHierarchy &&
            candidate.ItemData != null &&
            candidate.ItemData.Id == "key_red");
        firstPickup ??= registeredPickups.FirstOrDefault(candidate =>
            candidate != null &&
            candidate.gameObject.activeInHierarchy &&
            candidate.ItemData != null &&
            candidate.ItemData.ItemType != ItemType.Ammo);
        if (firstPickup != null)
        {
            var pickupItemData = firstPickup.ItemData;
            int previousQuantity = pickupItemData != null ? player.InventoryComponent.GetQuantity(pickupItemData.Id) : 0;
            firstPickup.Interact(player);
            yield return new WaitForSecondsRealtime(0.1f);
            if (pickupItemData != null)
            {
                stateValidator?.ValidateInventoryPickup(player.InventoryComponent, pickupItemData.Id, previousQuantity);
            }
        }
        yield return new WaitForSecondsRealtime(0.1f);

        stateValidator?.ResetCounters();
        PickupItem medkitPickup = registeredPickups.FirstOrDefault(candidate =>
            candidate != null &&
            candidate.gameObject.activeInHierarchy &&
            candidate.ItemData != null &&
            candidate.ItemData.Id == "item_medkit");
        if (medkitPickup != null)
        {
            int previousQuantity = player.InventoryComponent.GetQuantity("item_medkit");
            medkitPickup.Interact(player);
            yield return new WaitForSecondsRealtime(0.1f);
            stateValidator?.ValidateInventoryPickup(player.InventoryComponent, "item_medkit", previousQuantity);
        }

        if (player.AbilityComponent != null)
        {
            stateValidator?.ResetCounters();
            player.StatsComponent.ApplyDamage(18f, player.ActorTransform.position, -player.ActorTransform.forward);
            yield return new WaitForSecondsRealtime(0.05f);
            float abilityHealthBefore = player.StatsComponent.Health;
            float abilityStaminaBefore = player.StatsComponent.Stamina;
            player.AbilityComponent.TryActivateBySlot(0);
            yield return new WaitForSecondsRealtime(0.1f);
            stateValidator?.ValidateAbilityUse(player.StatsComponent, abilityHealthBefore, abilityStaminaBefore);
        }

        registeredDoors
            .FirstOrDefault(door => door != null && door.gameObject.activeInHierarchy)?
            .Interact(player);
        yield return new WaitForSecondsRealtime(0.1f);

        EnemyAgent enemy = registeredEnemies.FirstOrDefault(candidate => candidate != null && candidate.IsAlive && candidate.gameObject.activeInHierarchy && candidate.SaveId == "sentry_hub");
        enemy ??= registeredEnemies.FirstOrDefault(candidate => candidate != null && candidate.IsAlive && candidate.gameObject.activeInHierarchy);
        if (enemy != null)
        {
            stateValidator?.ResetCounters();
            int previousSkillPoints = player.SkillTreeComponent.SkillPoints;
            EventBus?.Publish(new DamageEvent
            {
                SourceRoot = player.ActorTransform.gameObject,
                TargetRoot = enemy.gameObject,
                Amount = enemy.Health + 1f,
                HitPoint = enemy.transform.position,
                HitDirection = (enemy.transform.position - player.ActorTransform.position).normalized
            });
            yield return new WaitForSecondsRealtime(0.1f);
            stateValidator?.ValidateEnemyDeath(enemy);
            stateValidator?.ValidateSkillPointGain(player.SkillTreeComponent, previousSkillPoints);
            stateValidator?.ValidateQuestCompletion(questManager, "quest_security_sweep");
        }

        if (valeNpc != null)
        {
            stateValidator?.ResetCounters();
            int armorPatchBeforeReward = player.InventoryComponent.GetQuantity("item_armor_patch");
            valeNpc.Interact(player);
            yield return new WaitForSecondsRealtime(0.1f);
            SelectDialogueChoice("vale_turnin_ack");
            yield return new WaitForSecondsRealtime(0.1f);
            stateValidator?.ValidateDialogueCompletion();
            stateValidator?.ValidateQuestCompletion(questManager, "quest_supply_recovery");
            stateValidator?.ValidateInventoryQuantityIncrease(player.InventoryComponent, "item_armor_patch", armorPatchBeforeReward);
        }

        ToggleSkills();
        yield return new WaitForSecondsRealtime(0.15f);
        var unlockCandidate = player.SkillTreeComponent.BuildEntries().FirstOrDefault(entry => entry.Available && !entry.Unlocked);
        if (unlockCandidate != null)
        {
            TryUnlockSkill(unlockCandidate.Id);
            yield return new WaitForSecondsRealtime(0.1f);
        }
        ToggleSkills();

        SaveGame();
        yield return new WaitForSecondsRealtime(0.1f);
        LoadGame();
        yield return new WaitForSecondsRealtime(0.2f);

        NotifyStatus("Smoke test completed");
        yield return new WaitForSecondsRealtime(0.3f);
        ExitGame();
    }

    private bool TryApplyConsumableEffect(ConsumableEffectData effect)
    {
        if (effect == null || player?.StatsComponent == null)
        {
            return false;
        }

        switch (effect.EffectType)
        {
            case ConsumableEffectType.Heal:
                if (player.StatsComponent.Health >= player.StatsComponent.MaxHealth - 0.01f)
                {
                    return false;
                }

                player.StatsComponent.Heal(effect.Amount);
                return true;

            case ConsumableEffectType.RestoreStamina:
                if (player.StatsComponent.Stamina >= player.StatsComponent.MaxStamina - 0.01f)
                {
                    return false;
                }

                player.StatsComponent.RegenerateStamina(effect.Amount);
                return true;

            default:
                return false;
        }
    }

    private void RebuildConsumableLookup()
    {
        consumableLookup.Clear();
        foreach (ConsumableEffectData effect in consumableEffects)
        {
            if (effect == null || string.IsNullOrWhiteSpace(effect.ItemId))
            {
                continue;
            }

            consumableLookup[effect.ItemId] = effect;
        }
    }

    private void BindRuntimeServicesToWorld()
    {
        player?.BindRuntimeServices(this);
        questManager?.BindRuntimeServices(this);

        foreach (var pickup in registeredPickups)
        {
            pickup?.BindRuntimeServices(this);
        }

        foreach (var door in registeredDoors)
        {
            door?.BindRuntimeServices(this);
        }

        foreach (var enemy in registeredEnemies)
        {
            enemy?.BindRuntimeServices(this);
        }

        if (saveableRoot == null)
        {
            return;
        }

        foreach (var npc in saveableRoot.GetComponentsInChildren<DialogueNpcInteractable>(true))
        {
            npc?.BindRuntimeServices(this);
        }
    }

    private IEnumerator TryCapturePreview(string fileName, string hierarchyPath, Vector3 framingScale)
    {
        var target = ResolveHierarchyPath(hierarchyPath);
        if (target == null || target.GetComponentsInChildren<Renderer>(true).Length == 0)
        {
            yield break;
        }

        yield return CapturePreview(fileName, hierarchyPath, framingScale);
    }

    private IEnumerator CapturePreview(string fileName, string hierarchyPath, Vector3 framingScale)
    {
        if (player?.ViewCamera == null || string.IsNullOrWhiteSpace(fileName))
        {
            Debug.LogWarning("[FPSDemo] CapturePreview skipped: missing camera or filename.");
            yield break;
        }

        var target = ResolveHierarchyPath(hierarchyPath);
        if (target == null)
        {
            Debug.LogWarning($"[FPSDemo] CapturePreview skipped: target not found for {hierarchyPath}");
            yield break;
        }

        var renderers = target.GetComponentsInChildren<Renderer>(true);
        if (renderers.Length == 0)
        {
            Debug.LogWarning($"[FPSDemo] CapturePreview skipped: no renderers under {hierarchyPath}");
            yield break;
        }

        var bounds = renderers[0].bounds;
        foreach (var renderer in renderers.Skip(1))
        {
            bounds.Encapsulate(renderer.bounds);
        }

        var camera = player.ViewCamera;
        var cameraTransform = camera.transform;
        Vector3 originalPosition = cameraTransform.position;
        Quaternion originalRotation = cameraTransform.rotation;
        float originalFov = camera.fieldOfView;

        var extents = bounds.extents + Vector3.one * 0.35f;
        var offset = Vector3.Scale(extents, framingScale);
        cameraTransform.position = bounds.center + offset;
        cameraTransform.LookAt(bounds.center + Vector3.up * Mathf.Max(0.12f, bounds.extents.y * 0.22f));
        camera.fieldOfView = Mathf.Clamp(originalFov - 8f, 42f, originalFov);

        string path = Path.Combine(Application.persistentDataPath, fileName);
        Directory.CreateDirectory(Path.GetDirectoryName(path) ?? Application.persistentDataPath);
        var previousTarget = camera.targetTexture;
        var previousActive = RenderTexture.active;
        var previewTarget = new RenderTexture(1280, 720, 24, RenderTextureFormat.ARGB32);
        yield return new WaitForEndOfFrame();
        camera.targetTexture = previewTarget;
        camera.Render();
        RenderTexture.active = previewTarget;

        var previewTexture = new Texture2D(previewTarget.width, previewTarget.height, TextureFormat.RGB24, false);
        previewTexture.ReadPixels(new Rect(0f, 0f, previewTarget.width, previewTarget.height), 0, 0, false);
        previewTexture.Apply(false, false);
        File.WriteAllBytes(path, previewTexture.EncodeToPNG());

        cameraTransform.position = originalPosition;
        cameraTransform.rotation = originalRotation;
        camera.fieldOfView = originalFov;
        camera.targetTexture = previousTarget;
        RenderTexture.active = previousActive;
        Destroy(previewTexture);
        previewTarget.Release();
        Destroy(previewTarget);
        Debug.Log($"[FPSDemo] Captured smoke preview {path}");
    }

    private static Transform ResolveHierarchyPath(string hierarchyPath)
    {
        if (string.IsNullOrWhiteSpace(hierarchyPath))
        {
            return null;
        }

        var segments = hierarchyPath.Split('/').Where(segment => !string.IsNullOrWhiteSpace(segment)).ToArray();
        if (segments.Length == 0)
        {
            return null;
        }

        Transform current = null;
        for (int sceneIndex = 0; sceneIndex < SceneManager.sceneCount; sceneIndex++)
        {
            var scene = SceneManager.GetSceneAt(sceneIndex);
            if (!scene.isLoaded)
            {
                continue;
            }

            current = scene
                .GetRootGameObjects()
                .Select(candidate => candidate.transform)
                .FirstOrDefault(candidate =>
                    candidate.name == segments[0] ||
                    FindDescendantByName(candidate, segments[0]) != null);
            if (current == null)
            {
                continue;
            }

            if (current.name != segments[0])
            {
                current = FindDescendantByName(current, segments[0]);
            }

            break;
        }

        if (current == null)
        {
            return null;
        }

        for (int i = 1; i < segments.Length; i++)
        {
            current = current.Find(segments[i]) ?? FindDescendantByName(current, segments[i]);
            if (current == null)
            {
                return null;
            }
        }

        return current;
    }

    private static Transform FindDescendantByName(Transform root, string name)
    {
        foreach (Transform child in root)
        {
            if (child.name == name)
            {
                return child;
            }

            var nested = FindDescendantByName(child, name);
            if (nested != null)
            {
                return nested;
            }
        }

        return null;
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
