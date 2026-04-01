using System;
using System.Collections.Generic;
using UnityEngine;

namespace HPR
{
    public enum QuestObjectiveType
    {
        KillEnemy,
        CollectItem,
        TalkToNpc
    }

    [Serializable]
    public class QuestObjectiveData
    {
        public string Id;
        public QuestObjectiveType ObjectiveType;
        public string TargetId;
        [TextArea(1, 3)] public string Description;
        public int RequiredCount = 1;
    }

    [Serializable]
    public class QuestObjectiveProgressViewData
    {
        public string Description;
        public int CurrentCount;
        public int RequiredCount;
        public bool Completed;
    }

    [Serializable]
    public class QuestJournalEntryViewData
    {
        public string Id;
        public string Title;
        public string Description;
        public bool Active;
        public bool Completed;
        public Color ThemeColor;
        public List<QuestObjectiveProgressViewData> Objectives = new();
    }

    [CreateAssetMenu(menuName = "HPR/FPS Demo/Quest", fileName = "QuestData")]
    public class QuestData : ScriptableObject
    {
        public string Id;
        public string Title;
        [TextArea(2, 6)] public string Description;
        public bool StartOnSession;
        public int RewardSkillPoints;
        public ItemData RewardItem;
        public int RewardItemAmount = 1;
        public Color ThemeColor = new Color(0.86f, 0.74f, 0.3f, 1f);
        public List<QuestObjectiveData> Objectives = new();
    }
}
