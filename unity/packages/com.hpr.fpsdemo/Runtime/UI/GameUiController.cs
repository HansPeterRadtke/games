using System;
using System.Collections.Generic;
using System.Linq;
using UnityEngine;
using UnityEngine.EventSystems;
using UnityEngine.UI;

public class GameUiController : MonoBehaviour
{
    private IGameMenuCommands menuCommands;
    private ISkillTreeCommands skillCommands;
    private IInputBindingsSource inputBindings;
    private IOptionsController optionsController;
    private Font uiFont;
    private Canvas canvas;
    private RectTransform root;
    private GameObject hudRoot;
    private Text statusText;
    private Text interactionText;
    private Text weaponText;
    private Text ammoText;
    private Text resourceText;
    private Slider healthSlider;
    private Slider staminaSlider;
    private Text menuTitleText;
    private GameObject menuPanel;
    private GameObject optionsPanel;
    private GameObject inventoryPanel;
    private GameObject mapPanel;
    private GameObject skillsPanel;
    private RectTransform inventoryGrid;
    private Text inventoryDetailText;
    private readonly Dictionary<InventoryTab, Button> inventoryTabButtons = new Dictionary<InventoryTab, Button>();
    private readonly List<GameObject> inventoryCards = new List<GameObject>();
    private readonly List<GameObject> skillCards = new List<GameObject>();
    private List<InventoryTabData> inventoryTabs = new List<InventoryTabData>();
    private InventoryTab currentInventoryTab = InventoryTab.Weapons;
    private RawImage mapImage;
    private Text mapHintText;
    private RectTransform skillsGrid;
    private Text skillPointsText;
    private Text skillDetailText;
    private Text optionsStatusText;
    private Button newGameButton;
    private Text newGameButtonText;
    private Button resumeButton;
    private Button saveButton;
    private Button loadButton;
    private Button restartButton;
    private Button optionsButton;
    private Button exitButton;
    private Text loadButtonText;
    private Text restartButtonText;
    private Text menuHintText;
    private readonly Dictionary<GameAction, Button> bindingButtons = new Dictionary<GameAction, Button>();
    private readonly Dictionary<GameAction, Text> bindingButtonTexts = new Dictionary<GameAction, Text>();
    private GameAction? pendingRebindAction;
    private float statusTimer;
    private bool hudBuilt;

    public bool IsRebindingKey => pendingRebindAction.HasValue;
    public bool IsInitialized => hudBuilt;

    public void Initialize(MonoBehaviour services, RenderTexture mapTexture)
    {
        menuCommands = ResolveInterface<IGameMenuCommands>(services);
        skillCommands = ResolveInterface<ISkillTreeCommands>(services);
        inputBindings = ResolveInterface<IInputBindingsSource>(services);
        optionsController = ResolveInterface<IOptionsController>(services);
        uiFont = Resources.GetBuiltinResource<Font>("Arial.ttf");
        BuildCanvas();
        mapImage.texture = mapTexture;
        RefreshOptions(inputBindings != null ? inputBindings.CurrentOptions : GameOptionsData.CreateDefault());
    }

    private void Update()
    {
        if (statusTimer > 0f)
        {
            statusTimer -= Time.unscaledDeltaTime;
            if (statusTimer <= 0f)
            {
                statusText.text = string.Empty;
            }
        }

        if (!pendingRebindAction.HasValue)
        {
            return;
        }

        foreach (KeyCode keyCode in Enum.GetValues(typeof(KeyCode)))
        {
            if (Input.GetKeyDown(keyCode))
            {
                if (keyCode == KeyCode.Escape)
                {
                    pendingRebindAction = null;
                    optionsStatusText.text = "Rebind cancelled";
                }
                else
                {
                    optionsController?.RebindAction(pendingRebindAction.Value, keyCode);
                    pendingRebindAction = null;
                    optionsStatusText.text = string.Empty;
                }
                RefreshOptions(inputBindings != null ? inputBindings.CurrentOptions : GameOptionsData.CreateDefault());
                break;
            }
        }
    }

    public void SetHudValues(float health, float maxHealth, float stamina, float maxStamina, string weaponName, string ammoLabel, string resources)
    {
        if (!hudBuilt || healthSlider == null || staminaSlider == null || weaponText == null || ammoText == null || resourceText == null)
        {
            return;
        }

        healthSlider.value = maxHealth <= 0f ? 0f : health / maxHealth;
        staminaSlider.value = maxStamina <= 0f ? 0f : stamina / maxStamina;
        weaponText.text = weaponName;
        ammoText.text = ammoLabel;
        resourceText.text = resources;
    }

    public void SetInteractionPrompt(string prompt)
    {
        if (interactionText == null)
        {
            return;
        }

        interactionText.text = string.IsNullOrWhiteSpace(prompt) ? string.Empty : prompt;
    }

    public void SetStatusMessage(string message)
    {
        if (statusText == null)
        {
            return;
        }

        statusText.text = message;
        statusTimer = 4f;
    }

    public void ShowTitleMenu(bool show, string title = "Facility Sweep")
    {
        if (menuPanel == null)
        {
            return;
        }

        if (show)
        {
            optionsPanel?.SetActive(false);
            inventoryPanel?.SetActive(false);
            mapPanel?.SetActive(false);
            skillsPanel?.SetActive(false);
        }

        menuPanel.SetActive(show);
        ShowHud(!show);
        menuTitleText.text = title;
        bool hasSave = menuCommands != null && menuCommands.HasSaveGame;
        bool missionFailed = title == "Mission Failed";
        newGameButtonText.text = missionFailed ? "Restart Run" : (hasSave ? "Continue" : "Start Game");
        loadButtonText.text = hasSave ? "Load Save" : "Load Game";
        restartButtonText.text = missionFailed ? "New Game" : "New Game";
        menuHintText.text = missionFailed
            ? (hasSave ? "Restart immediately or load the latest save" : "Press Enter or click Restart Run")
            : (hasSave ? "Continue resumes the latest save. New Game starts fresh." : "Press Enter or click Start Game");
        newGameButton.gameObject.SetActive(true);
        resumeButton.gameObject.SetActive(false);
        saveButton.gameObject.SetActive(false);
        loadButton.gameObject.SetActive(hasSave);
        loadButton.interactable = hasSave;
        restartButton.gameObject.SetActive(hasSave && !missionFailed);
        optionsButton.gameObject.SetActive(true);
        exitButton.gameObject.SetActive(true);
        SetMenuInteractable(true);
        FocusButton(newGameButton);
    }

    public void ShowPauseMenu(bool show)
    {
        if (menuPanel == null)
        {
            return;
        }

        menuPanel.SetActive(show);
        if (!show)
        {
            return;
        }

        bool hasSave = menuCommands != null && menuCommands.HasSaveGame;
        menuTitleText.text = "Paused";
        newGameButton.gameObject.SetActive(false);
        resumeButton.gameObject.SetActive(true);
        saveButton.gameObject.SetActive(true);
        loadButton.gameObject.SetActive(true);
        loadButton.interactable = hasSave;
        restartButton.gameObject.SetActive(true);
        restartButtonText.text = "Restart Run";
        optionsButton.gameObject.SetActive(true);
        exitButton.gameObject.SetActive(true);
        menuHintText.text = hasSave ? "Press Esc to resume. Save/Load is available." : "Press Esc to resume. Save Game creates the first save.";
        SetMenuInteractable(true);
        FocusButton(resumeButton);
    }

    public void SetMenuInteractable(bool interactable)
    {
        if (newGameButton != null)
        {
            newGameButton.interactable = interactable;
        }
        if (resumeButton != null)
        {
            resumeButton.interactable = interactable;
        }
        if (saveButton != null)
        {
            saveButton.interactable = interactable;
        }
        if (loadButton != null)
        {
            loadButton.interactable = interactable;
        }
        if (restartButton != null)
        {
            restartButton.interactable = interactable;
        }
        if (optionsButton != null)
        {
            optionsButton.interactable = interactable;
        }
        if (exitButton != null)
        {
            exitButton.interactable = interactable;
        }

        if (!interactable)
        {
            ClearSelection();
        }
    }

    public void ShowOptions(bool show)
    {
        optionsPanel.SetActive(show);
        if (!show)
        {
            pendingRebindAction = null;
            optionsStatusText.text = string.Empty;
        }
    }

    public void ShowInventory(bool show, List<InventoryTabData> tabs)
    {
        inventoryPanel.SetActive(show);
        skillsPanel?.SetActive(false);
        if (!show || tabs == null)
        {
            return;
        }

        inventoryTabs = tabs;
        if (inventoryTabs.Count > 0 && !inventoryTabs.Exists(tab => tab.Tab == currentInventoryTab))
        {
            currentInventoryTab = inventoryTabs[0].Tab;
        }
        RefreshInventoryContents();
    }

    public void ShowMap(bool show)
    {
        mapPanel.SetActive(show);
        skillsPanel?.SetActive(false);
        if (show && mapHintText != null)
        {
            mapHintText.text = "RMB drag to pan  |  Mouse wheel zoom";
        }
    }

    public void ShowSkills(bool show, List<SkillEntryViewData> entries, int skillPoints)
    {
        if (skillsPanel == null)
        {
            return;
        }

        skillsPanel.SetActive(show);
        if (!show || entries == null)
        {
            return;
        }

        RefreshSkills(entries, skillPoints);
    }

    public void SelectInventoryTab(InventoryTab tab)
    {
        currentInventoryTab = tab;
        RefreshInventoryContents();
    }

    public void ShowHud(bool show)
    {
        if (hudRoot != null)
        {
            hudRoot.SetActive(show);
        }
    }

    public void RefreshOptions(GameOptionsData options)
    {
        if (!hudBuilt || options == null)
        {
            return;
        }

        SetSliderValue("fov", options.fieldOfView, "0");
        SetSliderValue("sensitivity", options.lookSensitivity, "0.0");
        SetSliderValue("master", options.masterVolume * 100f, "0");
        SetSliderValue("music", options.musicVolume * 100f, "0");
        SetSliderValue("sfx", options.sfxVolume * 100f, "0");
        if (qualityButtonText != null)
        {
            int clamped = Mathf.Clamp(options.qualityLevel, 0, Mathf.Max(0, QualitySettings.names.Length - 1));
            qualityButtonText.text = QualitySettings.names[clamped];
        }
        if (invertYToggle != null)
        {
            invertYToggle.isOn = options.invertY;
        }

        foreach (var pair in bindingButtonTexts)
        {
            if (pair.Value != null)
            {
                pair.Value.text = GameOptionsStore.GetBinding(options, pair.Key).ToString();
            }
        }
    }

    private readonly Dictionary<string, Slider> sliders = new Dictionary<string, Slider>();
    private readonly Dictionary<string, Text> sliderValues = new Dictionary<string, Text>();
    private Button qualityButton;
    private Text qualityButtonText;
    private Toggle invertYToggle;

    private void BuildCanvas()
    {
        var canvasGo = new GameObject("HUD Canvas", typeof(Canvas), typeof(CanvasScaler), typeof(GraphicRaycaster));
        canvasGo.transform.SetParent(transform, false);
        canvas = canvasGo.GetComponent<Canvas>();
        canvas.renderMode = RenderMode.ScreenSpaceOverlay;
        var scaler = canvasGo.GetComponent<CanvasScaler>();
        scaler.uiScaleMode = CanvasScaler.ScaleMode.ScaleWithScreenSize;
        scaler.referenceResolution = new Vector2(1920f, 1080f);
        scaler.screenMatchMode = CanvasScaler.ScreenMatchMode.MatchWidthOrHeight;
        root = canvasGo.GetComponent<RectTransform>();

        if (EventSystem.current == null)
        {
            new GameObject("EventSystem", typeof(EventSystem), typeof(StandaloneInputModule));
        }

        BuildHud();
        BuildMenu();
        BuildOptions();
        BuildInventory();
        BuildSkills();
        BuildMap();
        hudBuilt = true;
    }

    private void RefreshSkills(List<SkillEntryViewData> entries, int skillPoints)
    {
        if (skillsGrid == null || skillPointsText == null)
        {
            return;
        }

        foreach (var card in skillCards)
        {
            if (card != null)
            {
                Destroy(card);
            }
        }
        skillCards.Clear();

        skillPointsText.text = $"Skill Points: {skillPoints}";
        skillDetailText.text = "Unlock permanent combat and movement upgrades.";

        foreach (SkillEntryViewData entry in entries)
        {
            skillCards.Add(CreateSkillCard(skillsGrid, entry).gameObject);
        }

        LayoutRebuilder.ForceRebuildLayoutImmediate(skillsGrid);
        Canvas.ForceUpdateCanvases();
    }

    private void RefreshInventoryContents()
    {
        if (inventoryGrid == null)
        {
            return;
        }

        foreach (var card in inventoryCards)
        {
            if (card != null)
            {
                Destroy(card);
            }
        }
        inventoryCards.Clear();

        foreach (var pair in inventoryTabButtons)
        {
            var image = pair.Value.GetComponent<Image>();
            if (image != null)
            {
                image.color = pair.Key == currentInventoryTab
                    ? new Color(0.28f, 0.42f, 0.62f, 0.95f)
                    : new Color(0.16f, 0.2f, 0.26f, 0.95f);
            }
        }

        var activeTab = inventoryTabs.Find(tab => tab.Tab == currentInventoryTab);
        if (activeTab == null)
        {
            inventoryDetailText.text = string.Empty;
            return;
        }

        foreach (var entry in activeTab.Entries)
        {
            inventoryCards.Add(CreateInventoryCard(inventoryGrid, entry).gameObject);
        }

        LayoutRebuilder.ForceRebuildLayoutImmediate(inventoryGrid);
        Canvas.ForceUpdateCanvases();

        inventoryDetailText.text = activeTab.Tab switch
        {
            InventoryTab.Weapons => "Weapons are grouped by slot. 1-9 equips instantly. RMB aims the active weapon.",
            InventoryTab.Consumables => "Consumables are instant-use support items. Medkits and armor patches are limited.",
            InventoryTab.Keys => "Security clearance persists across saves. Keycards unlock the corresponding doors.",
            _ => "Utility equipment covers scanners, repair tools, the map, and interaction hints."
        };
    }

    private void BuildHud()
    {
        hudRoot = new GameObject("HudRoot");
        hudRoot.transform.SetParent(root, false);
        var hudRt = hudRoot.AddComponent<RectTransform>();
        hudRt.anchorMin = Vector2.zero;
        hudRt.anchorMax = Vector2.one;
        hudRt.offsetMin = Vector2.zero;
        hudRt.offsetMax = Vector2.zero;

        var statsPanel = CreatePanel("StatsPanel", hudRt, new Vector2(22f, -22f), new Vector2(340f, 126f), new Color(0f, 0f, 0f, 0.45f), new Vector2(0f, 1f), new Vector2(0f, 1f));
        CreateText("StatsTitle", statsPanel, "PLAYER", 22, TextAnchor.UpperLeft, new Vector2(14f, -12f), new Vector2(100f, 28f));
        CreateText("HealthLabel", statsPanel, "HP", 18, TextAnchor.MiddleLeft, new Vector2(14f, -48f), new Vector2(36f, 24f));
        healthSlider = CreateSlider("HealthSlider", statsPanel, new Vector2(58f, -48f), new Vector2(260f, 20f), new Color(0.75f, 0.15f, 0.18f));
        CreateText("StaminaLabel", statsPanel, "STM", 18, TextAnchor.MiddleLeft, new Vector2(14f, -82f), new Vector2(44f, 24f));
        staminaSlider = CreateSlider("StaminaSlider", statsPanel, new Vector2(58f, -82f), new Vector2(260f, 20f), new Color(0.12f, 0.74f, 0.24f));

        var weaponPanel = CreatePanel("WeaponPanel", hudRt, new Vector2(-22f, -22f), new Vector2(360f, 110f), new Color(0f, 0f, 0f, 0.45f), new Vector2(1f, 1f), new Vector2(1f, 1f));
        weaponText = CreateText("WeaponName", weaponPanel, "Pulse Pistol", 24, TextAnchor.UpperRight, new Vector2(-16f, -14f), new Vector2(320f, 28f));
        ammoText = CreateText("AmmoLabel", weaponPanel, "16/64", 22, TextAnchor.UpperRight, new Vector2(-16f, -48f), new Vector2(320f, 26f));
        resourceText = CreateText("ResourceText", weaponPanel, string.Empty, 16, TextAnchor.UpperRight, new Vector2(-16f, -80f), new Vector2(320f, 22f));

        interactionText = CreateCenteredText("InteractionText", hudRt, string.Empty, 28, TextAnchor.MiddleCenter, new Vector2(0f, -120f), new Vector2(780f, 36f));
        interactionText.color = new Color(1f, 0.95f, 0.7f, 1f);
        statusText = CreateCenteredText("StatusText", hudRt, string.Empty, 22, TextAnchor.MiddleCenter, new Vector2(0f, -180f), new Vector2(980f, 32f));
        statusText.color = new Color(0.75f, 0.92f, 1f, 1f);

        var crosshair = CreateCenteredText("Crosshair", hudRt, "+", 28, TextAnchor.MiddleCenter, Vector2.zero, new Vector2(32f, 32f));
        crosshair.color = Color.white;
    }

    private void BuildMenu()
    {
        menuPanel = CreatePanel("MenuPanel", root, Vector2.zero, new Vector2(420f, 540f), new Color(0.03f, 0.04f, 0.06f, 0.9f), new Vector2(0.5f, 0.5f), new Vector2(0.5f, 0.5f)).gameObject;
        var panelRt = (RectTransform)menuPanel.transform;
        menuTitleText = CreateText("MenuTitle", panelRt, "Facility Sweep", 36, TextAnchor.MiddleCenter, new Vector2(0f, -52f), new Vector2(340f, 40f));
        newGameButton = CreateMenuButton(panelRt, "NewGame", "Start Game", new Vector2(0f, -130f), () => menuCommands?.ActivatePrimaryMenuAction());
        newGameButtonText = newGameButton.GetComponentInChildren<Text>();
        resumeButton = CreateMenuButton(panelRt, "Resume", "Resume", new Vector2(0f, -130f), () => menuCommands?.ResumeSession());
        saveButton = CreateMenuButton(panelRt, "Save", "Save Game", new Vector2(0f, -188f), () => menuCommands?.SaveGame());
        loadButton = CreateMenuButton(panelRt, "Load", "Load Game", new Vector2(0f, -246f), () => menuCommands?.LoadGame());
        restartButton = CreateMenuButton(panelRt, "Restart", "Restart Run", new Vector2(0f, -304f), () => menuCommands?.StartNewGame());
        optionsButton = CreateMenuButton(panelRt, "Options", "Options", new Vector2(0f, -362f), () => menuCommands?.ShowOptionsMenu(true));
        exitButton = CreateMenuButton(panelRt, "Exit", "Exit", new Vector2(0f, -420f), () => menuCommands?.ExitGame());
        loadButtonText = loadButton.GetComponentInChildren<Text>();
        restartButtonText = restartButton.GetComponentInChildren<Text>();
        menuHintText = CreateText("MenuHint", panelRt, string.Empty, 16, TextAnchor.MiddleCenter, new Vector2(0f, -476f), new Vector2(340f, 24f));
        menuHintText.color = new Color(0.8f, 0.86f, 0.92f, 0.95f);
    }

    private void BuildOptions()
    {
        var panel = CreatePanel("OptionsPanel", root, Vector2.zero, new Vector2(1260f, 820f), new Color(0.03f, 0.05f, 0.08f, 0.95f), new Vector2(0.5f, 0.5f), new Vector2(0.5f, 0.5f));
        optionsPanel = panel.gameObject;
        optionsPanel.SetActive(false);
        CreateText("OptionsTitle", panel, "Options", 34, TextAnchor.UpperCenter, new Vector2(0f, -18f), new Vector2(280f, 40f));

        var left = CreatePanel("OptionsLeft", panel, new Vector2(28f, -80f), new Vector2(540f, 660f), new Color(0.12f, 0.14f, 0.18f, 0.55f), new Vector2(0f, 1f), new Vector2(0f, 1f));
        var right = CreatePanel("OptionsRight", panel, new Vector2(-28f, -80f), new Vector2(620f, 660f), new Color(0.12f, 0.14f, 0.18f, 0.55f), new Vector2(1f, 1f), new Vector2(1f, 1f));

        CreateTopLeftText("GraphicsHeader", left, "Graphics / Audio", 26, TextAnchor.UpperLeft, new Vector2(18f, -16f), new Vector2(240f, 28f));
        CreateSliderRow(left, "fov", "Field of View", 75f, 55f, 110f, new Vector2(18f, -72f), value =>
        {
            var options = CloneCurrentOptions();
            options.fieldOfView = value;
            optionsController?.ApplyOptions(options);
        });
        CreateSliderRow(left, "sensitivity", "Look Sensitivity", 2f, 0.4f, 5f, new Vector2(18f, -162f), value =>
        {
            var options = CloneCurrentOptions();
            options.lookSensitivity = value;
            optionsController?.ApplyOptions(options);
        });
        CreateSliderRow(left, "master", "Master Volume", 100f, 0f, 100f, new Vector2(18f, -252f), value =>
        {
            var options = CloneCurrentOptions();
            options.masterVolume = value / 100f;
            optionsController?.ApplyOptions(options);
        });
        CreateSliderRow(left, "music", "Music Volume", 65f, 0f, 100f, new Vector2(18f, -342f), value =>
        {
            var options = CloneCurrentOptions();
            options.musicVolume = value / 100f;
            optionsController?.ApplyOptions(options);
        });
        CreateSliderRow(left, "sfx", "SFX Volume", 85f, 0f, 100f, new Vector2(18f, -432f), value =>
        {
            var options = CloneCurrentOptions();
            options.sfxVolume = value / 100f;
            optionsController?.ApplyOptions(options);
        });

        CreateTopLeftText("QualityLabel", left, "Quality", 20, TextAnchor.MiddleLeft, new Vector2(18f, -544f), new Vector2(140f, 28f));
        qualityButton = CreateTopLeftButton(left, "QualityCycle", string.Empty, new Vector2(178f, -540f), new Vector2(290f, 38f), () =>
        {
            var options = CloneCurrentOptions();
            options.qualityLevel = (options.qualityLevel + 1) % Mathf.Max(1, QualitySettings.names.Length);
            optionsController?.ApplyOptions(options);
            RefreshOptions(inputBindings != null ? inputBindings.CurrentOptions : options);
        });
        qualityButtonText = qualityButton.GetComponentInChildren<Text>();
        CreateTopLeftText("InvertLabel", left, "Invert Y", 20, TextAnchor.MiddleLeft, new Vector2(18f, -598f), new Vector2(120f, 28f));
        invertYToggle = CreateToggle(left, new Vector2(182f, -596f), new Vector2(180f, 32f), "Enabled", value =>
        {
            var options = CloneCurrentOptions();
            options.invertY = value;
            optionsController?.ApplyOptions(options);
        });
        CreateTopLeftButton(left, "ResetDefaults", "Reset Defaults", new Vector2(18f, -646f), new Vector2(220f, 42f), () =>
        {
            var defaults = GameOptionsData.CreateDefault();
            optionsController?.ApplyOptions(defaults);
            RefreshOptions(inputBindings != null ? inputBindings.CurrentOptions : defaults);
            optionsStatusText.text = "Defaults restored";
        });

        CreateTopLeftText("KeyboardHeader", right, "Keyboard Settings", 26, TextAnchor.UpperLeft, new Vector2(18f, -16f), new Vector2(280f, 28f));
        float y = -72f;
        foreach (var action in new[]
                 {
                     GameAction.MoveForward, GameAction.MoveBackward, GameAction.MoveLeft, GameAction.MoveRight,
                     GameAction.Jump, GameAction.Run, GameAction.Interact, GameAction.Inventory, GameAction.Skills, GameAction.Map,
                     GameAction.Pause, GameAction.Flashlight, GameAction.Reload
                 })
        {
            CreateBindingRow(right, action, new Vector2(18f, y));
            y -= 48f;
        }

        optionsStatusText = CreateText("OptionsStatus", panel, string.Empty, 18, TextAnchor.MiddleCenter, new Vector2(0f, -768f), new Vector2(920f, 26f));
        CreateButton(panel, "OptionsBack", "Back", new Vector2(0f, -716f), new Vector2(180f, 44f), () => menuCommands?.ShowOptionsMenu(false));
    }

    private void BuildInventory()
    {
        var panel = CreatePanel("InventoryPanel", root, new Vector2(-28f, -100f), new Vector2(520f, 720f), new Color(0.02f, 0.03f, 0.05f, 0.94f), new Vector2(1f, 1f), new Vector2(1f, 1f));
        inventoryPanel = panel.gameObject;
        inventoryPanel.SetActive(false);
        CreateText("InventoryTitle", panel, "Inventory", 30, TextAnchor.UpperCenter, new Vector2(0f, -18f), new Vector2(260f, 34f));

        float tabX = -182f;
        foreach (var tab in new[] { InventoryTab.Weapons, InventoryTab.Consumables, InventoryTab.Keys, InventoryTab.Utility })
        {
            var button = CreateButton(panel, $"{tab}Tab", tab.ToString(), new Vector2(tabX, -66f), new Vector2(106f, 34f), () => SelectInventoryTab(tab));
            button.GetComponentInChildren<Text>().fontSize = 16;
            inventoryTabButtons[tab] = button;
            tabX += 122f;
        }

        var gridPanel = CreatePanel(
            "InventoryGridPanel",
            panel,
            new Vector2(0f, -104f),
            new Vector2(474f, 500f),
            new Color(0.08f, 0.1f, 0.14f, 0.8f),
            new Vector2(0.5f, 1f),
            new Vector2(0.5f, 1f));
        inventoryGrid = CreateRectTransform("InventoryGrid", gridPanel, new Vector2(0f, 1f), new Vector2(0f, 1f), new Vector2(12f, -12f), new Vector2(450f, 0f));
        inventoryGrid.pivot = new Vector2(0f, 1f);
        var layout = inventoryGrid.gameObject.AddComponent<GridLayoutGroup>();
        layout.cellSize = new Vector2(142f, 142f);
        layout.spacing = new Vector2(12f, 12f);
        layout.startCorner = GridLayoutGroup.Corner.UpperLeft;
        layout.constraint = GridLayoutGroup.Constraint.FixedColumnCount;
        layout.constraintCount = 3;
        layout.childAlignment = TextAnchor.UpperLeft;
        layout.padding = new RectOffset(0, 0, 0, 0);
        var fitter = inventoryGrid.gameObject.AddComponent<ContentSizeFitter>();
        fitter.verticalFit = ContentSizeFitter.FitMode.PreferredSize;

        inventoryDetailText = CreateText("InventoryDetail", panel, string.Empty, 17, TextAnchor.UpperLeft, new Vector2(0f, -628f), new Vector2(460f, 62f));
        inventoryDetailText.horizontalOverflow = HorizontalWrapMode.Wrap;
        inventoryDetailText.verticalOverflow = VerticalWrapMode.Overflow;
    }

    private void BuildSkills()
    {
        var panel = CreatePanel("SkillsPanel", root, Vector2.zero, new Vector2(860f, 720f), new Color(0.04f, 0.05f, 0.08f, 0.95f), new Vector2(0.5f, 0.5f), new Vector2(0.5f, 0.5f));
        skillsPanel = panel.gameObject;
        skillsPanel.SetActive(false);
        CreateText("SkillsTitle", panel, "Skill Tree", 32, TextAnchor.UpperCenter, new Vector2(0f, -18f), new Vector2(260f, 34f));
        skillPointsText = CreateText("SkillPoints", panel, "Skill Points: 0", 20, TextAnchor.UpperCenter, new Vector2(0f, -60f), new Vector2(260f, 24f));

        var gridPanel = CreatePanel("SkillsGridPanel", panel, new Vector2(0f, -98f), new Vector2(780f, 480f), new Color(0.1f, 0.12f, 0.16f, 0.85f), new Vector2(0.5f, 1f), new Vector2(0.5f, 1f));
        skillsGrid = CreateRectTransform("SkillsGrid", gridPanel, new Vector2(0f, 1f), new Vector2(0f, 1f), new Vector2(14f, -14f), new Vector2(752f, 0f));
        skillsGrid.pivot = new Vector2(0f, 1f);
        var layout = skillsGrid.gameObject.AddComponent<GridLayoutGroup>();
        layout.cellSize = new Vector2(240f, 140f);
        layout.spacing = new Vector2(12f, 12f);
        layout.constraint = GridLayoutGroup.Constraint.FixedColumnCount;
        layout.constraintCount = 3;
        layout.childAlignment = TextAnchor.UpperLeft;
        layout.padding = new RectOffset(0, 0, 0, 0);
        var fitter = skillsGrid.gameObject.AddComponent<ContentSizeFitter>();
        fitter.verticalFit = ContentSizeFitter.FitMode.PreferredSize;

        skillDetailText = CreateText("SkillDetail", panel, string.Empty, 18, TextAnchor.UpperLeft, new Vector2(0f, -618f), new Vector2(760f, 44f));
        skillDetailText.horizontalOverflow = HorizontalWrapMode.Wrap;
        skillDetailText.verticalOverflow = VerticalWrapMode.Overflow;
    }

    private void BuildMap()
    {
        var panel = CreatePanel("MapPanel", root, Vector2.zero, new Vector2(1540f, 900f), new Color(0f, 0f, 0f, 0.8f), new Vector2(0.5f, 0.5f), new Vector2(0.5f, 0.5f));
        mapPanel = panel.gameObject;
        mapPanel.SetActive(false);
        CreateText("MapTitle", panel, "Sector Map", 30, TextAnchor.UpperCenter, new Vector2(0f, -20f), new Vector2(260f, 32f));
        var imageRt = CreateRectTransform("MapImage", panel, new Vector2(0.5f, 0.5f), new Vector2(0.5f, 0.5f), new Vector2(0f, -10f), new Vector2(1300f, 760f));
        mapImage = imageRt.gameObject.AddComponent<RawImage>();
        mapImage.color = Color.white;
        mapHintText = CreateText("MapHint", panel, string.Empty, 18, TextAnchor.MiddleCenter, new Vector2(0f, -842f), new Vector2(520f, 24f));
        mapHintText.color = new Color(0.86f, 0.9f, 0.96f, 0.95f);
    }

    private void CreateBindingRow(RectTransform parent, GameAction action, Vector2 anchoredPos)
    {
        CreateTopLeftText($"{action}Label", parent, action.ToDisplayName(), 19, TextAnchor.MiddleLeft, anchoredPos, new Vector2(250f, 32f));
        var button = CreateTopLeftButton(parent, $"{action}Button", string.Empty, new Vector2(336f, anchoredPos.y - 2f), new Vector2(238f, 36f), () =>
        {
            pendingRebindAction = action;
            optionsStatusText.text = $"Press a key for {action.ToDisplayName()}";
        });
        bindingButtons[action] = button;
        bindingButtonTexts[action] = button.GetComponentInChildren<Text>();
    }

    private void CreateSliderRow(RectTransform parent, string key, string label, float initialValue, float min, float max, Vector2 anchoredPos, Action<float> onChanged)
    {
        CreateTopLeftText($"{key}Label", parent, label, 18, TextAnchor.UpperLeft, anchoredPos, new Vector2(220f, 24f));
        var slider = CreateSlider(key, parent, new Vector2(16f, anchoredPos.y - 34f), new Vector2(382f, 28f), new Color(0.3f, 0.65f, 0.9f));
        slider.minValue = min;
        slider.maxValue = max;
        slider.value = initialValue;
        slider.onValueChanged.AddListener(value =>
        {
            sliderValues[key].text = value.ToString(key == "sensitivity" ? "0.0" : "0");
            onChanged(value);
        });
        sliders[key] = slider;
        sliderValues[key] = CreateTopLeftText($"{key}Value", parent, initialValue.ToString(key == "sensitivity" ? "0.0" : "0"), 18, TextAnchor.MiddleRight, new Vector2(420f, anchoredPos.y - 30f), new Vector2(86f, 28f));
    }

    private void SetSliderValue(string key, float value, string format)
    {
        if (!sliders.TryGetValue(key, out var slider) || !sliderValues.TryGetValue(key, out var valueText))
        {
            return;
        }

        slider.SetValueWithoutNotify(value);
        valueText.text = value.ToString(format);
    }

    private Button CreateMenuButton(RectTransform parent, string name, string label, Vector2 anchoredPos, UnityEngine.Events.UnityAction action)
    {
        return CreateButton(parent, name, label, anchoredPos, new Vector2(280f, 44f), action);
    }

    private Button CreateTopLeftButton(RectTransform parent, string name, string label, Vector2 anchoredPos, Vector2 size, UnityEngine.Events.UnityAction action)
    {
        var rt = CreateRectTransform(name, parent, new Vector2(0f, 1f), new Vector2(0f, 1f), anchoredPos, size);
        rt.pivot = new Vector2(0f, 1f);
        var image = rt.gameObject.AddComponent<Image>();
        image.color = new Color(0.2f, 0.26f, 0.33f, 0.95f);
        var button = rt.gameObject.AddComponent<Button>();
        button.targetGraphic = image;
        button.onClick.AddListener(action);
        var labelText = CreateCenteredText($"{name}Label", rt, label, 20, TextAnchor.MiddleCenter, Vector2.zero, size);
        labelText.color = Color.white;
        return button;
    }

    private Text CreateTopLeftText(string name, RectTransform parent, string content, int fontSize, TextAnchor anchor, Vector2 anchoredPos, Vector2 size)
    {
        var rt = CreateRectTransform(name, parent, new Vector2(0f, 1f), new Vector2(0f, 1f), anchoredPos, size);
        rt.pivot = new Vector2(0f, 1f);
        var text = rt.gameObject.AddComponent<Text>();
        text.font = uiFont;
        text.fontSize = fontSize;
        text.alignment = anchor;
        text.horizontalOverflow = HorizontalWrapMode.Overflow;
        text.verticalOverflow = VerticalWrapMode.Overflow;
        text.color = Color.white;
        text.text = content;
        return text;
    }

    private RectTransform CreateInventoryCard(RectTransform parent, InventoryEntryData entry)
    {
        var card = CreateRectTransform($"{entry.Name}_Card", parent, new Vector2(0f, 1f), new Vector2(0f, 1f), Vector2.zero, new Vector2(142f, 142f));
        var cardImage = card.gameObject.AddComponent<Image>();
        cardImage.color = new Color(0.12f, 0.15f, 0.19f, 0.95f);

        var icon = CreateRectTransform("Icon", card, new Vector2(0f, 1f), new Vector2(0f, 1f), new Vector2(12f, -12f), new Vector2(46f, 46f));
        var iconImage = icon.gameObject.AddComponent<Image>();
        iconImage.color = entry.IconColor;

        var countBadge = CreateRectTransform("Count", card, new Vector2(1f, 1f), new Vector2(1f, 1f), new Vector2(-12f, -12f), new Vector2(34f, 22f));
        var countBg = countBadge.gameObject.AddComponent<Image>();
        countBg.color = new Color(0.03f, 0.04f, 0.06f, 0.95f);
        var countText = CreateCenteredText("CountText", countBadge, entry.Count.ToString(), 15, TextAnchor.MiddleCenter, Vector2.zero, new Vector2(34f, 22f));
        countText.color = Color.white;

        var name = CreateText("Name", card, entry.Name, 16, TextAnchor.UpperLeft, new Vector2(12f, -68f), new Vector2(118f, 34f));
        name.horizontalOverflow = HorizontalWrapMode.Wrap;
        name.verticalOverflow = VerticalWrapMode.Overflow;

        var detail = CreateText("Detail", card, entry.Detail, 13, TextAnchor.UpperLeft, new Vector2(12f, -106f), new Vector2(118f, 30f));
        detail.color = new Color(0.76f, 0.82f, 0.92f, 0.92f);
        detail.horizontalOverflow = HorizontalWrapMode.Wrap;
        detail.verticalOverflow = VerticalWrapMode.Overflow;
        return card;
    }

    private RectTransform CreateSkillCard(RectTransform parent, SkillEntryViewData entry)
    {
        var card = CreateRectTransform($"{entry.Id}_SkillCard", parent, new Vector2(0f, 1f), new Vector2(0f, 1f), Vector2.zero, new Vector2(240f, 140f));
        var buttonImage = card.gameObject.AddComponent<Image>();
        buttonImage.color = entry.Unlocked
            ? new Color(0.16f, 0.34f, 0.2f, 0.96f)
            : (entry.Available ? new Color(0.12f, 0.18f, 0.24f, 0.96f) : new Color(0.1f, 0.1f, 0.12f, 0.96f));
        var button = card.gameObject.AddComponent<Button>();
        button.targetGraphic = buttonImage;
        button.interactable = entry.Available;
        button.onClick.AddListener(() =>
        {
            if (skillDetailText != null)
            {
                skillDetailText.text = entry.Description;
            }
            skillCommands?.TryUnlockSkill(entry.Id);
        });

        var accent = CreateRectTransform("Accent", card, new Vector2(0f, 1f), new Vector2(1f, 1f), Vector2.zero, new Vector2(0f, 8f));
        accent.offsetMin = new Vector2(0f, -8f);
        accent.offsetMax = new Vector2(0f, 0f);
        var accentImage = accent.gameObject.AddComponent<Image>();
        accentImage.color = entry.ThemeColor;

        var title = CreateTopLeftText("Title", card, entry.DisplayName, 18, TextAnchor.UpperLeft, new Vector2(12f, -18f), new Vector2(146f, 24f));
        title.horizontalOverflow = HorizontalWrapMode.Wrap;
        title.verticalOverflow = VerticalWrapMode.Overflow;
        var cost = CreateTopLeftText("Cost", card, entry.Unlocked ? "Unlocked" : $"Cost {entry.Cost}", 15, TextAnchor.UpperRight, new Vector2(112f, -18f), new Vector2(116f, 20f));
        cost.color = entry.Unlocked ? new Color(0.7f, 1f, 0.7f, 1f) : new Color(1f, 0.9f, 0.62f, 1f);
        var desc = CreateTopLeftText("Desc", card, entry.Description, 14, TextAnchor.UpperLeft, new Vector2(12f, -52f), new Vector2(214f, 54f));
        desc.horizontalOverflow = HorizontalWrapMode.Wrap;
        desc.verticalOverflow = VerticalWrapMode.Overflow;
        desc.color = new Color(0.82f, 0.88f, 0.95f, 0.96f);
        var state = CreateTopLeftText("State", card, entry.Unlocked ? "Active" : (entry.Available ? "Click to unlock" : "Locked"), 14, TextAnchor.UpperLeft, new Vector2(12f, -116f), new Vector2(214f, 18f));
        state.color = entry.Unlocked ? new Color(0.72f, 1f, 0.72f, 1f) : (entry.Available ? new Color(0.88f, 0.94f, 1f, 1f) : new Color(0.7f, 0.72f, 0.76f, 1f));
        return card;
    }

    private Button CreateButton(RectTransform parent, string name, string label, Vector2 anchoredPos, Vector2 size, UnityEngine.Events.UnityAction action)
    {
        var rt = CreateRectTransform(name, parent, new Vector2(0.5f, 1f), new Vector2(0.5f, 1f), anchoredPos, size);
        var image = rt.gameObject.AddComponent<Image>();
        image.color = new Color(0.2f, 0.26f, 0.33f, 0.95f);
        var button = rt.gameObject.AddComponent<Button>();
        button.targetGraphic = image;
        button.onClick.AddListener(action);
        var labelText = CreateCenteredText($"{name}Label", rt, label, 20, TextAnchor.MiddleCenter, Vector2.zero, size);
        labelText.color = Color.white;
        return button;
    }

    private Slider CreateSlider(string name, RectTransform parent, Vector2 anchoredPos, Vector2 size, Color fillColor)
    {
        var rt = CreateRectTransform(name, parent, new Vector2(0f, 1f), new Vector2(0f, 1f), anchoredPos, size);
        var slider = rt.gameObject.AddComponent<Slider>();

        var background = CreateRectTransform("Background", rt, new Vector2(0f, 0.5f), new Vector2(1f, 0.5f), Vector2.zero, size);
        var backgroundImage = background.gameObject.AddComponent<Image>();
        backgroundImage.color = new Color(0.12f, 0.13f, 0.16f, 0.95f);

        var fillArea = CreateRectTransform("FillArea", rt, new Vector2(0f, 0f), new Vector2(1f, 1f), Vector2.zero, new Vector2(-18f, 0f));
        fillArea.offsetMin = new Vector2(5f, 5f);
        fillArea.offsetMax = new Vector2(-13f, -5f);
        var fill = CreateRectTransform("Fill", fillArea, new Vector2(0f, 0f), new Vector2(1f, 1f), Vector2.zero, Vector2.zero);
        var fillImage = fill.gameObject.AddComponent<Image>();
        fillImage.color = fillColor;

        var handleArea = CreateRectTransform("HandleArea", rt, new Vector2(0f, 0f), new Vector2(1f, 1f), Vector2.zero, Vector2.zero);
        handleArea.offsetMin = new Vector2(10f, 0f);
        handleArea.offsetMax = new Vector2(-10f, 0f);
        var handle = CreateRectTransform("Handle", handleArea, new Vector2(0.5f, 0.5f), new Vector2(0.5f, 0.5f), Vector2.zero, new Vector2(18f, 30f));
        var handleImage = handle.gameObject.AddComponent<Image>();
        handleImage.color = new Color(0.95f, 0.95f, 1f, 0.95f);

        slider.fillRect = fill;
        slider.handleRect = handle;
        slider.targetGraphic = handleImage;
        slider.direction = Slider.Direction.LeftToRight;
        return slider;
    }

    private Toggle CreateToggle(RectTransform parent, Vector2 anchoredPos, Vector2 size, string label, Action<bool> onChanged)
    {
        var rt = CreateRectTransform("Toggle", parent, new Vector2(0f, 1f), new Vector2(0f, 1f), anchoredPos, size);
        var toggle = rt.gameObject.AddComponent<Toggle>();

        var background = CreateRectTransform("Background", rt, new Vector2(0f, 0.5f), new Vector2(0f, 0.5f), new Vector2(18f, 0f), new Vector2(22f, 22f));
        var bgImage = background.gameObject.AddComponent<Image>();
        bgImage.color = new Color(0.15f, 0.18f, 0.21f, 1f);
        var checkmark = CreateRectTransform("Checkmark", background, new Vector2(0.5f, 0.5f), new Vector2(0.5f, 0.5f), Vector2.zero, new Vector2(14f, 14f));
        var checkImage = checkmark.gameObject.AddComponent<Image>();
        checkImage.color = new Color(0.2f, 0.9f, 0.3f, 1f);
        toggle.graphic = checkImage;
        toggle.targetGraphic = bgImage;
        CreateText("Label", rt, label, 18, TextAnchor.MiddleLeft, new Vector2(54f, 0f), new Vector2(90f, 24f));
        toggle.onValueChanged.AddListener(value => onChanged(value));
        return toggle;
    }

    private GameOptionsData CloneCurrentOptions()
    {
        var current = inputBindings != null ? inputBindings.CurrentOptions : null;
        if (current == null)
        {
            return GameOptionsData.CreateDefault();
        }

        return new GameOptionsData
        {
            fieldOfView = current.fieldOfView,
            lookSensitivity = current.lookSensitivity,
            masterVolume = current.masterVolume,
            musicVolume = current.musicVolume,
            sfxVolume = current.sfxVolume,
            qualityLevel = current.qualityLevel,
            invertY = current.invertY,
            moveForward = current.moveForward,
            moveBackward = current.moveBackward,
            moveLeft = current.moveLeft,
            moveRight = current.moveRight,
            jump = current.jump,
            run = current.run,
            interact = current.interact,
            inventory = current.inventory,
            skills = current.skills,
            map = current.map,
            pause = current.pause,
            flashlight = current.flashlight,
            reload = current.reload
        };
    }

    private static T ResolveInterface<T>(MonoBehaviour behaviour) where T : class
    {
        if (behaviour == null)
        {
            return null;
        }

        return behaviour.GetComponents<MonoBehaviour>().OfType<T>().FirstOrDefault();
    }

    private RectTransform CreatePanel(string name, RectTransform parent, Vector2 anchoredPos, Vector2 size, Color color, Vector2 anchorMin, Vector2 anchorMax)
    {
        var rt = CreateRectTransform(name, parent, anchorMin, anchorMax, anchoredPos, size);
        var image = rt.gameObject.AddComponent<Image>();
        image.color = color;
        return rt;
    }

    private Text CreateText(string name, RectTransform parent, string content, int fontSize, TextAnchor anchor, Vector2 anchoredPos, Vector2 size)
    {
        var rt = CreateRectTransform(name, parent, new Vector2(0.5f, 1f), new Vector2(0.5f, 1f), anchoredPos, size);
        var text = rt.gameObject.AddComponent<Text>();
        text.font = uiFont;
        text.fontSize = fontSize;
        text.alignment = anchor;
        text.horizontalOverflow = HorizontalWrapMode.Overflow;
        text.verticalOverflow = VerticalWrapMode.Overflow;
        text.color = Color.white;
        text.text = content;
        return text;
    }

    private Text CreateCenteredText(string name, RectTransform parent, string content, int fontSize, TextAnchor anchor, Vector2 anchoredPos, Vector2 size)
    {
        var rt = CreateRectTransform(name, parent, new Vector2(0.5f, 0.5f), new Vector2(0.5f, 0.5f), anchoredPos, size);
        var text = rt.gameObject.AddComponent<Text>();
        text.font = uiFont;
        text.fontSize = fontSize;
        text.alignment = anchor;
        text.horizontalOverflow = HorizontalWrapMode.Overflow;
        text.verticalOverflow = VerticalWrapMode.Overflow;
        text.color = Color.white;
        text.text = content;
        return text;
    }

    private RectTransform CreateRectTransform(string name, RectTransform parent, Vector2 anchorMin, Vector2 anchorMax, Vector2 anchoredPos, Vector2 size)
    {
        var go = new GameObject(name, typeof(RectTransform));
        go.transform.SetParent(parent, false);
        var rt = go.GetComponent<RectTransform>();
        rt.anchorMin = anchorMin;
        rt.anchorMax = anchorMax;
        rt.pivot = anchorMin == anchorMax ? anchorMin : (anchorMin + anchorMax) * 0.5f;
        rt.anchoredPosition = anchoredPos;
        rt.sizeDelta = size;
        return rt;
    }

    private static void FocusButton(Button button)
    {
        var eventSystem = EventSystem.current;
        if (eventSystem == null || button == null || !button.gameObject.activeInHierarchy)
        {
            return;
        }

        eventSystem.SetSelectedGameObject(null);
        eventSystem.SetSelectedGameObject(button.gameObject);
    }

    private static void ClearSelection()
    {
        var eventSystem = EventSystem.current;
        if (eventSystem == null)
        {
            return;
        }

        eventSystem.SetSelectedGameObject(null);
    }
}
