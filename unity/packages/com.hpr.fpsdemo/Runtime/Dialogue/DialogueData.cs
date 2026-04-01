using System;
using System.Collections.Generic;
using System.Linq;
using UnityEngine;

namespace HPR
{
    [Serializable]
    public class DialogueChoiceData
    {
        public string Id;
        public string Text;
        public string NextNodeId;
        public bool ExitAfterChoice;
        public string StartQuestId;
        public string StatusMessage;
    }

    [Serializable]
    public class DialogueNodeData
    {
        public string Id;
        public string SpeakerName;
        [TextArea(2, 6)] public string Text;
        public List<DialogueChoiceData> Choices = new();
    }

    [Serializable]
    public class DialogueChoiceViewData
    {
        public string Id;
        public string Label;
    }

    [Serializable]
    public class DialogueViewData
    {
        public string DialogueId;
        public string NpcId;
        public string SpeakerName;
        public string Body;
        public List<DialogueChoiceViewData> Choices = new();
    }

    [CreateAssetMenu(menuName = "HPR/FPS Demo/Dialogue", fileName = "DialogueData")]
    public class DialogueData : ScriptableObject
    {
        public string Id;
        public string DisplayName;
        public string StartNodeId;
        public List<DialogueNodeData> Nodes = new();

        public DialogueNodeData ResolveStartNode()
        {
            string startId = !string.IsNullOrWhiteSpace(StartNodeId) ? StartNodeId : Nodes?.FirstOrDefault()?.Id;
            return GetNode(startId);
        }

        public DialogueNodeData GetNode(string nodeId)
        {
            if (string.IsNullOrWhiteSpace(nodeId))
            {
                return null;
            }

            return Nodes?.FirstOrDefault(node => node != null && string.Equals(node.Id, nodeId, StringComparison.Ordinal));
        }
    }
}
