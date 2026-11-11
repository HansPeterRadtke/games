// Copyright (c) Multiverse Studio. All rights reserved.
// Original self-contained training arena built entirely from Unity primitives.
#if UNITY_EDITOR
using System;
using System.IO;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using HPR;

namespace HPR.GameplaySuite
{
    public static class HprGameplaySuiteSceneBuilder
    {
        private const string Root = "Assets/HPRGameplaySuite";
        private const string Samples = Root + "/Samples";
        private const string Scene = Root + "/Demo/GameplaySuiteShowcase.unity";

        // Only save new HPR sample assets authored by this explicitly requested
        // private scene creation. Never flush unrelated customer Inspector edits.
        // SaveAssetIfDirty does not call OnWillSaveAssets; this tradeoff is
        // disclosed for projects using custom VCS/asset checkout hooks.
        private static void SaveOwnedSamplesOnly()
        {
            foreach (string guid in AssetDatabase.FindAssets("", new[] { Samples }))
            {
                string path = AssetDatabase.GUIDToAssetPath(guid);
                if (!path.StartsWith(Samples + "/", StringComparison.Ordinal) ||
                    !(path.EndsWith(".asset", StringComparison.OrdinalIgnoreCase) ||
                      path.EndsWith(".mat", StringComparison.OrdinalIgnoreCase)))
                    continue;
                UnityEngine.Object asset = AssetDatabase.LoadMainAssetAtPath(path);
                if (asset == null)
                    throw new InvalidOperationException("Missing HPR newly authored sample: " + path);
                AssetDatabase.SaveAssetIfDirty(asset);
            }
        }

        private static T CreateAsset<T>(string filename) where T : ScriptableObject
        {
            string path = Samples + "/" + filename + ".asset";
            T data = AssetDatabase.LoadAssetAtPath<T>(path);
            if (data != null) return data;
            data = ScriptableObject.CreateInstance<T>();
            AssetDatabase.CreateAsset(data, path);
            return data;
        }

        private static Material CreateMaterial(string name, Color color, float metallic = 0f, float roughness = 0.6f)
        {
            string path = Samples + "/" + name + ".mat";
            Material material = AssetDatabase.LoadAssetAtPath<Material>(path);
            if (material == null)
            {
                // Select a shader matching the active render pipeline; never ship a pink legacy
                // Standard material into an active URP/HDRP project.
                bool scriptablePipeline = UnityEngine.Rendering.GraphicsSettings.currentRenderPipeline != null;
                Shader shader = scriptablePipeline
                    ? (Shader.Find("Universal Render Pipeline/Lit") ?? Shader.Find("HDRP/Lit"))
                    : Shader.Find("Standard");
                if (shader == null) shader = Shader.Find("Unlit/Color");
                if (shader == null) throw new InvalidOperationException("Unity has no supported demo shader");
                material = new Material(shader);
                AssetDatabase.CreateAsset(material, path);
            }
            material.color = color;
            // Metal/roughness workflow: Standard/URP smoothness is one minus roughness.
            float smoothness = 1f - Mathf.Clamp01(roughness);
            if (material.HasProperty("_Metallic")) material.SetFloat("_Metallic", Mathf.Clamp01(metallic));
            if (material.HasProperty("_Smoothness")) material.SetFloat("_Smoothness", smoothness);
            if (material.HasProperty("_Glossiness")) material.SetFloat("_Glossiness", smoothness);
            EditorUtility.SetDirty(material);
            return material;
        }

        private static GameObject Shape(string name, PrimitiveType type, Vector3 pos, Vector3 scale, Material material,
            Transform parent = null)
        {
            GameObject obj = GameObject.CreatePrimitive(type);
            obj.name = name;
            if (parent != null) obj.transform.SetParent(parent, false);
            obj.transform.position = pos;
            obj.transform.localScale = scale;
            obj.GetComponent<Renderer>().sharedMaterial = material;
            return obj;
        }

        private static GameObject DecorativeShape(string name, PrimitiveType type,
            Vector3 position, Vector3 scale, Material material, Transform parent = null)
        {
            GameObject result = Shape(name, type, position, scale, material, parent);
            Collider collider = result.GetComponent<Collider>();
            if (collider != null) UnityEngine.Object.DestroyImmediate(collider);
            return result;
        }

        private static void FloatingLabel(string name, string caption, Vector3 position,
            Color color, float size = .12f)
        {
            GameObject root = new GameObject(name);
            root.transform.position = position;
            TextMesh label = root.AddComponent<TextMesh>();
            label.text = caption;
            label.fontSize = 45;
            label.characterSize = size;
            label.fontStyle = FontStyle.Bold;
            label.anchor = TextAnchor.MiddleCenter;
            label.alignment = TextAlignment.Center;
            label.color = color;
        }

        private static void SetRef(Component component, string property, UnityEngine.Object value)
        {
            var data = new SerializedObject(component);
            SerializedProperty field = data.FindProperty(property);
            if (field == null) throw new MissingFieldException(component.GetType().Name, property);
            field.objectReferenceValue = value;
            data.ApplyModifiedPropertiesWithoutUndo();
            EditorUtility.SetDirty(component);
        }

        [MenuItem("Tools/HPR/Gameplay Suite/Open Showcase")]
        public static void OpenShowcase()
        {
            if (!EditorSceneManager.SaveCurrentModifiedScenesIfUserWantsTo()) return;
            SceneAsset asset = AssetDatabase.LoadAssetAtPath<SceneAsset>(Scene);
            if (asset == null)
            {
                EditorUtility.DisplayDialog("HPR Suite", "Demo scene missing. Use Build Showcase to recreate it.", "OK");
                return;
            }
            EditorSceneManager.OpenScene(Scene, OpenSceneMode.Single);
            Debug.Log("HPR Suite buyer demo scene opened.");
        }

        // A partial import must still compile and explain where to find the missing tool.
        // Referencing the installer type directly would make both diagnostics unavailable.
        internal static string AbilityInstallerIssue()
        {
            const string path = Root + "/Editor/HprSelectedAbilityInstaller.cs";
            var script = AssetDatabase.LoadAssetAtPath<MonoScript>(path);
            if (script == null)
                return path;
            Type type = script.GetClass();
            if (type == null || type.FullName != "HPR.GameplaySuite.Experimental.HprSelectedAbilityInstaller" ||
                !typeof(EditorWindow).IsAssignableFrom(type))
                return path + " (check the script and Console for compilation errors)";
            return null;
        }

        [MenuItem("Tools/HPR/Gameplay Suite/Verify Installation")]
        public static void VerifyInstallation()
        {
            int checkedFiles = 0;
            var missing = new System.Collections.Generic.List<string>();
            string[] modules = {
                "eventbus", "inventory", "composition", "save", "stats",
                "interaction", "abilities", "weapons", "ai", "world"
            };
            foreach (string module in modules)
            {
                string moduleRoot = Root + "/Modules/com.hpr." + module + "/Runtime/";
                string[] scripts = AssetDatabase.FindAssets("t:MonoScript", new[] { moduleRoot });
                if (scripts.Length == 0) missing.Add(module + " runtime C# scripts");
                else checkedFiles += scripts.Length;
            }
            foreach (string required in new[] { Scene, Root + "/QUICKSTART.md",
                Root + "/ARCHITECTURE.md", Samples + "/FieldMedkit.asset",
                Samples + "/TrainingKey.asset", Samples + "/RepairAbility.asset",
                Samples + "/PulseAbility.asset", Samples + "/TrainingWorldRegistry.asset" })
            {
                if (AssetDatabase.LoadMainAssetAtPath(required) == null)
                    missing.Add(required);
            }
            string installerIssue = AbilityInstallerIssue();
            if (installerIssue != null) missing.Add(installerIssue);
            string report = "HPR Gameplay Systems Suite\nUnity: " + Application.unityVersion +
                "\nFound original runtime scripts: " + checkedFiles +
                "\nMissing requirements: " + missing.Count +
                (missing.Count == 0 ? "\nAll ten modules and key demo assets found." :
                    "\nMissing: " + string.Join(", ", missing));
            if (missing.Count > 0) Debug.LogError(report);
            else Debug.Log(report);
            EditorUtility.DisplayDialog("HPR Gameplay Suite installation check",
                report, "OK");
        }

        // Internal creation entry point for disposable release projects only.
        // The packaged demo is already built: do not expose a destructive rebuild menu.
        public static void BuildShowcase()
        {
            if (AssetDatabase.LoadAssetAtPath<SceneAsset>(Scene) != null ||
                AssetDatabase.FindAssets("", new[] { Samples }).Length > 0)
                throw new InvalidOperationException(
                    "Existing demo assets found. No files modified. " +
                    "Open the shipped demo; generate new defaults only in an empty project.");
            if (!Application.isBatchMode &&
                !EditorSceneManager.SaveCurrentModifiedScenesIfUserWantsTo())
                throw new OperationCanceledException("Unsaved scenes preserved; generation cancelled.");
            Directory.CreateDirectory(Samples);
            Directory.CreateDirectory(Root + "/Demo");
            AssetDatabase.Refresh();
            Material floorMat = CreateMaterial("ArenaDarkSlate", new Color(.11f, .16f, .22f), 0f, 0.82f);
            Material trimMat = CreateMaterial("ArenaSteel", new Color(.26f, .32f, .39f), .85f, .37f);
            Material wallMat = CreateMaterial("ArenaWall", new Color(.17f, .24f, .32f), 0f, .72f);
            Material cyanMat = CreateMaterial("ArenaCyan", new Color(.1f, .74f, .82f));
            Material amberMat = CreateMaterial("ArenaAmber", new Color(.98f, .67f, .17f));
            Material redMat = CreateMaterial("ArenaEnemy", new Color(.98f, .32f, .18f));
            Material blueMat = CreateMaterial("ArenaPlayer", new Color(.22f, .55f, .96f));

            ItemData medkit = CreateAsset<ItemData>("FieldMedkit");
            medkit.Id = "hpr_suite_field_medkit";
            medkit.DisplayName = "Field Medkit";
            medkit.Description = "Collect from the cyan supply station or defeat the enemy; restores 30 health.";
            medkit.ItemType = ItemType.Consumable;
            medkit.StartingPlayerQuantity = 0;
            EditorUtility.SetDirty(medkit);

            ItemData key = CreateAsset<ItemData>("TrainingKey");
            key.Id = "hpr_suite_training_key";
            key.DisplayName = "Training Key";
            key.Description = "Pick up the amber key to unlock the training gate.";
            key.ItemType = ItemType.Key;
            key.StartingPlayerQuantity = 0;
            EditorUtility.SetDirty(key);

            WeaponData rifle = CreateAsset<WeaponData>("DemoRifle");
            rifle.Id = "hpr_suite_demo_rifle";
            rifle.DisplayName = "Training Rifle";
            rifle.Damage = 15f;
            rifle.Range = 50f;
            rifle.FireDelay = 0.35f;
            rifle.MagazineSize = 6;
            rifle.StartingMagazineAmmo = 6;
            rifle.StartingReserveAmmo = 30;
            rifle.MaxAmmo = 60;
            rifle.UsesAmmo = true;
            EditorUtility.SetDirty(rifle);

            EnemyData raider = CreateAsset<EnemyData>("DemoRaider");
            raider.Id = "hpr_suite_demo_raider";
            raider.DisplayName = "Training Target";
            raider.MaxHealth = 60f;
            raider.AttackRange = 2.5f;
            raider.ChaseRange = 10f;
            raider.AttackDamage = 8f;
            raider.MoveSpeed = 2f;
            raider.AttackCooldown = 1f;
            raider.AIType = EnemyAIType.PatrolChase;
            EditorUtility.SetDirty(raider);

            AbilityEffectData healEffect = CreateAsset<AbilityEffectData>("RepairEffect");
            healEffect.Id = "hpr_suite_repair_effect";
            healEffect.DisplayName = "Recovery";
            healEffect.EffectType = AbilityEffectType.Heal;
            healEffect.Value = 20f;
            EditorUtility.SetDirty(healEffect);

            AbilityData heal = CreateAsset<AbilityData>("RepairAbility");
            heal.Id = "hpr_suite_repair";
            heal.DisplayName = "Field Recovery";
            heal.Description = "Spend twenty stamina to restore twenty health. Four-second cooldown.";
            heal.Cost = 20f;
            heal.Cooldown = 4f;
            heal.Effects.Clear();
            heal.Effects.Add(healEffect);
            EditorUtility.SetDirty(heal);

            AbilityEffectData pulseEffect = CreateAsset<AbilityEffectData>("PulseEffect");
            pulseEffect.Id = "hpr_suite_pulse_effect";
            pulseEffect.DisplayName = "Pulse";
            pulseEffect.EffectType = AbilityEffectType.AreaDamage;
            pulseEffect.Value = 12f;
            pulseEffect.Radius = 7f;
            pulseEffect.ForwardOffset = 0f;
            EditorUtility.SetDirty(pulseEffect);

            AbilityData pulse = CreateAsset<AbilityData>("PulseAbility");
            pulse.Id = "hpr_suite_pulse";
            pulse.DisplayName = "Damage Pulse";
            pulse.Description = "Area damage to the target through a typed DamageEvent. Six-second cooldown.";
            pulse.Cost = 25f;
            pulse.Cooldown = 6f;
            pulse.TargetType = AbilityTargetType.Area;
            pulse.Effects.Clear();
            pulse.Effects.Add(pulseEffect);
            EditorUtility.SetDirty(pulse);

            AssetMetadata medkitMetadata = CreateAsset<AssetMetadata>("WorldMedkitMetadata");
            medkitMetadata.AssetId = medkit.Id;
            medkitMetadata.DisplayName = medkit.DisplayName;
            medkitMetadata.AssetType = AssetType.Prop;
            EditorUtility.SetDirty(medkitMetadata);
            AssetRegistry catalog = CreateAsset<AssetRegistry>("TrainingWorldRegistry");
            catalog.SetEntries(new[] { medkitMetadata });
            EditorUtility.SetDirty(catalog);

            var scene = EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);
            Material gridMat = CreateMaterial("ArenaGrid", new Color(.10f, .20f, .27f), .52f, .44f);
            Material railMat = CreateMaterial("ArenaSafetyTrim", new Color(.90f, .55f, .15f), .4f, .44f);
            Material underlay = CreateMaterial("ArenaSubfloor", new Color(.065f, .092f, .14f), .18f, .8f);
            Material instrument = CreateMaterial("ArenaInstrument", new Color(.09f, .28f, .38f), .28f, .48f);
            Shape("Arena / structural plinth", PrimitiveType.Cube, new Vector3(0, -.24f, 0),
                new Vector3(17.8f, .48f, 12.8f), underlay);
            Shape("Arena / matte tactical floor", PrimitiveType.Plane, new Vector3(0, .02f, 0),
                new Vector3(1.7f, 1f, 1.2f), floorMat);
            Shape("North safety boundary", PrimitiveType.Cube, new Vector3(0, .75f, 6f),
                new Vector3(17f, 1.5f, .3f), wallMat);
            Shape("South safety boundary", PrimitiveType.Cube, new Vector3(0, .75f, -6f),
                new Vector3(17f, 1.5f, .3f), wallMat);
            Shape("West safety boundary", PrimitiveType.Cube, new Vector3(-8.5f, .75f, 0),
                new Vector3(.3f, 1.5f, 12f), wallMat);
            Shape("East safety boundary", PrimitiveType.Cube, new Vector3(8.5f, .75f, 0),
                new Vector3(.3f, 1.5f, 12f), wallMat);
            for (int x = -7; x <= 7; x += 2)
                DecorativeShape("Grid / longitudinal " + x, PrimitiveType.Cube,
                    new Vector3(x, .044f, 0), new Vector3(.025f, .025f, 11.5f), gridMat);
            for (int z = -5; z <= 5; z += 2)
                DecorativeShape("Grid / latitude " + z, PrimitiveType.Cube,
                    new Vector3(0, .045f, z), new Vector3(16.5f, .025f, .025f), gridMat);
            DecorativeShape("Combat lane / luminous separator", PrimitiveType.Cube,
                new Vector3(0, .06f, 0), new Vector3(.13f, .025f, 11.5f), trimMat);
            DecorativeShape("Blue player zone", PrimitiveType.Cube,
                new Vector3(-4f, .067f, 0), new Vector3(5f, .03f, .15f), cyanMat);
            DecorativeShape("Amber enemy zone", PrimitiveType.Cube,
                new Vector3(3f, .067f, 0), new Vector3(5f, .03f, .15f), amberMat);
            DecorativeShape("Blue player position ring A", PrimitiveType.Cylinder,
                new Vector3(-4, .065f, 0), new Vector3(1.5f, .012f, 1.5f), instrument);
            DecorativeShape("Amber opponent position ring B", PrimitiveType.Cylinder,
                new Vector3(3.3f, .067f, 0), new Vector3(1.5f, .014f, 1.5f), railMat);
            for (int i = -2; i <= 2; i++)
            {
                DecorativeShape("Hazard / gate approach " + i, PrimitiveType.Cube,
                    new Vector3(4f + i * .27f, .065f, 3.3f),
                    new Vector3(.13f, .024f, .55f), railMat);
            }
            Shape("Cargo cover / raised metallic crate", PrimitiveType.Cube,
                new Vector3(.6f, .85f, 3.55f), new Vector3(1.7f, 1.7f, 1.5f), trimMat);
            Shape("Cargo cover / side", PrimitiveType.Cube,
                new Vector3(-.9f, .72f, -3.5f), new Vector3(1.4f, 1.45f, 1.4f), trimMat);
            for (int i = 0; i < 4; i++)
            {
                DecorativeShape("Rail / left reflector " + i, PrimitiveType.Cube,
                    new Vector3(-8.14f, 1.2f, -4.4f + i * 2.8f),
                    new Vector3(.10f, .12f, 1f), cyanMat);
                DecorativeShape("Rail / right reflector " + i, PrimitiveType.Cube,
                    new Vector3(8.14f, 1.2f, -4.4f + i * 2.8f),
                    new Vector3(.10f, .12f, 1f), amberMat);
            }
            FloatingLabel("Header / title", "HPR  /  INTEGRATED SYSTEMS LAB",
                new Vector3(0, 2.7f, 5.9f), new Color(.68f, .89f, 1f), .13f);
            FloatingLabel("Zone A / text", "A / PLAYER  •  INVENTORY + ABILITIES",
                new Vector3(-4.0f, 2f, 5.83f), new Color(.24f, .94f, 1f), .063f);
            FloatingLabel("Zone B / text", "B / TARGET  •  COMBAT + EVENTS",
                new Vector3(3.75f, 2f, 5.83f), new Color(1f, .75f, .35f), .063f);
            GameObject player = Shape("Player / Stats, Inventory, Abilities, EventBus", PrimitiveType.Capsule,
                new Vector3(-4f, 1f, 0f), Vector3.one, blueMat);
            UnityEngine.Object.DestroyImmediate(player.GetComponent<CapsuleCollider>());
            player.AddComponent<CharacterController>();
            player.AddComponent<HprSuiteArenaMotor>();
            DecorativeShape("Player / shoulder armor", PrimitiveType.Cube,
                player.transform.position + new Vector3(0f, .15f, 0),
                new Vector3(.95f, .36f, .58f), trimMat, player.transform);
            DecorativeShape("Player / helmet", PrimitiveType.Sphere,
                player.transform.position + new Vector3(0f, .85f, 0),
                new Vector3(.56f, .40f, .58f), blueMat, player.transform);
            DecorativeShape("Player / forward aim sight", PrimitiveType.Cube,
                player.transform.position + new Vector3(0f, .12f, .58f),
                new Vector3(.13f, .12f, .7f), cyanMat, player.transform);
            player.AddComponent<EventManager>();
            player.AddComponent<InventoryComponent>();
            player.AddComponent<ActorStatsComponent>();
            player.AddComponent<SimpleInteractionActor>();
            player.AddComponent<HprSuiteAbilityPool>();
            player.AddComponent<AbilityRunnerComponent>();

            GameObject enemy = Shape("Target / EnemyRuntime and damageable adapter", PrimitiveType.Capsule,
                new Vector3(3.3f, 1f, 0), new Vector3(1.2f, 1.1f, 1.2f), redMat);
            UnityEngine.Object.DestroyImmediate(enemy.GetComponent<CapsuleCollider>());
            enemy.AddComponent<CharacterController>();
            enemy.AddComponent<HprSuiteArenaMotor>();
            DecorativeShape("Target / chest armor", PrimitiveType.Cube,
                enemy.transform.position + new Vector3(0, .12f, 0),
                new Vector3(1.15f, .44f, .67f), wallMat, enemy.transform);
            DecorativeShape("Target / optical sensor", PrimitiveType.Cube,
                enemy.transform.position + new Vector3(0, .8f, -.44f),
                new Vector3(.7f, .18f, .15f), amberMat, enemy.transform);
            enemy.AddComponent<HprSuiteEnemyTarget>();

            GameObject medkitStation = Shape("Cyan station / interact to collect medkit", PrimitiveType.Cube,
                new Vector3(-4.0f, .55f, 2.3f), new Vector3(1f, 1.1f, 1f), cyanMat);
            var medkitPickup = medkitStation.AddComponent<InventoryPickupInteractable>();
            SetRef(medkitPickup, "itemData", medkit);

            GameObject keyStation = Shape("Amber station / interact to collect key", PrimitiveType.Cube,
                new Vector3(-2f, .45f, -2.1f), new Vector3(.9f, .9f, .9f), amberMat);
            var keyPickup = keyStation.AddComponent<InventoryPickupInteractable>();
            SetRef(keyPickup, "itemData", key);

            GameObject doorRoot = new GameObject("Training gate / requires key");
            doorRoot.transform.position = new Vector3(4.0f, 0f, 2.3f);
            var leaf = Shape("Rotating keyed gate", PrimitiveType.Cube,
                doorRoot.transform.position + new Vector3(0, 1.05f, 0),
                new Vector3(1.65f, 2.1f, .23f), amberMat, doorRoot.transform);
            var door = doorRoot.AddComponent<KeyDoorInteractable>();
            SetRef(door, "requiredKeyItem", key);
            SetRef(door, "doorLeaf", leaf.transform);

            GameObject cameraObject = new GameObject("Main Camera", typeof(Camera), typeof(AudioListener));
            cameraObject.tag = "MainCamera";
            cameraObject.transform.position = new Vector3(0f, 12.5f, -15f);
            cameraObject.transform.rotation = Quaternion.Euler(38f, 0f, 0f);
            Camera camera = cameraObject.GetComponent<Camera>();
            camera.clearFlags = CameraClearFlags.SolidColor;
            camera.backgroundColor = new Color(.06f, .11f, .18f);
            camera.orthographic = true;
            camera.orthographicSize = 7.1f;
            camera.allowHDR = true;
            RenderSettings.ambientMode = UnityEngine.Rendering.AmbientMode.Flat;
            RenderSettings.ambientLight = new Color(.32f, .39f, .48f);

            GameObject sun = new GameObject("Main warm light", typeof(Light));
            sun.transform.rotation = Quaternion.Euler(45f, -35f, 0);
            sun.GetComponent<Light>().type = LightType.Directional;
            sun.GetComponent<Light>().intensity = 1.3f;
            GameObject fill = new GameObject("Training fill light", typeof(Light));
            fill.transform.position = new Vector3(-4, 7, -2);
            fill.GetComponent<Light>().type = LightType.Point;
            fill.GetComponent<Light>().range = 15;
            fill.GetComponent<Light>().intensity = 1.9f;

            GameObject root = new GameObject("HPR Gameplay Suite / integrated controller");
            var controller = root.AddComponent<HprGameplaySuitePlayground>();
            SetRef(controller, "arenaCamera", camera);
            SetRef(controller, "playerRoot", player);
            SetRef(controller, "enemyVisual", enemy);
            SetRef(controller, "lootItem", medkit);
            SetRef(controller, "keyItem", key);
            SetRef(controller, "weaponData", rifle);
            SetRef(controller, "enemyData", raider);
            SetRef(controller, "healAbility", heal);
            SetRef(controller, "pulseAbility", pulse);
            SetRef(controller, "worldRegistry", catalog);
            SetRef(controller, "medkitPickup", medkitStation);
            SetRef(controller, "keyPickup", keyStation);
            SetRef(controller, "demoDoor", door);

            SaveOwnedSamplesOnly();
            if (!EditorSceneManager.SaveScene(scene, Scene))
                throw new InvalidOperationException("Unity failed to save original training arena");
            AssetDatabase.Refresh();
            Debug.Log("HPR Gameplay Suite arena saved at " + Scene);
        }

        /// <summary>
        /// Deliberately opt-in: users can retarget the included demo materials to
        /// the current render pipeline without changing their project settings.
        /// The suite never silently installs packages or edits buyer assets on import.
        /// </summary>
        [MenuItem("Tools/HPR/Gameplay Suite/Adapt Demo Materials to Current Render Pipeline")]
        public static void AdaptDemoMaterials()
        {
            UnityEngine.Rendering.RenderPipelineAsset current =
                UnityEngine.Rendering.GraphicsSettings.currentRenderPipeline;
            Shader target;
            if (current == null)
                target = Shader.Find("Standard");
            else if (current.GetType().Name.Contains("Universal"))
                target = Shader.Find("Universal Render Pipeline/Lit");
            else if (current.GetType().Name.Contains("HDRenderPipeline"))
                target = Shader.Find("HDRP/Lit");
            else
                throw new InvalidOperationException(
                    "The active render pipeline is not Built-in, URP or HDRP. No materials changed.");
            if (target == null || !target.isSupported)
                throw new InvalidOperationException("Required pipeline Lit shader is not installed/supported; no changes made.");
            string[] guids = AssetDatabase.FindAssets("t:Material", new[] { Samples });
            foreach (string guid in guids)
            {
                string path = AssetDatabase.GUIDToAssetPath(guid);
                Material material = AssetDatabase.LoadAssetAtPath<Material>(path);
                if (material == null || material.shader == target) continue;
                Color color = material.HasProperty("_BaseColor") ? material.GetColor("_BaseColor") :
                              material.HasProperty("_Color") ? material.GetColor("_Color") : Color.white;
                float metallic = material.HasProperty("_Metallic") ? material.GetFloat("_Metallic") : 0f;
                float smoothness = material.HasProperty("_Smoothness") ? material.GetFloat("_Smoothness") :
                                   material.HasProperty("_Glossiness") ? material.GetFloat("_Glossiness") : .4f;
                material.shader = target;
                if (material.HasProperty("_BaseColor")) material.SetColor("_BaseColor", color);
                if (material.HasProperty("_Color")) material.SetColor("_Color", color);
                if (material.HasProperty("_Metallic")) material.SetFloat("_Metallic", Mathf.Clamp01(metallic));
                if (material.HasProperty("_Smoothness")) material.SetFloat("_Smoothness", Mathf.Clamp01(smoothness));
                if (material.HasProperty("_Glossiness")) material.SetFloat("_Glossiness", Mathf.Clamp01(smoothness));
                EditorUtility.SetDirty(material);
                // Save only this explicitly adapted HPR-owned sample material.
                AssetDatabase.SaveAssetIfDirty(material);
            }
            Debug.Log("HPR Gameplay Suite adapted its demo materials to " +
                (current == null ? "Built-in" : current.GetType().Name) +
                ". No other project materials, packages or render settings changed.");
        }

        public static void BuildAndExport()
        {
            BuildShowcase(); // first-time build: creates original sample only in an empty project
            ExportExisting();
        }

        /// <summary>Export an existing complete sample without changing any buyer assets.</summary>
        public static void ExportExisting()
        {
            if (AssetDatabase.LoadAssetAtPath<SceneAsset>(Scene) == null ||
                AssetDatabase.LoadAssetAtPath<WeaponData>(Samples + "/DemoRifle.asset") == null ||
                AssetDatabase.LoadAssetAtPath<EnemyData>(Samples + "/DemoRaider.asset") == null)
                throw new InvalidOperationException("Cannot export an incomplete HPR sample project.");
            string archive = Environment.GetEnvironmentVariable("HPR_GAMEPLAY_SUITE_OUTPUT");
            if (string.IsNullOrWhiteSpace(archive))
                throw new InvalidOperationException("HPR_GAMEPLAY_SUITE_OUTPUT is required");
            Directory.CreateDirectory(Path.GetDirectoryName(archive) ?? ".");
#if UNITY_6000_6_OR_NEWER
            UnityEditor.AssetPackage.Package.Export(
                new UnityEditor.AssetPackage.ExportPackageParameters(
                    Root, archive, "", ExportPackageOptions.Recurse));
#else
            AssetDatabase.ExportPackage(Root, archive, ExportPackageOptions.Recurse);
#endif
            if (!File.Exists(archive) || new FileInfo(archive).Length < 4096)
                throw new IOException("Unity did not export the HPR suite");
            Debug.Log("HPR Gameplay Suite candidate built; bytes=" + new FileInfo(archive).Length);
        }
    }
}
#endif
