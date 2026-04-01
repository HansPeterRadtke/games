#nullable enable
using NUnit.Framework;
using UnityEngine;

namespace HPR
{
    public class InteractionEditModeTests
    {
        [Test]
        public void InteractionTargetProxy_ReturnsExplicitBinding()
        {
            var go = new GameObject("Proxy");
            try
            {
                var interactable = go.AddComponent<TestInteractable>();
                var proxy = go.AddComponent<InteractionTargetProxy>();
                proxy.Bind(interactable);

                Assert.That(proxy.Resolve(), Is.SameAs(interactable));
            }
            finally
            {
                Object.DestroyImmediate(go);
            }
        }

        [Test]
        public void KeyDoorInteractable_StaysClosedWithoutRequiredKey()
        {
            var door = new GameObject("Door");
            var key = ScriptableObject.CreateInstance<ItemData>();
            try
            {
                key.Id = "door.key";
                key.DisplayName = "Door Key";

                var interactable = door.AddComponent<KeyDoorInteractable>();
                typeof(KeyDoorInteractable).GetField("requiredKeyItem", System.Reflection.BindingFlags.NonPublic | System.Reflection.BindingFlags.Instance)!.SetValue(interactable, key);

                interactable.Interact(null);

                Assert.That(interactable.IsOpen, Is.False);
            }
            finally
            {
                Object.DestroyImmediate(key);
                Object.DestroyImmediate(door);
            }
        }

        private sealed class TestInteractable : MonoBehaviour, IInteractable
        {
            public InteractionType InteractionType => InteractionType.Activate;
            public string GetPrompt(IInteractionActor actor) => "Prompt";
            public void Interact(IInteractionActor actor) { }
        }
    }
}
