using System;

public enum GameAction
{
    MoveForward,
    MoveBackward,
    MoveLeft,
    MoveRight,
    Jump,
    Run,
    Interact,
    Inventory,
    Map,
    Pause,
    Flashlight,
    Reload
}

public static class GameActionExtensions
{
    public static string ToDisplayName(this GameAction action)
    {
        return action switch
        {
            GameAction.MoveForward => "Move Forward",
            GameAction.MoveBackward => "Move Backward",
            GameAction.MoveLeft => "Move Left",
            GameAction.MoveRight => "Move Right",
            GameAction.Jump => "Jump",
            GameAction.Run => "Run",
            GameAction.Interact => "Interact",
            GameAction.Inventory => "Inventory",
            GameAction.Map => "Map",
            GameAction.Pause => "Pause Menu",
            GameAction.Flashlight => "Flashlight",
            GameAction.Reload => "Reload",
            _ => action.ToString()
        };
    }
}
