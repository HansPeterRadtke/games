// Isolated QA prototype, NOT included in the public or current HPR buyer archive.
// Purpose: show that a customer can attach one ability to an EXISTING player
// using visible Editor controls, validation, Undo and no source-code rewriting.
// Does not modify any user file on import, on inspector redraw or on preview.
#if UNITY_EDITOR
using System;
using System.Linq;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEditor.UIElements;
using UnityEngine;
using UnityEngine.UIElements;
using HPR;

namespace HPR.GameplaySuite.Experimental
{
    public sealed class HprSelectedAbilityInstaller : EditorWindow
    {
        private GameObject target;
        private AbilityData ability;
        private MonoBehaviour provider;
        private ObjectField selectedObjectField;
        private ObjectField abilityField;
        private ObjectField providerField;
        private Button attachButton;
        private Button removeButton;
        private HelpBox readiness;

        [MenuItem("Tools/HPR/Gameplay Suite/Attach Ability to Selected Object")]
        public static void Open()
        {
            var window = GetWindow<HprSelectedAbilityInstaller>();
            window.titleContent = new GUIContent("HPR Ability Installer");
            window.minSize = new Vector2(370f, 280f);
            window.Show();
        }

        private void OnEnable()
        {
            Selection.selectionChanged += RefreshFromSelection;
            EditorApplication.projectChanged += Refresh;
        }

        private void OnDisable()
        {
            Selection.selectionChanged -= RefreshFromSelection;
            EditorApplication.projectChanged -= Refresh;
        }

        public void CreateGUI()
        {
            rootVisualElement.Clear();
            var scroll = new ScrollView();
            rootVisualElement.Add(scroll);
            scroll.Add(new Label("ADD ONE ABILITY TO YOUR EXISTING GAME"));
            scroll.Add(new Label(
                "Choose your existing player, an independently copied ability, " +
                "and your resource provider. Preview does not change any assets."));
            selectedObjectField = new ObjectField("Selected object")
            {
                objectType = typeof(GameObject),
                allowSceneObjects = true,
                value = Selection.activeGameObject
            };
            abilityField = new ObjectField("Customer-owned ability")
            {
                objectType = typeof(AbilityData),
                allowSceneObjects = false,
                value = Selection.activeObject as AbilityData
            };
            providerField = new ObjectField("Resource provider")
            {
                objectType = typeof(MonoBehaviour),
                allowSceneObjects = true
            };
            scroll.Add(selectedObjectField);
            scroll.Add(abilityField);
            scroll.Add(providerField);
            readiness = new HelpBox("Choose an object and a customer-owned ability.", HelpBoxMessageType.Info);
            scroll.Add(readiness);
            scroll.Add(new Button(Refresh) { text = "Preview: verify without modifying your scene" });
            attachButton = new Button(AttachRequested)
            {
                text = "Attach ability (Undo available; save scene manually)"
            };
            scroll.Add(attachButton);
            removeButton = new Button(RemoveRequested)
            {
                text = "Remove HPR runner (Undo available; save scene manually)"
            };
            scroll.Add(removeButton);

            selectedObjectField.RegisterValueChangedCallback(change =>
            {
                target = change.newValue as GameObject;
                provider = FindProvider(target);
                providerField.SetValueWithoutNotify(provider);
                Refresh();
            });
            abilityField.RegisterValueChangedCallback(change =>
            {
                ability = change.newValue as AbilityData;
                Refresh();
            });
            providerField.RegisterValueChangedCallback(change =>
            {
                provider = change.newValue as MonoBehaviour;
                Refresh();
            });
            target = selectedObjectField.value as GameObject;
            ability = abilityField.value as AbilityData;
            provider = FindProvider(target);
            providerField.SetValueWithoutNotify(provider);
            Refresh();
        }

        private static MonoBehaviour FindProvider(GameObject target)
        {
            return target == null
                ? null
                : target.GetComponents<MonoBehaviour>()
                    .FirstOrDefault(component => component is IAbilityResourcePool);
        }

        private void RefreshFromSelection()
        {
            if (selectedObjectField == null)
                return;
            target = Selection.activeGameObject;
            selectedObjectField.SetValueWithoutNotify(target);
            provider = FindProvider(target);
            providerField.SetValueWithoutNotify(provider);
            Refresh();
        }

        private void Refresh()
        {
            if (readiness == null || attachButton == null || removeButton == null)
                return;
            string error = ValidateSelection(target, ability, provider);
            string removalError = ValidateRemoval(target);
            bool ready = error == null;
            bool removable = removalError == null;
            readiness.messageType = ready || removable
                ? HelpBoxMessageType.Info : HelpBoxMessageType.Warning;
            readiness.text = ready
                ? "Ready. One HPR AbilityRunner will be attached to the selected scene " +
                  "object. Your controller, input settings and assets will not be rewritten. " +
                  "This changes only the selected scene when you confirm. Undo is available."
                : removable
                    ? "The selected scene object already contains one HPR runner. " +
                      "Remove HPR runner explicitly if you want to detach it. Undo is available. " +
                      "This does not uninstall the HPR package or remove other components."
                    : "Nothing will be modified. " + error;
            attachButton.SetEnabled(ready);
            removeButton.SetEnabled(removable);
        }

        private void AttachRequested()
        {
            if (readiness == null)
                return;
            try
            {
                readiness.text = "Applying only the selected ability; scene is not automatically saved.";
                var result = AttachExplicitly(target, ability, provider);
                Selection.activeObject = result;
                readiness.messageType = HelpBoxMessageType.Info;
                readiness.text = "Attached in the currently open scene. Inspect the new AbilityRunner; " +
                                 "save your scene to keep the change, or choose Edit > Undo.";
                attachButton.SetEnabled(false);
                removeButton.SetEnabled(true);
            }
            catch (Exception error)
            {
                Debug.LogException(error);
                readiness.messageType = HelpBoxMessageType.Error;
                readiness.text = "No ability was installed: " + error.Message;
                Refresh();
            }
        }

        private void RemoveRequested()
        {
            string validationError = ValidateRemoval(target);
            if (validationError != null)
            {
                Refresh();
                return;
            }
            // Removing a component can invalidate references elsewhere in the
            // buyer's game; require explicit consent and never delete assets.
            if (!EditorUtility.DisplayDialog("Remove HPR runner?",
                    "Remove the HPR AbilityRunner from only the selected scene object? " +
                    "This does not remove your player, prefab, resources or independent " +
                    "ability definitions. Review other references and save the scene yourself. " +
                    "Unity Undo can restore the component before the Editor closes.",
                    "Remove HPR runner", "Cancel"))
            {
                readiness.text = "Removal cancelled. No scene objects changed.";
                return;
            }
            try
            {
                RemoveExplicitly(target);
                Refresh();
                readiness.messageType = HelpBoxMessageType.Info;
                readiness.text = "HPR runner detached in this scene. " +
                                 "Choose Edit > Undo to restore it, or save the scene to keep removal. " +
                                 "Customer assets and project settings were not changed.";
            }
            catch (Exception error)
            {
                Debug.LogException(error);
                Refresh();
                readiness.messageType = HelpBoxMessageType.Error;
                readiness.text = "Removal was not completed: " + error.Message;
            }
        }

        /// <summary>Read-only validation for one deliberate scene-component removal.</summary>
        public static string ValidateRemoval(GameObject target)
        {
            if (EditorApplication.isPlayingOrWillChangePlaymode)
                return "Stop Play mode before removing a scene component.";
            if (target == null)
                return "Select an existing GameObject in the current scene.";
            if (EditorUtility.IsPersistent(target) || PrefabUtility.IsPartOfPrefabAsset(target))
                return "Select a scene instance, not a prefab asset.";
            if (!target.scene.IsValid() || !target.scene.isLoaded ||
                target.scene != EditorSceneManager.GetActiveScene())
                return "Only the current, loaded scene can be edited.";
            int count = target.GetComponents<AbilityRunnerComponent>().Length;
            if (count == 0)
                return "There is no HPR AbilityRunner to remove from this object.";
            if (count != 1)
                return "Multiple HPR runners found; refuse ambiguous removal and inspect manually.";
            return null;
        }

        /// <summary>Pure, read-only gate, intended for both the UI and real Editor QA.</summary>
        public static string ValidateSelection(GameObject target, AbilityData ability,
                                               MonoBehaviour resourceProvider)
        {
            if (EditorApplication.isPlayingOrWillChangePlaymode)
                return "Stop Play mode before editing a customer scene.";
            if (target == null)
                return "Select an existing GameObject in the currently open scene.";
            if (EditorUtility.IsPersistent(target) || PrefabUtility.IsPartOfPrefabAsset(target))
                return "Select a scene object, not an asset prefab.";
            if (!target.scene.IsValid() || !target.scene.isLoaded ||
                target.scene != EditorSceneManager.GetActiveScene())
                return "Only the current, loaded scene can be edited.";
            if (target.GetComponent<AbilityRunnerComponent>() != null)
                return "An HPR AbilityRunner already exists; no automatic replacement is allowed.";
            if (resourceProvider == null || resourceProvider.gameObject != target ||
                !(resourceProvider is IAbilityResourcePool))
                return "Choose an IAbilityResourcePool component on that same GameObject.";
            if (ability == null || string.IsNullOrWhiteSpace(ability.Id))
                return "Choose a valid customer-owned ability with a stable identifier.";
            string path = AssetDatabase.GetAssetPath(ability);
            if (string.IsNullOrWhiteSpace(path) ||
                !path.StartsWith("Assets/", StringComparison.Ordinal) ||
                path.StartsWith("Assets/HPRGameplaySuite/", StringComparison.Ordinal) ||
                AssetDatabase.LoadAssetAtPath<AbilityData>(path) != ability)
                return "Copy the vendor sample into your own Assets folder before integrating.";
            if (float.IsNaN(ability.Cost) || float.IsInfinity(ability.Cost) || ability.Cost < 0f ||
                float.IsNaN(ability.Cooldown) || float.IsInfinity(ability.Cooldown) ||
                ability.Cooldown < 0f)
                return "Ability cost/cooldown must be finite and nonnegative.";
            if (ability.Effects == null || ability.Effects.Count == 0)
                return "The ability has no configured effect.";
            foreach (AbilityEffectData effect in ability.Effects)
            {
                string effectPath = effect == null ? "" : AssetDatabase.GetAssetPath(effect);
                if (string.IsNullOrEmpty(effectPath) ||
                    !effectPath.StartsWith("Assets/", StringComparison.Ordinal) ||
                    effectPath.StartsWith("Assets/HPRGameplaySuite/", StringComparison.Ordinal))
                    return "All effects must be independently owned outside the HPR sample folder.";
            }
            return null;
        }

        /// <summary>
        /// Explicit, reversible single-scene operation. Never saves files, rewrites
        /// player/controller source, changes project settings or copies assets.
        /// </summary>
        public static AbilityRunnerComponent AttachExplicitly(GameObject target, AbilityData ability,
                                                                MonoBehaviour resourceProvider)
        {
            string error = ValidateSelection(target, ability, resourceProvider);
            if (error != null)
                throw new ArgumentException(error);

            Undo.IncrementCurrentGroup();
            int group = Undo.GetCurrentGroup();
            Undo.SetCurrentGroupName("HPR: attach one selected ability");
            try
            {
                AbilityRunnerComponent runner = Undo.AddComponent<AbilityRunnerComponent>(target);
                if (runner == null)
                    throw new InvalidOperationException("Unity could not add the ability runner.");

                Undo.RecordObject(runner, "HPR: configure selected ability");
                var serialized = new SerializedObject(runner);
                var abilities = serialized.FindProperty("configuredAbilities");
                var unlocked = serialized.FindProperty("unlockAllConfiguredAbilities");
                var resources = serialized.FindProperty("resourcePoolBehaviour");
                var effectOrigin = serialized.FindProperty("effectOrigin");
                if (abilities == null || !abilities.isArray ||
                    unlocked == null || unlocked.propertyType != SerializedPropertyType.Boolean ||
                    resources == null || resources.propertyType != SerializedPropertyType.ObjectReference ||
                    effectOrigin == null)
                    throw new InvalidOperationException("The installed HPR component has incompatible Inspector fields.");
                abilities.arraySize = 1;
                abilities.GetArrayElementAtIndex(0).objectReferenceValue = ability;
                unlocked.boolValue = true;
                resources.objectReferenceValue = resourceProvider;
                effectOrigin.objectReferenceValue = target.transform;
                if (!serialized.ApplyModifiedProperties())
                    throw new InvalidOperationException("Unity did not apply the selected ability settings.");

                if (PrefabUtility.IsPartOfPrefabInstance(runner))
                    PrefabUtility.RecordPrefabInstancePropertyModifications(runner);
                EditorSceneManager.MarkSceneDirty(target.scene);
                Undo.CollapseUndoOperations(group);
                return runner;
            }
            catch
            {
                Undo.RevertAllDownToGroup(group);
                throw;
            }
        }

        /// <summary>Explicit, scene-only detach; never deletes user assets or saves files.</summary>
        public static bool RemoveExplicitly(GameObject target)
        {
            string error = ValidateRemoval(target);
            if (error != null)
                throw new ArgumentException(error);
            AbilityRunnerComponent runner = target.GetComponent<AbilityRunnerComponent>();
            if (runner == null)
                throw new InvalidOperationException("Selected player has no HPR runner.");
            Undo.IncrementCurrentGroup();
            int group = Undo.GetCurrentGroup();
            Undo.SetCurrentGroupName("HPR: remove one selected ability runner");
            try
            {
                Undo.DestroyObjectImmediate(runner);
                EditorSceneManager.MarkSceneDirty(target.scene);
                Undo.CollapseUndoOperations(group);
                return true;
            }
            catch
            {
                Undo.RevertAllDownToGroup(group);
                throw;
            }
        }
    }
}
#endif
