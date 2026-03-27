using System.Linq;
using UnityEngine;

[DefaultExecutionOrder(-1000)]
public sealed class FpsDemoCompositionRoot : MonoBehaviour
{
    [SerializeField] private GameManager gameManager;
    [SerializeField] private EventManager eventManager;
    [SerializeField] private GameStateValidator stateValidator;
    [SerializeField] private QuestManager questManager;
    [SerializeField] private GameUiController uiController;
    [SerializeField] private FpsDemoServiceAdapter serviceAdapter;
    [SerializeField] private PlayerActorContext player;
    [SerializeField] private Camera mapCamera;
    [SerializeField] private Transform saveableRoot;

    private CompositionRoot compositionRoot;

    public void ConfigureSceneReferences(GameManager manager, EventManager events, GameStateValidator validator, QuestManager quests, GameUiController ui, FpsDemoServiceAdapter adapter, PlayerActorContext actor, Camera overheadMapCamera, Transform worldRoot)
    {
        gameManager = manager;
        eventManager = events;
        stateValidator = validator;
        questManager = quests;
        uiController = ui;
        serviceAdapter = adapter;
        player = actor;
        mapCamera = overheadMapCamera;
        saveableRoot = worldRoot;
    }

    private void Awake()
    {
        EnsureReferences();
        gameManager?.ConfigureSceneReferences(eventManager, stateValidator, questManager, player, mapCamera, uiController, saveableRoot);
        compositionRoot = new CompositionRoot();
        RegisterServices(compositionRoot.Services);
        serviceAdapter?.Configure(compositionRoot.Services);
        compositionRoot.Initialize();
        BindSceneObjects();
    }

    private void OnDestroy()
    {
        compositionRoot?.Dispose();
    }

    private void EnsureReferences()
    {
        gameManager ??= GetComponent<GameManager>();
        eventManager ??= GetComponent<EventManager>();
        stateValidator ??= GetComponent<GameStateValidator>();
        questManager ??= GetComponent<QuestManager>();
        uiController ??= GetComponent<GameUiController>();
        serviceAdapter ??= GetComponent<FpsDemoServiceAdapter>();
    }

    private void RegisterServices(ServiceRegistry services)
    {
        if (eventManager?.EventBus != null)
        {
            services.Register<IEventBus>(eventManager.EventBus);
        }

        if (gameManager != null)
        {
            services.Register<IInputBindingsSource>(gameManager);
            services.Register<IOptionsController>(gameManager);
            services.Register<IGameplayStateSource>(gameManager);
            services.Register<IStatusMessageSink>(gameManager);
            services.Register<IInteractionPromptSink>(gameManager);
            services.Register<IHudRefreshSink>(gameManager);
            services.Register<IThreatScanner>(gameManager);
            services.Register<IGameplayFlowCommands>(gameManager);
            services.Register<IGameMenuCommands>(gameManager);
            services.Register<IPlayerDeathHandler>(gameManager);
            services.Register<IPlayerActorSource>(gameManager);
            services.Register<IEnemyRegistry>(gameManager);
            services.Register<ISkillTreeCommands>(gameManager);
            services.Register<IQuestJournalSource>(gameManager);
            services.Register<IDialogueFlowCommands>(gameManager);
            services.Register<ISkillPointRewardSink>(gameManager);
            services.Register<IQuestStateQuery>(gameManager);
            services.Register<IInventoryItemUseCommands>(gameManager);
        }

        if (player != null)
        {
            services.Register<IPlayerActor>(player);
        }
    }

    private void BindSceneObjects()
    {
        if (serviceAdapter == null)
        {
            return;
        }

        uiController?.Initialize(serviceAdapter, gameManager != null ? gameManager.MapTexture : null);
        stateValidator?.Bind(eventManager != null ? eventManager.EventBus : null);
        player?.BindRuntimeServices(serviceAdapter);
        questManager?.BindRuntimeServices(serviceAdapter);

        if (saveableRoot == null)
        {
            return;
        }

        foreach (PickupItem pickup in saveableRoot.GetComponentsInChildren<PickupItem>(true))
        {
            pickup?.BindRuntimeServices(serviceAdapter);
        }

        foreach (DoorController door in saveableRoot.GetComponentsInChildren<DoorController>(true))
        {
            door?.BindRuntimeServices(serviceAdapter);
        }

        foreach (EnemyAgent enemy in saveableRoot.GetComponentsInChildren<EnemyAgent>(true))
        {
            enemy?.BindRuntimeServices(serviceAdapter);
        }

        foreach (DialogueNpcInteractable npc in saveableRoot.GetComponentsInChildren<DialogueNpcInteractable>(true))
        {
            npc?.BindRuntimeServices(serviceAdapter);
        }
    }
}
