using System;
using System.IO;
using System.Linq;
using UnityEditor;
using UnityEditor.Animations;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.SceneManagement;

namespace HPR
{
    public static class LocalCharacterAnimationTools
    {
        private const string GameplayScenePath = "Assets/Scenes/Gameplay.unity";
        private const string GeneratedRoot = "Assets/DoubleL/HPRGenerated";
        private const string EnemyControllerPath = GeneratedRoot + "/HPR_EnemyHumanoid.controller";
        private static readonly string[] CharacterSearchRoots =
        {
            "Assets/npc_casual_set_00",
            "Assets/Survivalist",
            "Assets/Survivalist/Prefab",
            "Assets/Survivalist character",
        };

        private static readonly string[] CombatAnimationRoots =
        {
            "Assets/DoubleL/Demo/Anim",
        };

        [MenuItem("Tools/HPR/Integrate/Apply Animation Packs")]
        public static void ApplyAnimationPacks()
        {
            EnsureFolder("Assets", "DoubleL");
            EnsureFolder("Assets/DoubleL", "HPRGenerated");

            var enemyController = EnsureEnemyCombatController();
            int updatedPrefabs = ApplyEnemyAnimatorControllers(enemyController);
            int placedAmbient = ApplyAmbientCharacters();

            AssetDatabase.SaveAssets();
            AssetDatabase.Refresh();
            ImportedAssetMetadataSynchronizer.Synchronize();
            Debug.Log($"Applied local animation packs to {updatedPrefabs} character prefabs and placed {placedAmbient} ambient NPCs.");
        }

        [MenuItem("Tools/HPR/Integrate/Apply Animation Packs From Batch")]
        public static void ApplyAnimationPacksFromBatch()
        {
            ApplyAnimationPacks();
        }

        private static AnimatorController EnsureEnemyCombatController()
        {
            var controller = AssetDatabase.LoadAssetAtPath<AnimatorController>(EnemyControllerPath);
            if (controller == null)
            {
                controller = AnimatorController.CreateAnimatorControllerAtPath(EnemyControllerPath);
            }

            var idle = LoadClip("OneHand_Up_Idle");
            var walk = LoadClip("OneHand_Up_Walk_F_InPlace");
            var run = LoadClip("OneHand_Up_Run_F_InPlace");
            var attack = LoadClip("Enemy_Attack_1_InPlace") ?? LoadClip("OneHand_Up_Attack_1_InPlace");
            var hit = LoadClip("Hit_F_1_InPlace");
            var death = LoadClip("Hit_F_2_InPlace") ?? hit;

            if (idle == null || walk == null || run == null || attack == null || hit == null || death == null)
            {
                throw new Exception("Missing required imported animation clips for enemy controller generation.");
            }

            RebuildController(controller, idle, walk, run, attack, hit, death);
            EditorUtility.SetDirty(controller);
            return controller;
        }

        private static void RebuildController(AnimatorController controller, AnimationClip idle, AnimationClip walk, AnimationClip run, AnimationClip attack, AnimationClip hit, AnimationClip death)
        {
            controller.parameters = Array.Empty<AnimatorControllerParameter>();
            controller.AddParameter("MoveSpeed", AnimatorControllerParameterType.Float);
            controller.AddParameter("Attack", AnimatorControllerParameterType.Trigger);
            controller.AddParameter("Hit", AnimatorControllerParameterType.Trigger);
            controller.AddParameter("Dead", AnimatorControllerParameterType.Bool);

            var stateMachine = controller.layers.Length > 0 ? controller.layers[0].stateMachine : new AnimatorStateMachine();
            if (controller.layers.Length == 0)
            {
                controller.AddLayer("Base Layer");
                stateMachine = controller.layers[0].stateMachine;
            }

            foreach (var child in stateMachine.states.ToArray())
            {
                stateMachine.RemoveState(child.state);
            }

            foreach (var transition in stateMachine.anyStateTransitions.ToArray())
            {
                stateMachine.RemoveAnyStateTransition(transition);
            }

            var locomotion = stateMachine.AddState("Locomotion");
            var blendTree = new BlendTree
            {
                name = "EnemyLocomotion",
                blendParameter = "MoveSpeed",
                useAutomaticThresholds = false
            };
            AssetDatabase.AddObjectToAsset(blendTree, controller);
            blendTree.AddChild(idle, 0f);
            blendTree.AddChild(walk, 0.35f);
            blendTree.AddChild(run, 1f);
            locomotion.motion = blendTree;

            var attackState = stateMachine.AddState("Attack");
            attackState.motion = attack;

            var hitState = stateMachine.AddState("Hit");
            hitState.motion = hit;

            var deadState = stateMachine.AddState("Dead");
            deadState.motion = death;

            stateMachine.defaultState = locomotion;

            AddReturnTransition(attackState, locomotion, 0.92f);
            AddReturnTransition(hitState, locomotion, 0.82f);

            var attackTransition = stateMachine.AddAnyStateTransition(attackState);
            attackTransition.hasExitTime = false;
            attackTransition.duration = 0.06f;
            attackTransition.AddCondition(AnimatorConditionMode.If, 0f, "Attack");

            var hitTransition = stateMachine.AddAnyStateTransition(hitState);
            hitTransition.hasExitTime = false;
            hitTransition.duration = 0.04f;
            hitTransition.AddCondition(AnimatorConditionMode.If, 0f, "Hit");

            var deadTransition = stateMachine.AddAnyStateTransition(deadState);
            deadTransition.hasExitTime = false;
            deadTransition.duration = 0.05f;
            deadTransition.AddCondition(AnimatorConditionMode.If, 0f, "Dead");
        }

        private static void AddReturnTransition(AnimatorState fromState, AnimatorState toState, float exitTime)
        {
            var transition = fromState.AddTransition(toState);
            transition.hasExitTime = true;
            transition.exitTime = exitTime;
            transition.duration = 0.08f;
        }

        private static int ApplyEnemyAnimatorControllers(RuntimeAnimatorController controller)
        {
            int updated = 0;
            var enemyPrefabs = AssetDatabase.FindAssets("t:EnemyData", new[] { GameplayDataSeeder.EnemiesRoot })
                .Select(AssetDatabase.GUIDToAssetPath)
                .Select(AssetDatabase.LoadAssetAtPath<EnemyData>)
                .Where(asset => asset != null && asset.VisualPrefab != null)
                .Select(asset => AssetDatabase.GetAssetPath(asset.VisualPrefab))
                .Where(path => !string.IsNullOrWhiteSpace(path))
                .Distinct()
                .ToArray();

            foreach (var prefabPath in enemyPrefabs)
            {
                if (AssignControllerToPrefab(prefabPath, controller))
                {
                    updated++;
                }
            }

            return updated;
        }

        private static bool AssignControllerToPrefab(string prefabPath, RuntimeAnimatorController controller)
        {
            var prefabRoot = PrefabUtility.LoadPrefabContents(prefabPath);
            try
            {
                var animator = prefabRoot.GetComponentInChildren<Animator>(true);
                if (animator == null)
                {
                    return false;
                }

                bool changed = false;
                if (animator.runtimeAnimatorController != controller)
                {
                    animator.runtimeAnimatorController = controller;
                    changed = true;
                }

                if (animator.applyRootMotion)
                {
                    animator.applyRootMotion = false;
                    changed = true;
                }

                if (animator.cullingMode != AnimatorCullingMode.AlwaysAnimate)
                {
                    animator.cullingMode = AnimatorCullingMode.AlwaysAnimate;
                    changed = true;
                }

                if (!changed)
                {
                    return false;
                }

                PrefabUtility.SaveAsPrefabAsset(prefabRoot, prefabPath);
                return true;
            }
            finally
            {
                PrefabUtility.UnloadPrefabContents(prefabRoot);
            }
        }

        private static int ApplyAmbientCharacters()
        {
            if (!File.Exists(GameplayScenePath))
            {
                return 0;
            }

            var scene = EditorSceneManager.OpenScene(GameplayScenePath, OpenSceneMode.Single);
            var world = GameObject.Find("World")?.transform;
            if (world == null)
            {
                return 0;
            }

            var propsRoot = EnsureChild(world, "PropsRoot");
            var ambientRoot = EnsureChild(propsRoot, "AmbientCharacters");
            ClearChildren(ambientRoot);

            int placed = 0;
            placed += TryPlaceAmbientCharacter(
                ambientRoot,
                "hub_engineer",
                new[] { "npc_csl_00_character_01m_02", "Survivalist (1)" },
                "Assets/Kevin Iglesias/Human Animations/Unity Demo Scenes/Human Crafting Animations/AnimatorControllers/Male/HumanM@Building01.controller",
                new Vector3(-6.6f, 0f, 4.2f),
                new Vector3(0f, 42f, 0f),
                1.8f);
            placed += TryPlaceAmbientCharacter(
                ambientRoot,
                "medbay_operator",
                new[] { "npc_csl_00_character_02f_01", "npc_csl_00_character_01f_02" },
                "Assets/Kevin Iglesias/Human Animations/Unity Demo Scenes/Human Crafting Animations/AnimatorControllers/Female/HumanF@Gathering02.controller",
                new Vector3(-19.6f, 0f, 2.6f),
                new Vector3(0f, -78f, 0f),
                1.72f);

            if (placed > 0)
            {
                EditorSceneManager.MarkSceneDirty(scene);
                EditorSceneManager.SaveScene(scene);
            }

            return placed;
        }

        private static int TryPlaceAmbientCharacter(Transform parent, string instanceName, string[] preferredPrefabNames, string controllerPath, Vector3 position, Vector3 rotationEuler, float targetHeight)
        {
            var prefab = FindBestCharacterPrefab(preferredPrefabNames);
            var controller = AssetDatabase.LoadAssetAtPath<RuntimeAnimatorController>(controllerPath);
            if (prefab == null || controller == null)
            {
                return 0;
            }

            var instance = PrefabUtility.InstantiatePrefab(prefab, parent) as GameObject;
            if (instance == null)
            {
                return 0;
            }

            instance.name = instanceName;
            instance.transform.localPosition = position;
            instance.transform.localEulerAngles = rotationEuler;

            var animator = instance.GetComponentInChildren<Animator>(true);
            if (animator != null)
            {
                animator.runtimeAnimatorController = controller;
                animator.applyRootMotion = false;
                animator.cullingMode = AnimatorCullingMode.AlwaysAnimate;
            }

            foreach (var behaviour in instance.GetComponentsInChildren<MonoBehaviour>(true))
            {
                if (behaviour == null)
                {
                    continue;
                }

                UnityEngine.Object.DestroyImmediate(behaviour);
            }

            foreach (var rigidbody in instance.GetComponentsInChildren<Rigidbody>(true))
            {
                UnityEngine.Object.DestroyImmediate(rigidbody);
            }

            foreach (var collider in instance.GetComponentsInChildren<Collider>(true))
            {
                UnityEngine.Object.DestroyImmediate(collider);
            }

            float height = MeasureBounds(instance).size.y;
            if (height > 0.01f)
            {
                float scale = targetHeight / height;
                instance.transform.localScale = Vector3.one * scale;
            }

            return 1;
        }

        private static GameObject FindBestCharacterPrefab(string[] preferredNames)
        {
            var roots = CharacterSearchRoots.Where(AssetDatabase.IsValidFolder).Distinct().ToArray();
            if (roots.Length == 0)
            {
                return null;
            }

            var preferred = preferredNames
                .Where(name => !string.IsNullOrWhiteSpace(name))
                .Select(name => name.Trim().ToLowerInvariant())
                .ToArray();

            return AssetDatabase.FindAssets("t:GameObject", roots)
                .Select(AssetDatabase.GUIDToAssetPath)
                .Where(path => path.EndsWith(".prefab", StringComparison.OrdinalIgnoreCase) || path.EndsWith(".fbx", StringComparison.OrdinalIgnoreCase))
                .Select(path => new
                {
                    asset = AssetDatabase.LoadAssetAtPath<GameObject>(path),
                    name = Path.GetFileNameWithoutExtension(path).ToLowerInvariant()
                })
                .Where(candidate => candidate.asset != null)
                .OrderByDescending(candidate => preferred.Any(name => candidate.name == name))
                .ThenByDescending(candidate => preferred.Count(name => candidate.name.Contains(name)))
                .ThenBy(candidate => candidate.name.Length)
                .Select(candidate => candidate.asset)
                .FirstOrDefault();
        }

        private static AnimationClip LoadClip(string clipName)
        {
            return AssetDatabase.FindAssets($"{clipName} t:AnimationClip", CombatAnimationRoots)
                .Select(AssetDatabase.GUIDToAssetPath)
                .Select(AssetDatabase.LoadAssetAtPath<AnimationClip>)
                .FirstOrDefault(clip => clip != null && clip.name == clipName);
        }

        private static Bounds MeasureBounds(GameObject prefabOrInstance)
        {
            var renderers = prefabOrInstance.GetComponentsInChildren<Renderer>(true);
            if (renderers.Length == 0)
            {
                return new Bounds(prefabOrInstance.transform.position, Vector3.zero);
            }

            var bounds = renderers[0].bounds;
            foreach (var renderer in renderers.Skip(1))
            {
                bounds.Encapsulate(renderer.bounds);
            }

            return bounds;
        }

        private static Transform EnsureChild(Transform parent, string name)
        {
            var child = parent.Find(name);
            if (child != null)
            {
                return child;
            }

            var go = new GameObject(name).transform;
            go.SetParent(parent, false);
            return go;
        }

        private static void ClearChildren(Transform parent)
        {
            for (int i = parent.childCount - 1; i >= 0; i--)
            {
                UnityEngine.Object.DestroyImmediate(parent.GetChild(i).gameObject);
            }
        }

        private static void EnsureFolder(string parent, string child)
        {
            if (!AssetDatabase.IsValidFolder($"{parent}/{child}"))
            {
                AssetDatabase.CreateFolder(parent, child);
            }
        }
    }
}
