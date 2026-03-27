using System.Linq;
using UnityEngine;

public class DialogueNpcInteractable : MonoBehaviour, IInteractable
{
    [SerializeField] private string npcId;
    [SerializeField] private string displayName = "Operator";
    [SerializeField] private DialogueData dialogueData;
    [SerializeField] private MonoBehaviour servicesBehaviour;

    private IDialogueFlowCommands dialogueCommands;
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
        if (dialogueData == null)
        {
            statusSink?.NotifyStatus($"{displayName} has nothing to say");
            return;
        }

        if (!(dialogueCommands?.StartDialogue(npcId, displayName, dialogueData) ?? false))
        {
            statusSink?.NotifyStatus($"{displayName} is unavailable");
        }
    }

    private void ResolveServices()
    {
        dialogueCommands = servicesBehaviour as IDialogueFlowCommands;
        statusSink = servicesBehaviour as IStatusMessageSink;
    }
}
