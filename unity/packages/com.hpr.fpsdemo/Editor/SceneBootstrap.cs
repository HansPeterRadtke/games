using System.Collections.Generic;
using System.IO;
using HPR.Foundation.Utils;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.Rendering;

namespace HPR
{
    public static class SceneBootstrap
    {
        private const string LegacyScenePath = "Assets/Scenes/Main.unity";
        private const string GameplayScenePath = "Assets/Scenes/Gameplay.unity";
        private const string BootstrapScenePath = "Assets/Scenes/Bootstrap.unity";

        public static void EnsureProjectSetup()
        {
            GameplayDataSeeder.EnsureDataAssets();
            Directory.CreateDirectory("Assets/Scenes");
            EnsureBootstrapScene();
            if (!File.Exists(GameplayScenePath))
            {
                if (File.Exists(LegacyScenePath))
                {
                    AssetDatabase.CopyAsset(LegacyScenePath, GameplayScenePath);
                    AssetDatabase.Refresh();
                }
                else
                {
                    CreateScene();
                    return;
                }
            }

            EditorBuildSettings.scenes = new[]
            {
                new EditorBuildSettingsScene(BootstrapScenePath, true),
                new EditorBuildSettingsScene(GameplayScenePath, true)
            };
            EnsureSceneWiring();
        }

        private static void EnsureBootstrapScene()
        {
            if (File.Exists(BootstrapScenePath))
            {
                return;
            }

            var scene = EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);
            var bootstrap = new GameObject("Bootstrap");
            bootstrap.AddComponent<BootstrapLoader>();
            EditorSceneManager.SaveScene(scene, BootstrapScenePath);
            AssetDatabase.SaveAssets();
            AssetDatabase.Refresh();
        }

        public static void CreateScene()
        {
            CreateGameplayScene();
            EnsureBootstrapScene();
        }

        private static void CreateGameplayScene()
        {
            GameplayDataSeeder.EnsureDataAssets();
            Directory.CreateDirectory("Assets/Scenes");
            var scene = EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);
            ConfigureRenderSettings();

            var sharedMaterials = CreateMaterialPalette();
            var allItems = GameplayDataSeeder.LoadAllItems();
            var allConsumables = GameplayDataSeeder.LoadAllConsumables();
            var allAbilities = GameplayDataSeeder.LoadAllAbilities();
            var allSkills = GameplayDataSeeder.LoadAllSkills();
            var allQuests = GameplayDataSeeder.LoadAllQuests();
            var itemLookup = BuildItemLookup(allItems);
            var weaponLoadout = GameplayDataSeeder.LoadDefaultWeapons();

            CreateLighting();
            var world = CreateWorld(sharedMaterials, itemLookup);
            var player = CreatePlayer(weaponLoadout, allItems, allSkills, allAbilities);
            var mapCamera = CreateMapCamera(player.ActorTransform);
            player.GetComponent<PlayerGameplayController>().BindMapCamera(mapCamera.GetComponent<MapCameraFollow>());
            CreateGameSystems(player, mapCamera, world, allQuests, allConsumables);

            EditorBuildSettings.scenes = new[]
            {
                new EditorBuildSettingsScene(BootstrapScenePath, true),
                new EditorBuildSettingsScene(GameplayScenePath, true)
            };

            EditorSceneManager.SaveScene(scene, GameplayScenePath);
            AssetDatabase.SaveAssets();
            AssetDatabase.Refresh();
            Debug.Log($"Created {GameplayScenePath}");
        }

        public static void RecreateDemoScene()
        {
            CreateGameplayScene();
        }

        public static void BuildLinux()
        {
            EnsureProjectSetup();
            Directory.CreateDirectory("Build/Linux");
            var report = BuildPipeline.BuildPlayer(new[] { BootstrapScenePath, GameplayScenePath }, "Build/Linux/FPSDemo.x86_64", BuildTarget.StandaloneLinux64, BuildOptions.StrictMode);
            if (report.summary.result != UnityEditor.Build.Reporting.BuildResult.Succeeded)
            {
                throw new System.Exception($"Build failed: {report.summary.result}");
            }
            Debug.Log("Build succeeded");
        }

        private static void EnsureSceneWiring()
        {
            var scene = EditorSceneManager.OpenScene(GameplayScenePath, OpenSceneMode.Single);
            bool changed = false;

            var playerGo = GameObject.Find("Player");
            var world = GameObject.Find("World")?.transform;
            var mapCamera = GameObject.Find("Map Camera")?.GetComponent<Camera>();
            var systems = GameObject.Find("GameSystems");
            if (playerGo == null || world == null || mapCamera == null || systems == null)
            {
                return;
            }

            var knownItems = GameplayDataSeeder.LoadAllItems();
            var consumables = GameplayDataSeeder.LoadAllConsumables();
            var abilities = GameplayDataSeeder.LoadAllAbilities();
            var skills = GameplayDataSeeder.LoadAllSkills();
            var quests = GameplayDataSeeder.LoadAllQuests();
            var itemLookup = BuildItemLookup(knownItems);
            var loadout = GameplayDataSeeder.LoadDefaultWeapons();
            var sharedMaterials = CreateMaterialPalette();

            changed |= EnsureWorldHierarchy(world);
            changed |= EnsureWorldEntityData(world, itemLookup, sharedMaterials);
            changed |= EnsurePlayerRuntime(playerGo, knownItems, loadout, skills, abilities, mapCamera);
            changed |= EnsureSystemRuntime(systems, playerGo.GetComponent<PlayerActorContext>(), mapCamera, world, quests, consumables);

            if (changed)
            {
                EditorSceneManager.MarkSceneDirty(scene);
                EditorSceneManager.SaveScene(scene);
                AssetDatabase.SaveAssets();
            }
        }

        private static Dictionary<string, ItemData> BuildItemLookup(IEnumerable<ItemData> allItems)
        {
            var lookup = new Dictionary<string, ItemData>();
            foreach (var item in allItems)
            {
                if (item != null && !string.IsNullOrWhiteSpace(item.Id))
                {
                    lookup[item.Id] = item;
                }
            }

            return lookup;
        }

        private static void ConfigureRenderSettings()
        {
            RenderSettings.ambientMode = AmbientMode.Flat;
            RenderSettings.ambientLight = new Color(0.48f, 0.5f, 0.56f);
            RenderSettings.fog = true;
            RenderSettings.fogMode = FogMode.ExponentialSquared;
            RenderSettings.fogDensity = 0.0055f;
            RenderSettings.fogColor = new Color(0.08f, 0.1f, 0.12f);
        }

        private static Dictionary<string, Material> CreateMaterialPalette()
        {
            return new Dictionary<string, Material>
            {
                ["Ground"] = CreateMaterial(new Color(0.18f, 0.2f, 0.22f)),
                ["Wall"] = CreateMaterial(new Color(0.32f, 0.34f, 0.38f)),
                ["Trim"] = CreateMaterial(new Color(0.62f, 0.42f, 0.18f)),
                ["Door"] = CreateMaterial(new Color(0.42f, 0.18f, 0.12f)),
                ["SecurityDoor"] = CreateMaterial(new Color(0.56f, 0.16f, 0.16f)),
                ["BlueDoor"] = CreateMaterial(new Color(0.16f, 0.24f, 0.58f)),
                ["Pickup"] = CreateMaterial(new Color(0.14f, 0.65f, 0.22f)),
                ["KeyRed"] = CreateMaterial(new Color(0.76f, 0.1f, 0.14f)),
                ["KeyBlue"] = CreateMaterial(new Color(0.2f, 0.35f, 0.82f)),
                ["Enemy"] = CreateMaterial(new Color(0.7f, 0.7f, 0.82f)),
                ["EnemyHead"] = CreateMaterial(new Color(0.18f, 0.84f, 0.8f)),
                ["Accent"] = CreateMaterial(new Color(0.18f, 0.56f, 0.78f))
            };
        }

        private static Material CreateMaterial(Color color)
        {
            return new Material(Shader.Find("Standard"))
            {
                color = color
            };
        }

        private static void CreateLighting()
        {
            var lightGo = new GameObject("Directional Light");
            var light = GameObjectUtils.GetOrAddComponent<Light>(lightGo);
            light.type = LightType.Directional;
            light.intensity = 1.18f;
            light.shadows = LightShadows.Soft;
            light.transform.rotation = Quaternion.Euler(48f, -30f, 0f);

            CreatePointLight("Hub Fill", new Vector3(0f, 5f, 0f), new Color(0.68f, 0.78f, 0.95f), 7f, 20f);
            CreatePointLight("Medbay Fill", new Vector3(-18f, 4f, 0f), new Color(0.4f, 1f, 0.45f), 4f, 15f);
            CreatePointLight("Armory Fill", new Vector3(18f, 4f, 0f), new Color(1f, 0.55f, 0.25f), 4f, 15f);
            CreatePointLight("Security Fill", new Vector3(0f, 4f, 18f), new Color(1f, 0.2f, 0.2f), 4f, 15f);
            CreatePointLight("Power Fill", new Vector3(0f, 4f, -18f), new Color(0.25f, 0.4f, 1f), 4f, 15f);
        }

        private static void CreatePointLight(string name, Vector3 position, Color color, float intensity, float range)
        {
            var go = new GameObject(name);
            var light = go.AddComponent<Light>();
            light.type = LightType.Point;
            light.color = color;
            light.intensity = intensity;
            light.range = range;
            go.transform.position = position;
        }

        private static bool EnsurePlayerRuntime(GameObject playerGo, List<ItemData> knownItems, List<WeaponData> loadout, List<SkillNodeData> skills, List<AbilityData> abilities, Camera mapCamera)
        {
            bool changed = false;
            changed |= playerGo.GetComponent<PlayerStats>() == null;
            GameObjectUtils.GetOrAddComponent<PlayerStats>(playerGo);
            changed |= playerGo.GetComponent<PlayerInventory>() == null;
            var inventory = GameObjectUtils.GetOrAddComponent<PlayerInventory>(playerGo);
            changed |= playerGo.GetComponent<WeaponSystem>() == null;
            var weaponSystem = GameObjectUtils.GetOrAddComponent<WeaponSystem>(playerGo);
            changed |= playerGo.GetComponent<SkillTreeComponent>() == null;
            var skillTree = GameObjectUtils.GetOrAddComponent<SkillTreeComponent>(playerGo);
            changed |= playerGo.GetComponent<AbilityRunnerComponent>() == null;
            var abilityRunner = GameObjectUtils.GetOrAddComponent<AbilityRunnerComponent>(playerGo);
            changed |= playerGo.GetComponent<PlayerController>() == null;
            var playerController = GameObjectUtils.GetOrAddComponent<PlayerController>(playerGo);
            changed |= playerGo.GetComponent<PlayerActorContext>() == null;
            var actorContext = GameObjectUtils.GetOrAddComponent<PlayerActorContext>(playerGo);
            changed |= playerGo.GetComponent<PlayerGameplayController>() == null;
            var gameplayController = GameObjectUtils.GetOrAddComponent<PlayerGameplayController>(playerGo);
            changed |= mapCamera.GetComponent<MapCameraFollow>() == null;
            var mapFollow = GameObjectUtils.GetOrAddComponent<MapCameraFollow>(mapCamera.gameObject);

            actorContext.ConfigureKnownItems(knownItems);
            actorContext.ConfigureLoadout(loadout);
            actorContext.ConfigureSkills(skills);
            actorContext.ConfigureAbilities(abilities);
            gameplayController.BindMapCamera(mapFollow);

            EditorUtility.SetDirty(inventory);
            EditorUtility.SetDirty(weaponSystem);
            EditorUtility.SetDirty(skillTree);
            EditorUtility.SetDirty(abilityRunner);
            EditorUtility.SetDirty(playerController);
            EditorUtility.SetDirty(actorContext);
            EditorUtility.SetDirty(gameplayController);
            EditorUtility.SetDirty(mapFollow);
            return changed;
        }

        private static bool EnsureSystemRuntime(GameObject systems, PlayerActorContext player, Camera mapCamera, Transform worldRoot, List<QuestData> quests, List<ConsumableEffectData> consumables)
        {
            bool changed = false;
            changed |= systems.GetComponent<EventManager>() == null;
            var eventManager = GameObjectUtils.GetOrAddComponent<EventManager>(systems);
            changed |= systems.GetComponent<GameStateValidator>() == null;
            var validator = GameObjectUtils.GetOrAddComponent<GameStateValidator>(systems);
            changed |= systems.GetComponent<GameUiController>() == null;
            var ui = GameObjectUtils.GetOrAddComponent<GameUiController>(systems);
            changed |= systems.GetComponent<QuestManager>() == null;
            var questManager = GameObjectUtils.GetOrAddComponent<QuestManager>(systems);
            changed |= systems.GetComponent<GameManager>() == null;
            var manager = GameObjectUtils.GetOrAddComponent<GameManager>(systems);
            changed |= systems.GetComponent<FpsDemoServiceAdapter>() == null;
            var serviceAdapter = GameObjectUtils.GetOrAddComponent<FpsDemoServiceAdapter>(systems);
            changed |= systems.GetComponent<FpsDemoCompositionRoot>() == null;
            var compositionRoot = GameObjectUtils.GetOrAddComponent<FpsDemoCompositionRoot>(systems);
            questManager.ConfigureQuests(quests);
            manager.ConfigureConsumables(consumables);
            compositionRoot.ConfigureSceneReferences(manager, eventManager, validator, questManager, ui, serviceAdapter, player, mapCamera, worldRoot);
            EditorUtility.SetDirty(eventManager);
            EditorUtility.SetDirty(validator);
            EditorUtility.SetDirty(questManager);
            EditorUtility.SetDirty(ui);
            EditorUtility.SetDirty(serviceAdapter);
            EditorUtility.SetDirty(compositionRoot);
            EditorUtility.SetDirty(manager);
            return changed;
        }

        private static bool EnsureWorldEntityData(Transform worldRoot, IReadOnlyDictionary<string, ItemData> items, Dictionary<string, Material> materials)
        {
            bool changed = false;
            changed |= EnsureDialogueNpcPresence(worldRoot, materials);
            changed |= EnsurePickupData(worldRoot, items);
            changed |= EnsureDoorData(worldRoot, items);
            changed |= EnsureEnemyData(worldRoot);
            changed |= EnsureDialogueNpcData(worldRoot);
            return changed;
        }

        private static bool EnsurePickupData(Transform worldRoot, IReadOnlyDictionary<string, ItemData> items)
        {
            bool changed = false;
            foreach (var pickup in worldRoot.GetComponentsInChildren<PickupItem>(true))
            {
                if (pickup == null || string.IsNullOrWhiteSpace(pickup.SaveId))
                {
                    continue;
                }

                if (!TryResolvePickupDefinition(pickup.SaveId, items, out ItemData itemData, out int amount) || itemData == null)
                {
                    continue;
                }

                if (pickup.ItemData == itemData && pickup.Amount == amount)
                {
                    continue;
                }

                pickup.Configure(pickup.SaveId, itemData, amount);
                EditorUtility.SetDirty(pickup);
                changed = true;
            }

            return changed;
        }

        private static bool EnsureDoorData(Transform worldRoot, IReadOnlyDictionary<string, ItemData> items)
        {
            bool changed = false;
            foreach (var door in worldRoot.GetComponentsInChildren<DoorController>(true))
            {
                if (door == null || string.IsNullOrWhiteSpace(door.SaveId))
                {
                    continue;
                }

                ItemData requiredKey = ResolveDoorKeyItem(door.SaveId, items);
                Transform leaf = door.transform.Find("DoorLeaf");
                if (leaf == null)
                {
                    continue;
                }

                door.Configure(door.SaveId, leaf, requiredKey);
                EditorUtility.SetDirty(door);
                changed = true;
            }

            return changed;
        }

        private static bool EnsureEnemyData(Transform worldRoot)
        {
            bool changed = false;
            foreach (var enemy in worldRoot.GetComponentsInChildren<EnemyAgent>(true))
            {
                if (enemy == null || string.IsNullOrWhiteSpace(enemy.SaveId))
                {
                    continue;
                }

                EnemyData data = GameplayDataSeeder.LoadEnemy($"enemy_{enemy.SaveId}");
                if (data == null && enemy.SaveId == "medbay_intruder")
                {
                    data = GameplayDataSeeder.LoadEnemy("enemy_medbay_intruder");
                }

                if (data == null)
                {
                    continue;
                }

                Transform patrolA = worldRoot.Find($"EnemyRoot/{enemy.SaveId}_PatrolA");
                Transform patrolB = worldRoot.Find($"EnemyRoot/{enemy.SaveId}_PatrolB");
                Transform muzzle = enemy.transform.Find("Muzzle");
                if (patrolA == null || patrolB == null || muzzle == null)
                {
                    continue;
                }

                enemy.Configure(enemy.SaveId, data, patrolA, patrolB, muzzle);
                EditorUtility.SetDirty(enemy);
                changed = true;
            }

            return changed;
        }

        private static bool EnsureDialogueNpcData(Transform worldRoot)
        {
            bool changed = false;
            foreach (var npc in worldRoot.GetComponentsInChildren<DialogueNpcInteractable>(true))
            {
                if (npc == null || string.IsNullOrWhiteSpace(npc.NpcId))
                {
                    continue;
                }

                DialogueData dialogue = npc.NpcId switch
                {
                    "npc_echo" => GameplayDataSeeder.LoadDialogue("dialogue_echo_briefing"),
                    "npc_vale" => GameplayDataSeeder.LoadDialogue("dialogue_vale_supplies"),
                    _ => null
                };

                if (dialogue == null)
                {
                    continue;
                }

                string displayName = npc.NpcId switch
                {
                    "npc_echo" => "Commander Echo",
                    "npc_vale" => "Quartermaster Vale",
                    _ => npc.DisplayName
                };

                npc.Configure(npc.NpcId, displayName, dialogue);
                npc.ConfigureVariants(BuildDialogueVariants(npc.NpcId));
                EditorUtility.SetDirty(npc);
                changed = true;
            }

            return changed;
        }

        private static bool EnsureDialogueNpcPresence(Transform worldRoot, Dictionary<string, Material> materials)
        {
            if (worldRoot == null || materials == null)
            {
                return false;
            }

            var npcRoot = EnsureChild(EnsureChild(worldRoot, "PropsRoot"), "NpcRoot");
            bool changed = false;
            if (npcRoot.Find("npc_echo") == null)
            {
                CreateDialogueNpc(npcRoot, "npc_echo", "Commander Echo", GameplayDataSeeder.LoadDialogue("dialogue_echo_briefing"), new Vector3(3.5f, 0f, -2.5f), new Vector3(0f, 210f, 0f), materials["Accent"]);
                changed = true;
            }

            if (npcRoot.Find("npc_vale") == null)
            {
                CreateDialogueNpc(npcRoot, "npc_vale", "Quartermaster Vale", GameplayDataSeeder.LoadDialogue("dialogue_vale_supplies"), new Vector3(-4.2f, 0f, -3.2f), new Vector3(0f, 140f, 0f), materials["Pickup"]);
                changed = true;
            }

            return changed;
        }

        private static bool TryResolvePickupDefinition(string saveId, IReadOnlyDictionary<string, ItemData> items, out ItemData itemData, out int amount)
        {
            itemData = null;
            amount = 1;
            switch (saveId)
            {
                case "pickup_red_key":
                    return items.TryGetValue("key_red", out itemData);
                case "pickup_blue_key":
                    return items.TryGetValue("key_blue", out itemData);
                case "pickup_shotgun_ammo":
                    return items.TryGetValue("ammo_scatter_shot", out itemData);
                case "pickup_launcher_ammo":
                    return items.TryGetValue("ammo_arc_launcher", out itemData);
                case "pickup_pistol_ammo":
                    return items.TryGetValue("ammo_pulse_pistol", out itemData);
                case "pickup_needler_ammo":
                    return items.TryGetValue("ammo_needler", out itemData);
                case "pickup_medkit":
                    return items.TryGetValue("item_medkit", out itemData);
                case "pickup_armor":
                    return items.TryGetValue("item_armor_patch", out itemData);
                default:
                    return false;
            }
        }

        private static ItemData ResolveDoorKeyItem(string saveId, IReadOnlyDictionary<string, ItemData> items)
        {
            switch (saveId)
            {
                case "door_north":
                    items.TryGetValue("key_red", out ItemData redKey);
                    return redKey;
                case "door_south":
                    items.TryGetValue("key_blue", out ItemData blueKey);
                    return blueKey;
                default:
                    return null;
            }
        }

        private static Transform CreateWorld(Dictionary<string, Material> materials, IReadOnlyDictionary<string, ItemData> items)
        {
            var world = new GameObject("World").transform;
            var environmentRoot = EnsureChild(world, "EnvironmentRoot");
            var enemyRoot = EnsureChild(world, "EnemyRoot");
            var propsRoot = EnsureChild(world, "PropsRoot");

            CreateBlock(environmentRoot, "Ground", new Vector3(0f, -0.5f, 0f), new Vector3(62f, 1f, 62f), materials["Ground"]);
            CreateBlock(environmentRoot, "PerimeterNorth", new Vector3(0f, 2f, 31f), new Vector3(62f, 4f, 1f), materials["Wall"]);
            CreateBlock(environmentRoot, "PerimeterSouth", new Vector3(0f, 2f, -31f), new Vector3(62f, 4f, 1f), materials["Wall"]);
            CreateBlock(environmentRoot, "PerimeterEast", new Vector3(31f, 2f, 0f), new Vector3(1f, 4f, 62f), materials["Wall"]);
            CreateBlock(environmentRoot, "PerimeterWest", new Vector3(-31f, 2f, 0f), new Vector3(1f, 4f, 62f), materials["Wall"]);

            CreateBlock(environmentRoot, "HubNorthLeft", new Vector3(-7f, 2f, 10f), new Vector3(6f, 4f, 1f), materials["Wall"]);
            CreateBlock(environmentRoot, "HubNorthRight", new Vector3(7f, 2f, 10f), new Vector3(6f, 4f, 1f), materials["Wall"]);
            CreateBlock(environmentRoot, "HubSouthLeft", new Vector3(-7f, 2f, -10f), new Vector3(6f, 4f, 1f), materials["Wall"]);
            CreateBlock(environmentRoot, "HubSouthRight", new Vector3(7f, 2f, -10f), new Vector3(6f, 4f, 1f), materials["Wall"]);
            CreateBlock(environmentRoot, "HubEastTop", new Vector3(10f, 2f, 7f), new Vector3(1f, 4f, 6f), materials["Wall"]);
            CreateBlock(environmentRoot, "HubEastBottom", new Vector3(10f, 2f, -7f), new Vector3(1f, 4f, 6f), materials["Wall"]);
            CreateBlock(environmentRoot, "HubWestTop", new Vector3(-10f, 2f, 7f), new Vector3(1f, 4f, 6f), materials["Wall"]);
            CreateBlock(environmentRoot, "HubWestBottom", new Vector3(-10f, 2f, -7f), new Vector3(1f, 4f, 6f), materials["Wall"]);

            CreateBlock(environmentRoot, "NorthRoomFront", new Vector3(0f, 2f, 30f), new Vector3(22f, 4f, 1f), materials["Wall"]);
            CreateBlock(environmentRoot, "SouthRoomFront", new Vector3(0f, 2f, -30f), new Vector3(22f, 4f, 1f), materials["Wall"]);
            CreateBlock(environmentRoot, "EastRoomFront", new Vector3(30f, 2f, 0f), new Vector3(1f, 4f, 22f), materials["Wall"]);
            CreateBlock(environmentRoot, "WestRoomFront", new Vector3(-30f, 2f, 0f), new Vector3(1f, 4f, 22f), materials["Wall"]);

            CreateDoor(environmentRoot, "door_east", new Vector3(10f, 0f, 0f), Vector3.zero, null, materials["Door"]);
            CreateDoor(environmentRoot, "door_west", new Vector3(-10f, 0f, 0f), new Vector3(0f, 180f, 0f), null, materials["Door"]);
            CreateDoor(environmentRoot, "door_north", new Vector3(0f, 0f, 10f), new Vector3(0f, 90f, 0f), items["key_red"], materials["SecurityDoor"]);
            CreateDoor(environmentRoot, "door_south", new Vector3(0f, 0f, -10f), new Vector3(0f, -90f, 0f), items["key_blue"], materials["BlueDoor"]);

            CreateCoverAndDecor(propsRoot, materials);
            CreatePickups(propsRoot, materials, items);
            CreateDialogueNpcs(propsRoot, materials);
            CreateEnemies(enemyRoot, materials);
            return world;
        }

        private static void CreateCoverAndDecor(Transform parent, Dictionary<string, Material> materials)
        {
            Vector3[] cratePositions =
            {
                new Vector3(15f, 0.75f, -5f), new Vector3(18f, 0.75f, 4f), new Vector3(-18f, 0.75f, -4f),
                new Vector3(-15f, 0.75f, 5f), new Vector3(4f, 0.75f, 17f), new Vector3(-4f, 0.75f, -17f)
            };
            for (int i = 0; i < cratePositions.Length; i++)
            {
                CreateBlock(parent, $"Crate_{i}", cratePositions[i], new Vector3(1.5f, 1.5f, 1.5f), materials["Trim"]);
            }

            CreateDynamicProp(parent, "PhysicsBarrel_A", PrimitiveType.Cylinder, new Vector3(2.5f, 0.85f, 15.5f), new Vector3(0.7f, 0.85f, 0.7f), materials["Accent"], 18f);
            CreateDynamicProp(parent, "PhysicsCrate_B", PrimitiveType.Cube, new Vector3(-3.5f, 0.8f, -14.5f), new Vector3(1.1f, 1.1f, 1.1f), materials["Trim"], 12f);
            CreateDynamicProp(parent, "PhysicsCrate_C", PrimitiveType.Cube, new Vector3(13.5f, 0.8f, 13.5f), new Vector3(1.2f, 1.2f, 1.2f), materials["Door"], 14f);

            Vector3[] pillarPositions =
            {
                new Vector3(5f, 1.5f, 5f), new Vector3(-5f, 1.5f, 5f), new Vector3(5f, 1.5f, -5f), new Vector3(-5f, 1.5f, -5f)
            };
            for (int i = 0; i < pillarPositions.Length; i++)
            {
                CreateCylinder(parent, $"HubPillar_{i}", pillarPositions[i], new Vector3(1.3f, 3f, 1.3f), materials["Accent"]);
            }
        }

        private static void CreatePickups(Transform parent, Dictionary<string, Material> materials, IReadOnlyDictionary<string, ItemData> items)
        {
            CreatePickup(parent, "pickup_red_key", new Vector3(19f, 0.7f, 0f), items["key_red"], 1, materials["KeyRed"], PrimitiveType.Cube, new Vector3(0.5f, 0.15f, 0.9f));
            CreatePickup(parent, "pickup_shotgun_ammo", new Vector3(16f, 0.6f, -3f), items["ammo_scatter_shot"], 1, materials["Pickup"], PrimitiveType.Cube, new Vector3(0.5f, 0.5f, 0.5f));
            CreatePickup(parent, "pickup_launcher_ammo", new Vector3(20f, 0.6f, 3f), items["ammo_arc_launcher"], 1, materials["Pickup"], PrimitiveType.Cube, new Vector3(0.5f, 0.5f, 0.5f));
            CreatePickup(parent, "pickup_medkit", new Vector3(-19f, 0.6f, 0f), items["item_medkit"], 1, materials["Pickup"], PrimitiveType.Sphere, new Vector3(0.7f, 0.7f, 0.7f));
            CreatePickup(parent, "pickup_armor", new Vector3(-16f, 0.6f, -3f), items["item_armor_patch"], 1, materials["Pickup"], PrimitiveType.Capsule, new Vector3(0.4f, 0.7f, 0.4f));
            CreatePickup(parent, "pickup_blue_key", new Vector3(0f, 0.7f, -21f), items["key_blue"], 1, materials["KeyBlue"], PrimitiveType.Cube, new Vector3(0.5f, 0.15f, 0.9f));
            CreatePickup(parent, "pickup_pistol_ammo", new Vector3(0f, 0.6f, -17f), items["ammo_pulse_pistol"], 1, materials["Pickup"], PrimitiveType.Cube, new Vector3(0.5f, 0.5f, 0.5f));
            CreatePickup(parent, "pickup_needler_ammo", new Vector3(0f, 0.6f, 20f), items["ammo_needler"], 1, materials["Pickup"], PrimitiveType.Cube, new Vector3(0.5f, 0.5f, 0.5f));
        }

        private static void CreateEnemies(Transform parent, Dictionary<string, Material> materials)
        {
            CreateEnemy(parent, "sentry_hub", GameplayDataSeeder.LoadEnemy("enemy_sentry_hub"), new Vector3(0f, 0.2f, 4f), new Vector3(-4f, 0.2f, 4f), new Vector3(4f, 0.2f, 4f), materials);
            CreateEnemy(parent, "sweeper_armory", GameplayDataSeeder.LoadEnemy("enemy_sweeper_armory"), new Vector3(18f, 0.2f, -6f), new Vector3(14f, 0.2f, -6f), new Vector3(22f, 0.2f, -1f), materials);
            CreateEnemy(parent, "medbay_intruder", GameplayDataSeeder.LoadEnemy("enemy_medbay_intruder"), new Vector3(-18f, 0.2f, 6f), new Vector3(-22f, 0.2f, 1f), new Vector3(-14f, 0.2f, 6f), materials);
            CreateEnemy(parent, "security_guard", GameplayDataSeeder.LoadEnemy("enemy_security_guard"), new Vector3(0f, 0.2f, 20f), new Vector3(-4f, 0.2f, 18f), new Vector3(4f, 0.2f, 22f), materials);
            CreateEnemy(parent, "power_walker", GameplayDataSeeder.LoadEnemy("enemy_power_walker"), new Vector3(0f, 0.2f, -18f), new Vector3(-5f, 0.2f, -22f), new Vector3(5f, 0.2f, -16f), materials);
        }

        private static void CreateDialogueNpcs(Transform parent, Dictionary<string, Material> materials)
        {
            var npcRoot = EnsureChild(parent, "NpcRoot");
            CreateDialogueNpc(npcRoot, "npc_echo", "Commander Echo", GameplayDataSeeder.LoadDialogue("dialogue_echo_briefing"), new Vector3(3.5f, 0f, -2.5f), new Vector3(0f, 210f, 0f), materials["Accent"]);
            CreateDialogueNpc(npcRoot, "npc_vale", "Quartermaster Vale", GameplayDataSeeder.LoadDialogue("dialogue_vale_supplies"), new Vector3(-4.2f, 0f, -3.2f), new Vector3(0f, 140f, 0f), materials["Pickup"]);
        }

        private static PlayerActorContext CreatePlayer(List<WeaponData> weaponLoadout, List<ItemData> knownItems, List<SkillNodeData> skills, List<AbilityData> abilities)
        {
            var player = new GameObject("Player");
            player.transform.position = new Vector3(0f, 1.3f, -1.5f);
            player.transform.rotation = Quaternion.Euler(0f, 0f, 0f);
            var controller = player.AddComponent<CharacterController>();
            controller.height = 1.8f;
            controller.radius = 0.35f;
            controller.center = new Vector3(0f, 0.9f, 0f);

            player.AddComponent<PlayerStats>();
            var inventory = player.AddComponent<PlayerInventory>();
            var weaponSystem = player.AddComponent<WeaponSystem>();
            var skillTree = player.AddComponent<SkillTreeComponent>();
            var abilityRunner = player.AddComponent<AbilityRunnerComponent>();
            player.AddComponent<PlayerController>();
            var actorContext = player.AddComponent<PlayerActorContext>();
            player.AddComponent<PlayerGameplayController>();
            actorContext.ConfigureKnownItems(knownItems);
            actorContext.ConfigureLoadout(weaponLoadout);
            actorContext.ConfigureSkills(skills);
            actorContext.ConfigureAbilities(abilities);

            var cameraGo = new GameObject("Main Camera");
            cameraGo.tag = "MainCamera";
            cameraGo.transform.SetParent(player.transform, false);
            cameraGo.transform.ResetLocalPose();
            cameraGo.transform.localPosition = new Vector3(0f, 0.66f, 0f);
            var camera = cameraGo.AddComponent<Camera>();
            camera.fieldOfView = 75f;
            camera.nearClipPlane = 0.03f;
            camera.farClipPlane = 120f;
            cameraGo.AddComponent<AudioListener>();

            var flashlightGo = new GameObject("Flashlight");
            flashlightGo.transform.SetParent(cameraGo.transform, false);
            flashlightGo.transform.localPosition = new Vector3(0.18f, -0.08f, 0.25f);
            var flashlight = flashlightGo.AddComponent<Light>();
            flashlight.type = LightType.Spot;
            flashlight.range = 25f;
            flashlight.intensity = 3.4f;
            flashlight.spotAngle = 48f;
            flashlight.enabled = false;

            return actorContext;
        }

        private static Camera CreateMapCamera(Transform target)
        {
            var mapGo = new GameObject("Map Camera");
            var camera = mapGo.AddComponent<Camera>();
            camera.orthographic = true;
            camera.orthographicSize = 26f;
            camera.clearFlags = CameraClearFlags.SolidColor;
            camera.backgroundColor = new Color(0.04f, 0.04f, 0.05f, 1f);
            camera.cullingMask = ~0;
            camera.depth = -5f;
            var follow = mapGo.AddComponent<MapCameraFollow>();
            follow.SetTarget(target);
            return camera;
        }

        private static GameManager CreateGameSystems(PlayerActorContext player, Camera mapCamera, Transform worldRoot, List<QuestData> quests, List<ConsumableEffectData> consumables)
        {
            var systems = new GameObject("GameSystems");
            var eventManager = systems.AddComponent<EventManager>();
            var ui = systems.AddComponent<GameUiController>();
            var validator = systems.AddComponent<GameStateValidator>();
            var questManager = systems.AddComponent<QuestManager>();
            questManager.ConfigureQuests(quests);
            var manager = systems.AddComponent<GameManager>();
            var serviceAdapter = systems.AddComponent<FpsDemoServiceAdapter>();
            var compositionRoot = systems.AddComponent<FpsDemoCompositionRoot>();
            manager.ConfigureConsumables(consumables);
            compositionRoot.ConfigureSceneReferences(manager, eventManager, validator, questManager, ui, serviceAdapter, player, mapCamera, worldRoot);
            return manager;
        }

        private static DoorController CreateDoor(Transform parent, string saveId, Vector3 position, Vector3 euler, ItemData requiredKeyItem, Material material)
        {
            var rotation = Quaternion.Euler(euler);
            var frameTop = CreateBlock(parent, $"{saveId}_FrameTop", position + rotation * new Vector3(0f, 3.6f, 0f), new Vector3(3.2f, 0.4f, 1f), material);
            var frameLeft = CreateBlock(parent, $"{saveId}_FrameLeft", position + rotation * new Vector3(-1.35f, 1.8f, 0f), new Vector3(0.4f, 3.6f, 1f), material);
            var frameRight = CreateBlock(parent, $"{saveId}_FrameRight", position + rotation * new Vector3(1.35f, 1.8f, 0f), new Vector3(0.4f, 3.6f, 1f), material);
            frameTop.transform.rotation = rotation;
            frameLeft.transform.rotation = rotation;
            frameRight.transform.rotation = rotation;

            var pivot = new GameObject($"Door_{saveId}");
            pivot.transform.SetParent(parent, false);
            pivot.transform.position = position;
            pivot.transform.eulerAngles = euler;

            var leafRoot = new GameObject("DoorLeaf");
            leafRoot.transform.SetParent(pivot.transform, false);
            leafRoot.transform.localPosition = new Vector3(-1f, 0f, 0f);
            CreateBlock(leafRoot.transform, "LeafMesh", new Vector3(1f, 1.6f, 0f), new Vector3(2f, 3.2f, 0.35f), material);
            var controller = pivot.AddComponent<DoorController>();
            controller.Configure(saveId, leafRoot.transform, requiredKeyItem);
            return controller;
        }

        private static PickupItem CreatePickup(Transform parent, string saveId, Vector3 position, ItemData data, int amount, Material material, PrimitiveType primitive, Vector3 scale)
        {
            var pickup = GameObject.CreatePrimitive(primitive);
            pickup.name = saveId;
            pickup.transform.SetParent(parent, false);
            pickup.transform.position = position;
            pickup.transform.localScale = scale;
            pickup.GetComponent<Renderer>().sharedMaterial = material;
            var pickupItem = pickup.AddComponent<PickupItem>();
            pickupItem.Configure(saveId, data, amount);
            return pickupItem;
        }

        private static DialogueNpcInteractable CreateDialogueNpc(Transform parent, string npcId, string displayName, DialogueData dialogueData, Vector3 position, Vector3 euler, Material material)
        {
            var root = new GameObject(npcId);
            root.transform.SetParent(parent, false);
            root.transform.position = position;
            root.transform.eulerAngles = euler;

            var capsule = GameObject.CreatePrimitive(PrimitiveType.Capsule);
            capsule.name = "Body";
            capsule.transform.SetParent(root.transform, false);
            capsule.transform.localPosition = new Vector3(0f, 0.9f, 0f);
            capsule.transform.localScale = new Vector3(0.8f, 0.9f, 0.8f);
            capsule.GetComponent<Renderer>().sharedMaterial = material;

            var head = GameObject.CreatePrimitive(PrimitiveType.Sphere);
            head.name = "Head";
            head.transform.SetParent(root.transform, false);
            head.transform.localPosition = new Vector3(0f, 1.85f, 0f);
            head.transform.localScale = new Vector3(0.42f, 0.42f, 0.42f);
            head.GetComponent<Renderer>().sharedMaterial = material;

            var marker = GameObject.CreatePrimitive(PrimitiveType.Cylinder);
            marker.name = "Marker";
            marker.transform.SetParent(root.transform, false);
            marker.transform.localPosition = new Vector3(0f, 2.45f, 0f);
            marker.transform.localScale = new Vector3(0.12f, 0.25f, 0.12f);
            marker.GetComponent<Renderer>().sharedMaterial = material;
            Object.DestroyImmediate(marker.GetComponent<Collider>());

            var interactable = root.AddComponent<DialogueNpcInteractable>();
            interactable.Configure(npcId, displayName, dialogueData);
            interactable.ConfigureVariants(BuildDialogueVariants(npcId));
            return interactable;
        }

        private static List<DialogueNpcInteractable.DialogueVariantRule> BuildDialogueVariants(string npcId)
        {
            switch (npcId)
            {
                case "npc_echo":
                    return new List<DialogueNpcInteractable.DialogueVariantRule>
                    {
                        new DialogueNpcInteractable.DialogueVariantRule
                        {
                            Label = "Completed",
                            Dialogue = GameplayDataSeeder.LoadDialogue("dialogue_echo_complete"),
                            RequiredCompletedQuestId = "quest_security_sweep",
                            Priority = 40
                        },
                        new DialogueNpcInteractable.DialogueVariantRule
                        {
                            Label = "Reminder",
                            Dialogue = GameplayDataSeeder.LoadDialogue("dialogue_echo_reminder"),
                            RequiredActiveQuestId = "quest_security_sweep",
                            Priority = 20
                        }
                    };

                case "npc_vale":
                    return new List<DialogueNpcInteractable.DialogueVariantRule>
                    {
                        new DialogueNpcInteractable.DialogueVariantRule
                        {
                            Label = "Completed",
                            Dialogue = GameplayDataSeeder.LoadDialogue("dialogue_vale_complete"),
                            RequiredCompletedQuestId = "quest_supply_recovery",
                            Priority = 60
                        },
                        new DialogueNpcInteractable.DialogueVariantRule
                        {
                            Label = "TurnIn",
                            Dialogue = GameplayDataSeeder.LoadDialogue("dialogue_vale_turnin"),
                            RequiredActiveQuestId = "quest_supply_recovery",
                            RequiredObjectiveQuestId = "quest_supply_recovery",
                            RequiredObjectiveId = "collect_medkit",
                            Priority = 40
                        },
                        new DialogueNpcInteractable.DialogueVariantRule
                        {
                            Label = "Reminder",
                            Dialogue = GameplayDataSeeder.LoadDialogue("dialogue_vale_waiting"),
                            RequiredActiveQuestId = "quest_supply_recovery",
                            Priority = 20
                        }
                    };
            }

            return new List<DialogueNpcInteractable.DialogueVariantRule>();
        }

        private static EnemyAgent CreateEnemy(Transform parent, string saveId, EnemyData data, Vector3 position, Vector3 patrolA, Vector3 patrolB, Dictionary<string, Material> materials)
        {
            var root = new GameObject(saveId);
            root.transform.SetParent(parent, false);
            root.transform.position = position;
            var controller = root.AddComponent<CharacterController>();
            controller.height = 1.8f;
            controller.radius = 0.4f;
            controller.center = new Vector3(0f, 0.9f, 0f);
            var enemy = root.AddComponent<EnemyAgent>();

            var body = GameObject.CreatePrimitive(PrimitiveType.Capsule);
            body.name = "Body";
            body.transform.SetParent(root.transform, false);
            body.transform.localPosition = new Vector3(0f, 0.9f, 0f);
            body.transform.localScale = new Vector3(0.8f, 0.9f, 0.8f);
            body.GetComponent<Renderer>().sharedMaterial = materials["Enemy"];
            Object.DestroyImmediate(body.GetComponent<Collider>());

            var head = GameObject.CreatePrimitive(PrimitiveType.Sphere);
            head.name = "Head";
            head.transform.SetParent(root.transform, false);
            head.transform.localPosition = new Vector3(0f, 1.75f, 0f);
            head.transform.localScale = new Vector3(0.5f, 0.5f, 0.5f);
            head.GetComponent<Renderer>().sharedMaterial = materials["EnemyHead"];
            Object.DestroyImmediate(head.GetComponent<Collider>());

            var muzzle = new GameObject("Muzzle");
            muzzle.transform.SetParent(root.transform, false);
            muzzle.transform.localPosition = new Vector3(0f, 1.15f, 0.45f);

            var waypointA = new GameObject($"{saveId}_PatrolA");
            waypointA.transform.SetParent(parent, false);
            waypointA.transform.position = patrolA;
            var waypointB = new GameObject($"{saveId}_PatrolB");
            waypointB.transform.SetParent(parent, false);
            waypointB.transform.position = patrolB;
            enemy.Configure(saveId, data, waypointA.transform, waypointB.transform, muzzle.transform);
            return enemy;
        }

        private static GameObject CreateDynamicProp(Transform parent, string name, PrimitiveType primitive, Vector3 position, Vector3 scale, Material material, float mass)
        {
            var go = primitive == PrimitiveType.Cylinder
                ? CreateCylinder(parent, name, position, scale, material)
                : CreateBlock(parent, name, position, scale, material);
            var rigidbody = go.AddComponent<Rigidbody>();
            rigidbody.mass = mass;
            rigidbody.interpolation = RigidbodyInterpolation.Interpolate;
            rigidbody.collisionDetectionMode = CollisionDetectionMode.ContinuousDynamic;
            return go;
        }

        private static GameObject CreateBlock(Transform parent, string name, Vector3 position, Vector3 scale, Material material)
        {
            var go = GameObject.CreatePrimitive(PrimitiveType.Cube);
            go.name = name;
            go.transform.SetParent(parent, false);
            go.transform.localPosition = position;
            go.transform.localScale = scale;
            go.GetComponent<Renderer>().sharedMaterial = material;
            return go;
        }

        private static GameObject CreateCylinder(Transform parent, string name, Vector3 position, Vector3 scale, Material material)
        {
            var go = GameObject.CreatePrimitive(PrimitiveType.Cylinder);
            go.name = name;
            go.transform.SetParent(parent, false);
            go.transform.localPosition = position;
            go.transform.localScale = scale;
            go.GetComponent<Renderer>().sharedMaterial = material;
            return go;
        }

        private static bool EnsureWorldHierarchy(Transform world)
        {
            if (world == null)
            {
                return false;
            }

            bool changed = false;
            var environmentRoot = EnsureChild(world, "EnvironmentRoot");
            var enemyRoot = EnsureChild(world, "EnemyRoot");
            var propsRoot = EnsureChild(world, "PropsRoot");

            var children = new List<Transform>();
            foreach (Transform child in world)
            {
                if (child == environmentRoot || child == enemyRoot || child == propsRoot)
                {
                    continue;
                }

                children.Add(child);
            }

            foreach (Transform child in children)
            {
                Transform targetParent = ResolveWorldContainer(child, environmentRoot, enemyRoot, propsRoot);
                if (child.parent == targetParent)
                {
                    continue;
                }

                child.SetParent(targetParent, true);
                changed = true;
            }

            return changed;
        }

        private static Transform ResolveWorldContainer(Transform child, Transform environmentRoot, Transform enemyRoot, Transform propsRoot)
        {
            if (child.GetComponent<EnemyAgent>() != null || child.name.Contains("_Patrol"))
            {
                return enemyRoot;
            }

            if (child.GetComponent<PickupItem>() != null || child.GetComponent<DialogueNpcInteractable>() != null || child.GetComponent<Rigidbody>() != null || child.name.StartsWith("pickup_") || child.name.Contains("ThirdPartyArt"))
            {
                return propsRoot;
            }

            return environmentRoot;
        }

        private static Transform EnsureChild(Transform parent, string name)
        {
            var child = parent.Find(name);
            if (child != null)
            {
                return child;
            }

            var go = new GameObject(name);
            go.transform.SetParent(parent, false);
            return go.transform;
        }
    }
}
