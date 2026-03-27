using System.Linq;
using System.Collections.Generic;
using UnityEngine;

public class DialogueNpcInteractable : MonoBehaviour, IInteractable
{
    [System.Serializable]
    public class DialogueVariantRule
    {
        public string Label;
        public DialogueData Dialogue;
        public string RequiredActiveQuestId;
        public string RequiredCompletedQuestId;
        public string RequiredObjectiveQuestId;
        public string RequiredObjectiveId;
        public int Priority;

        public bool Matches(IQuestStateQuery questState)
        {
            if (Dialogue == null)
            {
                return false;
            }

            if (!string.IsNullOrWhiteSpace(RequiredActiveQuestId) && !(questState?.IsQuestActive(RequiredActiveQuestId) ?? false))
            {
                return false;
            }

            if (!string.IsNullOrWhiteSpace(RequiredCompletedQuestId) && !(questState?.IsQuestCompleted(RequiredCompletedQuestId) ?? false))
            {
                return false;
            }

            if (!string.IsNullOrWhiteSpace(RequiredObjectiveQuestId) || !string.IsNullOrWhiteSpace(RequiredObjectiveId))
            {
                if (questState == null || !questState.IsObjectiveComplete(RequiredObjectiveQuestId, RequiredObjectiveId))
                {
                    return false;
                }
            }

            return true;
        }
    }

    [SerializeField] private string npcId;
    [SerializeField] private string displayName = "Operator";
    [SerializeField] private DialogueData dialogueData;
    [SerializeField] private List<DialogueVariantRule> dialogueVariants = new();
    [SerializeField] private MonoBehaviour servicesBehaviour;

    private IDialogueFlowCommands dialogueCommands;
    private IQuestStateQuery questStateQuery;
    private IStatusMessageSink statusSink;

    public string NpcId => npcId;
    public string DisplayName => displayName;
    public DialogueData Dialogue => dialogueData;
    public InteractionType InteractionType => InteractionType.Talk;

    private void Awake()
    {
        servicesBehaviour = servicesBehaviour != null ? servicesBehaviour : GetComponentsInParent<MonoBehaviour>(true).FirstOrDefault(component =>
            component is IDialogueFlowCommands || component is IStatusMessageSink);
        ResolveServices();
    }

    public void Configure(string id, string npcDisplayName, DialogueData data)
    {
        npcId = id;
        displayName = npcDisplayName;
        dialogueData = data;
    }

    public void ConfigureVariants(IEnumerable<DialogueVariantRule> variants)
    {
        dialogueVariants = variants?.Where(variant => variant != null && variant.Dialogue != null)
            .OrderByDescending(variant => variant.Priority)
            .ToList() ?? new List<DialogueVariantRule>();
    }

    public void BindRuntimeServices(MonoBehaviour services)
    {
        servicesBehaviour = services;
        ResolveServices();
    }

    public string GetPrompt(IInteractionActor actor)
    {
        return $"Talk to {displayName} [E]";
    }

    public void Interact(IInteractionActor actor)
    {
        DialogueData resolvedDialogue = ResolveDialogue();
        if (resolvedDialogue == null)
        {
            statusSink?.NotifyStatus($"{displayName} has nothing to say");
            return;
        }

        if (!(dialogueCommands?.StartDialogue(npcId, displayName, resolvedDialogue) ?? false))
        {
            statusSink?.NotifyStatus($"{displayName} is unavailable");
        }
    }

    private void ResolveServices()
    {
        dialogueCommands = servicesBehaviour as IDialogueFlowCommands;
        questStateQuery = servicesBehaviour as IQuestStateQuery;
        statusSink = servicesBehaviour as IStatusMessageSink;
    }

    private DialogueData ResolveDialogue()
    {
        foreach (DialogueVariantRule variant in dialogueVariants.OrderByDescending(candidate => candidate.Priority))
        {
            if (variant != null && variant.Matches(questStateQuery))
            {
                return variant.Dialogue;
            }
        }

        return dialogueData;
    }
}
