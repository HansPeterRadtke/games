using UnityEngine;

public interface IGameplayStateSource
{
    bool AllowsGameplayInput { get; }
    bool IsGameplayRunning { get; }
    bool IsMapVisible { get; }
    bool IsInventoryVisible { get; }
    bool IsSkillsVisible { get; }
    bool IsPauseVisible { get; }
    bool IsOptionsVisible { get; }
    bool IsRebindingKey { get; }
    bool IsCombatLive { get; }
}

public interface IStatusMessageSink
{
    void NotifyStatus(string message);
}

public interface IInteractionPromptSink
{
    void SetInteractionPrompt(string prompt);
}

public interface IHudRefreshSink
{
    void RefreshHud();
}

public interface IThreatScanner
{
    string DescribeNearbyThreats(Vector3 position);
}

public interface IGameplayFlowCommands
{
    void MarkCombatReady();
    void TogglePauseMenu();
    void ToggleInventory();
    void ToggleSkills();
    void ToggleMap();
    void ShowOptionsMenu(bool visible);
}

public interface IPlayerDeathHandler
{
    void HandlePlayerDeath();
}

public interface IGameMenuCommands
{
    bool HasSaveGame { get; }
    void ActivatePrimaryMenuAction();
    void ResumeSession();
    void SaveGame();
    void LoadGame();
    void StartNewGame();
    void ExitGame();
    void ShowOptionsMenu(bool visible);
}
