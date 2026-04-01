using System;

namespace HPR
{
    public enum GameAction
    {
        MoveForward,
        MoveBackward,
        MoveLeft,
        MoveRight,
        Jump,
        Run,
        Interact,
        AbilityPrimary,
        AbilitySecondary,
        Inventory,
        Journal,
        Skills,
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
                GameAction.AbilityPrimary => "Ability Primary",
                GameAction.AbilitySecondary => "Ability Secondary",
                GameAction.Inventory => "Inventory",
                GameAction.Journal => "Quest Journal",
                GameAction.Skills => "Skill Tree",
                GameAction.Map => "Map",
                GameAction.Pause => "Pause Menu",
                GameAction.Flashlight => "Flashlight",
                GameAction.Reload => "Reload",
                _ => action.ToString()
            };
        }
    }
}
