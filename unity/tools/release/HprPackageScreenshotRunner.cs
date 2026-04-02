#nullable enable
using System;
using System.Collections.Generic;
using System.IO;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.UI;

namespace HPR
{
    public static class HprPackageScreenshotRunner
    {
        private static readonly Dictionary<string, Palette> Palettes = new Dictionary<string, Palette>
        {
            ["com.hpr.eventbus"] = new Palette(new Color(0.10f, 0.13f, 0.17f), new Color(0.20f, 0.79f, 0.74f), new Color(0.95f, 0.64f, 0.22f)),
            ["com.hpr.composition"] = new Palette(new Color(0.10f, 0.12f, 0.16f), new Color(0.36f, 0.70f, 0.95f), new Color(0.93f, 0.75f, 0.32f)),
            ["com.hpr.save"] = new Palette(new Color(0.09f, 0.14f, 0.15f), new Color(0.19f, 0.80f, 0.63f), new Color(0.36f, 0.93f, 0.87f)),
            ["com.hpr.stats"] = new Palette(new Color(0.13f, 0.10f, 0.12f), new Color(0.92f, 0.36f, 0.40f), new Color(0.25f, 0.82f, 0.94f)),
            ["com.hpr.inventory"] = new Palette(new Color(0.13f, 0.11f, 0.09f), new Color(0.94f, 0.63f, 0.20f), new Color(0.32f, 0.86f, 0.48f)),
            ["com.hpr.interaction"] = new Palette(new Color(0.10f, 0.11f, 0.13f), new Color(0.95f, 0.58f, 0.24f), new Color(0.27f, 0.80f, 0.95f)),
            ["com.hpr.abilities"] = new Palette(new Color(0.08f, 0.12f, 0.12f), new Color(0.30f, 0.86f, 0.52f), new Color(0.98f, 0.62f, 0.25f)),
            ["com.hpr.weapons"] = new Palette(new Color(0.12f, 0.11f, 0.11f), new Color(0.88f, 0.33f, 0.28f), new Color(0.79f, 0.84f, 0.90f)),
            ["com.hpr.ai"] = new Palette(new Color(0.12f, 0.10f, 0.11f), new Color(0.90f, 0.40f, 0.26f), new Color(0.93f, 0.77f, 0.29f)),
            ["com.hpr.world"] = new Palette(new Color(0.11f, 0.10f, 0.08f), new Color(0.83f, 0.70f, 0.32f), new Color(0.43f, 0.73f, 0.46f)),
        };

        public static void CapturePackageSetFromEnvironment()
        {
            string? packageName = Environment.GetEnvironmentVariable("HPR_SCREENSHOT_PACKAGE");
            string? outputDir = Environment.GetEnvironmentVariable("HPR_SCREENSHOT_OUTPUT_DIR");
            string? widthText = Environment.GetEnvironmentVariable("HPR_SCREENSHOT_WIDTH");
            string? heightText = Environment.GetEnvironmentVariable("HPR_SCREENSHOT_HEIGHT");

            if (string.IsNullOrWhiteSpace(packageName) || string.IsNullOrWhiteSpace(outputDir))
            {
                Debug.LogError("Missing HPR_SCREENSHOT_PACKAGE or HPR_SCREENSHOT_OUTPUT_DIR environment variable.");
                EditorApplication.Exit(1);
                return;
            }

            int width = ParseDimension(widthText, 1920);
            int height = ParseDimension(heightText, 1080);
            string[] names = { "01_overview.png", "02_workflow.png", "03_details.png" };

            try
            {
                Directory.CreateDirectory(outputDir);
                for (int shotIndex = 0; shotIndex < names.Length; shotIndex++)
                {
                    EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);
                    ShotContext context = CreateContext(packageName, width, height);
                    BuildShot(context, shotIndex);
                    byte[] png = Render(context.Camera, width, height);
                    string outputPath = Path.Combine(outputDir, names[shotIndex]);
                    File.WriteAllBytes(outputPath, png);
                    Debug.Log($"Saved screenshot to {outputPath}");
                }

                AssetDatabase.Refresh();
                EditorApplication.Exit(0);
            }
            catch (Exception ex)
            {
                Debug.LogException(ex);
                EditorApplication.Exit(1);
            }
        }

        public static void CaptureFromEnvironment()
        {
            CapturePackageSetFromEnvironment();
        }

        private static ShotContext CreateContext(string packageName, int width, int height)
        {
            Palette palette = Palettes.TryGetValue(packageName, out Palette stored)
                ? stored
                : new Palette(new Color(0.10f, 0.11f, 0.14f), new Color(0.28f, 0.65f, 0.95f), new Color(0.94f, 0.67f, 0.24f));

            Camera camera = new GameObject("Screenshot Camera", typeof(Camera)).GetComponent<Camera>();
            camera.clearFlags = CameraClearFlags.SolidColor;
            camera.backgroundColor = palette.Background;
            camera.orthographic = true;
            camera.orthographicSize = 540f;
            camera.nearClipPlane = -100f;
            camera.farClipPlane = 100f;
            camera.transform.position = new Vector3(960f, 540f, -10f);

            Canvas canvas = new GameObject("Canvas", typeof(Canvas), typeof(CanvasScaler), typeof(GraphicRaycaster)).GetComponent<Canvas>();
            canvas.renderMode = RenderMode.ScreenSpaceCamera;
            canvas.worldCamera = camera;
            canvas.planeDistance = 1f;

            CanvasScaler scaler = canvas.GetComponent<CanvasScaler>();
            scaler.uiScaleMode = CanvasScaler.ScaleMode.ScaleWithScreenSize;
            scaler.referenceResolution = new Vector2(width, height);
            scaler.matchWidthOrHeight = 0.5f;

            RectTransform root = canvas.GetComponent<RectTransform>();
            root.sizeDelta = new Vector2(width, height);

            Font font = Resources.GetBuiltinResource<Font>("LegacyRuntime.ttf");
            if (font == null)
            {
                throw new InvalidOperationException("Built-in LegacyRuntime font not available.");
            }

            CreateImage(root, "Background", new Vector2(width * 0.5f, height * 0.5f), new Vector2(width, height), palette.Background);
            CreateDecor(root, width, height, palette);

            return new ShotContext(packageName, palette, camera, root, font);
        }

        private static void BuildShot(ShotContext context, int shotIndex)
        {
            switch (context.PackageName)
            {
                case "com.hpr.eventbus":
                    BuildEventBus(context, shotIndex);
                    break;
                case "com.hpr.composition":
                    BuildComposition(context, shotIndex);
                    break;
                case "com.hpr.save":
                    BuildSave(context, shotIndex);
                    break;
                case "com.hpr.stats":
                    BuildStats(context, shotIndex);
                    break;
                case "com.hpr.inventory":
                    BuildInventory(context, shotIndex);
                    break;
                case "com.hpr.interaction":
                    BuildInteraction(context, shotIndex);
                    break;
                case "com.hpr.abilities":
                    BuildAbilities(context, shotIndex);
                    break;
                case "com.hpr.weapons":
                    BuildWeapons(context, shotIndex);
                    break;
                case "com.hpr.ai":
                    BuildAi(context, shotIndex);
                    break;
                case "com.hpr.world":
                    BuildWorld(context, shotIndex);
                    break;
                default:
                    BuildGenericFallback(context, shotIndex);
                    break;
            }
        }

        private static void BuildEventBus(ShotContext context, int shotIndex)
        {
            if (shotIndex == 0)
            {
                BuildTriCardShot(
                    context,
                    "HPR Typed Event Bus",
                    "Strongly typed publish/subscribe routing without scene or manager coupling.",
                    new CardData("Publishers", new[] { "Gameplay, UI, and tools publish typed payloads.", "No hard references to listeners.", "Scene-safe and headless-friendly." }),
                    new CardData("Event transport", new[] { "Pure C# EventBus plus Unity EventManager adapter.", "Exact-type and base-type dispatch.", "Explicit unsubscribe support." }),
                    new CardData("Subscribers", new[] { "Multiple listeners react to the same event contract.", "Optional IEventBusSource adapter for scene wiring.", "No GameManager dependency." }));
                CreateTagRow(context, new[] { "Pure C# core", "Unity adapter optional", "Launch-now" });
                return;
            }

            if (shotIndex == 1)
            {
                BuildFlowShot(
                    context,
                    "Publish once, fan out many",
                    "The package exists to route typed events across unrelated systems.",
                    new[]
                    {
                        new FlowNodeData("Publisher", "DemoPingEvent", context.Palette.AccentA),
                        new FlowNodeData("Event bus", "IEventBus / EventManager", context.Palette.AccentB),
                        new FlowNodeData("Subscriber A", "HUD / feedback", context.Palette.AccentA),
                        new FlowNodeData("Subscriber B", "Gameplay logic", context.Palette.AccentB),
                    },
                    new[] { "Disposable subscriptions", "Base-type dispatch", "No hidden singletons" });
                return;
            }

            BuildDetailShot(
                context,
                "Scene adapter and headless usage",
                "The same API works in editor tests, headless runners, and regular Unity scenes.",
                new CardData("Headless demo", new[] { "EventBus can be instantiated without a scene.", "Used by the repo headless validation.", "Good fit for isolated services." }),
                new CardData("Unity scene", new[] { "EventManager exposes the same API through a MonoBehaviour.", "EventBusSourceAdapter supports explicit inspector wiring.", "No parent lookup hacks." }),
                new[] { "API: Publish<T>", "API: Subscribe<T>", "API: Clear()" },
                new[] { "No replay buffer", "No persistence layer", "No ordering guarantees beyond registration order" });
        }

        private static void BuildComposition(ShotContext context, int shotIndex)
        {
            if (shotIndex == 0)
            {
                BuildTriCardShot(
                    context,
                    "HPR Composition Root",
                    "Explicit registration, initialization, ticking, and disposal for modular Unity runtime systems.",
                    new CardData("CompositionRoot", new[] { "Owns the lifecycle entry point.", "No reflection magic.", "Works in headless validation." }),
                    new CardData("ServiceRegistry", new[] { "Registers concrete services explicitly.", "Dependency resolution is deliberate.", "Great for package-safe composition." }),
                    new CardData("Service contracts", new[] { "IInitializable", "IUpdatableService", "IServiceResolver and IServiceRegistry" }));
                CreateTagRow(context, new[] { "Explicit wiring", "Headless-ready", "Launch-now" });
                return;
            }

            if (shotIndex == 1)
            {
                BuildFlowShot(
                    context,
                    "Registration to runtime lifecycle",
                    "The sample is about predictable orchestration, not a hidden framework core.",
                    new[]
                    {
                        new FlowNodeData("Register", "CounterService + SummaryService", context.Palette.AccentA),
                        new FlowNodeData("Initialize", "Resolve dependencies once", context.Palette.AccentB),
                        new FlowNodeData("Tick", "Run explicit updates", context.Palette.AccentA),
                        new FlowNodeData("Dispose", "Shut down cleanly", context.Palette.AccentB),
                    },
                    new[] { "No static global registry", "Thin scene adapters only", "Deterministic test path" });
                return;
            }

            BuildDetailShot(
                context,
                "Package-safe composition",
                "The launch value is architectural clarity: packages register services, the game composes them.",
                new CardData("Where it fits", new[] { "Bootstrap code", "Game-mode composition", "Editor headless test harnesses" }),
                new CardData("What it does not do", new[] { "No DI container conventions", "No auto-discovery", "No scene search fallback" }),
                new[] { "Resolve<T>()", "Register(instance)", "Tick(deltaTime)" },
                new[] { "No scopes", "No reflection injection", "No serialization layer" });
        }

        private static void BuildSave(ShotContext context, int shotIndex)
        {
            if (shotIndex == 0)
            {
                BuildTriCardShot(
                    context,
                    "HPR Save Contracts & Snapshots",
                    "Capture and restore runtime state without hard-coding a save backend into your gameplay code.",
                    new CardData("Capture", new[] { "SaveData snapshot objects.", "Runtime values plus transform state.", "No forced persistence backend." }),
                    new CardData("Mutate", new[] { "Gameplay can continue changing objects.", "Restore path remains explicit.", "Good for clean demos and tests." }),
                    new CardData("Restore", new[] { "State data round-trips back into the entity.", "Position, rotation, and active state can recover.", "Simple contracts stay reusable." }));
                CreateTagRow(context, new[] { "Snapshot contracts", "Backend-agnostic", "Launch-now" });
                return;
            }

            if (shotIndex == 1)
            {
                BuildFlowShot(
                    context,
                    "Capture -> mutate -> restore",
                    "The package is intentionally narrow: contracts and sample entity flow, not a monolithic save manager.",
                    new[]
                    {
                        new FlowNodeData("Entity", "value=7 / health=42", context.Palette.AccentA),
                        new FlowNodeData("CaptureState", "SaveEntityData", context.Palette.AccentB),
                        new FlowNodeData("Runtime change", "value=99 / moved", context.Palette.AccentA),
                        new FlowNodeData("RestoreState", "original snapshot reapplied", context.Palette.AccentB),
                    },
                    new[] { "Transform state", "Value state", "Active-state restore" });
                return;
            }

            BuildDetailShot(
                context,
                "For teams that want save contracts, not a giant framework",
                "Best fit when you already know where persistence belongs and only need reusable snapshot contracts.",
                new CardData("What buyers get", new[] { "SaveData base contract", "Sample entity round-trip", "Standalone validation demo" }),
                new CardData("What stays out", new[] { "Cloud sync", "Encryption", "Slot UI", "Serialization storage backend" }),
                new[] { "CaptureState()", "RestoreState(data)", "Custom SaveData types" },
                new[] { "Not a full save product", "No cross-scene manager", "No storage policy" });
        }

        private static void BuildStats(ShotContext context, int shotIndex)
        {
            if (shotIndex == 0)
            {
                BuildTriCardShot(
                    context,
                    "HPR Character Stats & Damage",
                    "Health, stamina, damage, healing, and runtime max-value bonuses in a small reusable runtime package.",
                    new CardData("Combat values", new[] { "Health and stamina tracked together.", "Damage and healing paths included.", "Reset flow for demos and tests." }),
                    new CardData("Runtime bonuses", new[] { "Effective max-health and max-stamina handling.", "Clamping respects active bonuses.", "Fixes validated in clean projects." }),
                    new CardData("Damage integration", new[] { "DamageEvent integration via event bus.", "Damageable proxy support.", "No project-specific actor classes." }));
                CreateTagRow(context, new[] { "Damage + heal", "Stamina flow", "Launch-now" });
                return;
            }

            if (shotIndex == 1)
            {
                BuildFlowShot(
                    context,
                    "Damage, healing, spend, recover",
                    "The demo covers the four runtime loops buyers actually care about.",
                    new[]
                    {
                        new FlowNodeData("DamageEvent", "Publish hit payload", context.Palette.AccentA),
                        new FlowNodeData("ActorStats", "Apply damage / clamp", context.Palette.AccentB),
                        new FlowNodeData("Heal", "Restore toward max", context.Palette.AccentA),
                        new FlowNodeData("Stamina", "Spend and regenerate", context.Palette.AccentB),
                    },
                    new[] { "Damage proxy", "Effective max values", "Event-driven integration" });
                return;
            }

            BuildDetailShot(
                context,
                "Concrete stat behavior, not just data shells",
                "The product is strongest because it already demonstrates runtime behavior instead of only exposing ScriptableObjects.",
                new CardData("Runtime hooks", new[] { "ConsumeStamina()", "RegenerateStamina()", "SetRuntimeBonuses()" }),
                new CardData("Non-goals", new[] { "No RPG skill tree", "No buffs/debuff stacks", "No character UI layer" }),
                new[] { "Health bars ready", "Damageable target proxy", "Resettable demo" },
                new[] { "No networking", "No combat VFX", "No turn-based layer" });
        }

        private static void BuildInventory(ShotContext context, int shotIndex)
        {
            if (shotIndex == 0)
            {
                BuildTriCardShot(
                    context,
                    "HPR Inventory System Core",
                    "A reusable inventory runtime for item definitions, counts, ammo, keys, and consumables without game-specific baggage.",
                    new CardData("Item definitions", new[] { "ItemData assets with ids, display names, and item types.", "Ammo, keys, and consumables covered.", "Package-owned sample assets included." }),
                    new CardData("InventoryComponent", new[] { "Known items configured explicitly.", "Quantities tracked per item id.", "Ammo state bug fixed in package runtime." }),
                    new CardData("Queries and events", new[] { "Counts and lookups are runtime-safe.", "Works with interaction pickups and abilities packages.", "Clean project demo included." }));
                CreateTagRow(context, new[] { "ItemData assets", "Counts + ammo", "Launch-now" });
                return;
            }

            if (shotIndex == 1)
            {
                BuildFlowShot(
                    context,
                    "Pickup to stored quantity",
                    "The package matters because it owns the count logic, not just the item definitions.",
                    new[]
                    {
                        new FlowNodeData("ItemData", "Health potion / key / ammo", context.Palette.AccentA),
                        new FlowNodeData("InventoryComponent", "Register known items", context.Palette.AccentB),
                        new FlowNodeData("Add item", "+1 potion / +12 ammo", context.Palette.AccentA),
                        new FlowNodeData("Runtime query", "Has key? Ammo count?", context.Palette.AccentB),
                    },
                    new[] { "Explicit known item list", "Persistent quantities", "Works standalone" });
                return;
            }

            BuildDetailShot(
                context,
                "What ships with the package",
                "The strongest buyer story is a lean runtime they can wire into their own pickup, UI, or save code.",
                new CardData("Included sample items", new[] { "Health Potion", "Rifle Ammo", "Silver Key" }),
                new CardData("Non-goals", new[] { "No inventory UI skin", "No drag-and-drop grid", "No economy backend" }),
                new[] { "Ammo", "Consumables", "Keys" },
                new[] { "No equipment slots", "No crafting", "No vendor system" });
        }

        private static void BuildInteraction(ShotContext context, int shotIndex)
        {
            if (shotIndex == 0)
            {
                BuildTriCardShot(
                    context,
                    "HPR Interaction Toolkit",
                    "Sensor-driven pickup and door interaction built around explicit bindings, not hierarchy assumptions.",
                    new CardData("InteractionSensor", new[] { "Explicit source camera binding.", "No parent service discovery.", "Package-safe runtime setup." }),
                    new CardData("Pickup interactables", new[] { "Inventory item pickups included.", "Works with medkits and keys in the sample.", "Event bus integration stays explicit." }),
                    new CardData("Door interaction", new[] { "Key-gated door sample included.", "Proxy binding fixes already validated.", "Good showcase package for first-wave launch." }));
                CreateTagRow(context, new[] { "Pickups", "Doors", "Launch-now" });
                return;
            }

            if (shotIndex == 1)
            {
                BuildFlowShot(
                    context,
                    "Actor sensor -> interactable -> result",
                    "The demo scene is strongest when it shows a concrete interaction chain: see, use, unlock.",
                    new[]
                    {
                        new FlowNodeData("Actor", "Capsule + camera sensor", context.Palette.AccentA),
                        new FlowNodeData("Medkit pickup", "InventoryPickupInteractable", context.Palette.AccentB),
                        new FlowNodeData("Bronze key", "Second pickup path", context.Palette.AccentA),
                        new FlowNodeData("Door", "KeyDoorInteractable unlocks", context.Palette.AccentB),
                    },
                    new[] { "No hidden parent lookup", "Explicit camera source", "Inventory-friendly" });
                return;
            }

            BuildDetailShot(
                context,
                "Interaction package boundaries",
                "The launch value comes from ready-made interaction primitives that still stay modular.",
                new CardData("Included runtime pieces", new[] { "InteractionSensor", "SimpleInteractionActor", "InventoryPickupInteractable", "KeyDoorInteractable" }),
                new CardData("Non-goals", new[] { "No full dialogue system", "No cinematic interaction UI", "No animation graph integration" }),
                new[] { "Proxy bindings", "Inventory hooks", "Package-safe demos" },
                new[] { "No quest scripting", "No network sync", "No controller bindings" });
        }

        private static void BuildAbilities(ShotContext context, int shotIndex)
        {
            if (shotIndex == 0)
            {
                BuildTriCardShot(
                    context,
                    "HPR Ability Data & Runtime",
                    "Ability definitions, effect assets, cooldowns, and a reusable runtime component for self and area abilities.",
                    new CardData("AbilityData assets", new[] { "Cooldown, cost, target type, status text.", "Theme colors and descriptions included.", "Repair and shock sample abilities ship in-package." }),
                    new CardData("AbilityRunnerComponent", new[] { "Configured abilities and unlock tracking.", "Startup unlock-id regression fixed.", "No runtime parent lookup remains." }),
                    new CardData("Effect assets", new[] { "Heal and area damage examples.", "Resource pool hookup stays explicit.", "Stats package integrates cleanly." }));
                CreateTagRow(context, new[] { "Cooldowns", "Self + area", "Launch-now" });
                return;
            }

            if (shotIndex == 1)
            {
                BuildFlowShot(
                    context,
                    "Ability asset -> effect asset -> runtime result",
                    "The package is saleable because buyers can author abilities without rewriting the runtime glue.",
                    new[]
                    {
                        new FlowNodeData("Repair Pulse", "Self-target heal", context.Palette.AccentA),
                        new FlowNodeData("Ability runner", "Cooldown / cost / unlock", context.Palette.AccentB),
                        new FlowNodeData("Shock Pulse", "Area-target damage", context.Palette.AccentA),
                        new FlowNodeData("Target dummy", "Stats package receives effect", context.Palette.AccentB),
                    },
                    new[] { "AbilityData", "AbilityEffectData", "Resource pool integration" });
                return;
            }

            BuildDetailShot(
                context,
                "A reusable ability layer, not a whole combat game",
                "This is one of the strongest first-wave products because the package boundary is clear and the demo already proves runtime behavior.",
                new CardData("Included sample content", new[] { "Repair Pulse", "Shock Pulse", "Repair Field effect", "Shock Ring effect" }),
                new CardData("Non-goals", new[] { "No animation system", "No VFX graph integration", "No multiplayer authority layer" }),
                new[] { "Unlock tracking", "Cooldown handling", "Theme-colored assets" },
                new[] { "No talent tree", "No combo system", "No cast bars" });
        }

        private static void BuildWeapons(ShotContext context, int shotIndex)
        {
            if (shotIndex == 0)
            {
                BuildTriCardShot(
                    context,
                    "HPR Weapon Data Kit",
                    "Reusable weapon definition assets for hitscan, scatter, ammo, and preview geometry with a clean Unity package boundary.",
                    new CardData("WeaponData assets", new[] { "Damage, range, ammo, fire mode, and preview shape.", "Rifle and scattergun samples included.", "Good fit for data-driven shooter prototypes." }),
                    new CardData("Fire mode support", new[] { "Hitscan", "Shotgun/scatter", "Projectile-capable fields available" }),
                    new CardData("Current product limit", new[] { "No full runtime controller in this package.", "Best sold later or alongside gameplay packages.", "Storefront story is weaker than first-wave packages." }));
                CreateTagRow(context, new[] { "Data-driven", "Second wave", "Bundle candidate" });
                return;
            }

            if (shotIndex == 1)
            {
                BuildFlowShot(
                    context,
                    "Weapon data authored once, consumed anywhere",
                    "This package is strongest as a data-definition layer paired with a runtime shooter controller.",
                    new[]
                    {
                        new FlowNodeData("Demo Rifle", "18 dmg / 64 range", context.Palette.AccentA),
                        new FlowNodeData("WeaponData", "fire mode + ammo + preview", context.Palette.AccentB),
                        new FlowNodeData("Demo Scattergun", "7 pellets / 11 dmg", context.Palette.AccentA),
                        new FlowNodeData("Runtime consumer", "game-specific firing code", context.Palette.AccentB),
                    },
                    new[] { "Hitscan fields", "Scatter fields", "Preview geometry" });
                return;
            }

            BuildDetailShot(
                context,
                "Recommendation: launch after the systems wave",
                "The package works technically, but it reads as a data companion rather than a standalone marquee product.",
                new CardData("Sell later as", new[] { "Weapon definition pack", "Shooter systems companion", "Bundle add-on" }),
                new CardData("Non-goals", new[] { "No recoil system", "No muzzle flash/VFX", "No runtime input/controller layer" }),
                new[] { "Range", "Damage", "Ammo / pellets" },
                new[] { "No equip flow", "No reload animation", "No project-specific UI" });
        }

        private static void BuildAi(ShotContext context, int shotIndex)
        {
            if (shotIndex == 0)
            {
                BuildTriCardShot(
                    context,
                    "HPR Enemy Archetypes",
                    "Enemy data assets for chase, stationary attack, melee, and ranged behaviors with clear archetype fields.",
                    new CardData("EnemyData assets", new[] { "Health, move speed, chase range, attack range, damage.", "Raider and sentry samples ship with the package.", "Visual preview scale is authored per archetype." }),
                    new CardData("Behavior archetypes", new[] { "Aggressive chase", "Stationary attack", "Melee and ranged attack styles" }),
                    new CardData("Current product limit", new[] { "No full nav/pathfinding runtime shipped here.", "Best positioned as second-wave or bundle content.", "Needs stronger gameplay wrapper for top-tier storefront clarity." }));
                CreateTagRow(context, new[] { "Archetype data", "Second wave", "Bundle candidate" });
                return;
            }

            if (shotIndex == 1)
            {
                BuildFlowShot(
                    context,
                    "Archetype data drives combat behavior",
                    "The package is valuable to teams that already own the runtime controller and need clean enemy data assets.",
                    new[]
                    {
                        new FlowNodeData("Raider", "Aggressive chase / melee", context.Palette.AccentA),
                        new FlowNodeData("EnemyData", "ranges, speeds, damage", context.Palette.AccentB),
                        new FlowNodeData("Sentry", "Stationary / ranged", context.Palette.AccentA),
                        new FlowNodeData("Runtime consumer", "AI controller reads fields", context.Palette.AccentB),
                    },
                    new[] { "Chase range", "Attack range", "Damage profile" });
                return;
            }

            BuildDetailShot(
                context,
                "Recommendation: strengthen the runtime story before first-wave launch",
                "Technically solid, but the current standalone value proposition is narrower than the first-wave packages.",
                new CardData("Sell later as", new[] { "Enemy archetype add-on", "Combat data companion", "Bundle component" }),
                new CardData("Non-goals", new[] { "No navigation", "No behavior trees", "No animation/locomotion package" }),
                new[] { "Raider", "Sentry", "Melee / ranged" },
                new[] { "No patrol graphs", "No senses package", "No spawner system" });
        }

        private static void BuildWorld(ShotContext context, int shotIndex)
        {
            if (shotIndex == 0)
            {
                BuildTriCardShot(
                    context,
                    "HPR World Asset Registry",
                    "Asset metadata and registry contracts for world props, materials, scale defaults, and package-safe catalog lookups.",
                    new CardData("AssetMetadata", new[] { "Asset id, display name, type, material, scale.", "Crate and lamp samples ship in-package.", "Good fit for data-driven prop registries." }),
                    new CardData("AssetRegistry", new[] { "Central lookup asset for reusable world entries.", "Lightweight and explicit.", "Works cleanly in isolated projects." }),
                    new CardData("Current product limit", new[] { "Too thin for a first-wave standalone SKU.", "Best as a supporting package or bundle component.", "Needs a larger world-building story to lead a listing." }));
                CreateTagRow(context, new[] { "Registry data", "Bundle only", "Support package" });
                return;
            }

            if (shotIndex == 1)
            {
                BuildFlowShot(
                    context,
                    "Metadata -> registry -> consuming tools",
                    "This package makes most sense inside a broader world-authoring workflow.",
                    new[]
                    {
                        new FlowNodeData("Crate metadata", "prop / wood / 1.2 scale", context.Palette.AccentA),
                        new FlowNodeData("AssetRegistry", "shared catalog asset", context.Palette.AccentB),
                        new FlowNodeData("Lamp metadata", "decoration / metal / 1.8 scale", context.Palette.AccentA),
                        new FlowNodeData("Consumer", "editor or runtime lookup", context.Palette.AccentB),
                    },
                    new[] { "Type tags", "Material tags", "Default scale" });
                return;
            }

            BuildDetailShot(
                context,
                "Recommendation: keep as bundle support, not first-wave standalone",
                "The code is clean and sale-prepped, but the buyer-facing value is stronger inside a larger world-building offer.",
                new CardData("Best commercial use", new[] { "Bundle component", "Supporting registry layer", "Companion to import/placement tooling" }),
                new CardData("Non-goals", new[] { "No prop placement system", "No world streaming", "No authoring UI beyond the sample registry" }),
                new[] { "Registry lookup", "Metadata assets", "Demo props" },
                new[] { "No placement rules", "No procedural generation", "No scene integration" });
        }

        private static void BuildGenericFallback(ShotContext context, int shotIndex)
        {
            BuildTriCardShot(
                context,
                context.PackageName,
                "Generated storefront screenshot fallback.",
                new CardData("Overview", new[] { "Package screenshot generation needs a package-specific layout." }),
                new CardData("Workflow", new[] { "This fallback should not ship." }),
                new CardData("Details", new[] { $"Shot {shotIndex + 1}" }));
        }

        private static void BuildTriCardShot(ShotContext context, string title, string subtitle, CardData left, CardData middle, CardData right)
        {
            CreateHeader(context, title, subtitle);
            CreateCard(context, left, new Vector2(360f, 590f), new Vector2(440f, 360f), context.Palette.AccentA);
            CreateCard(context, middle, new Vector2(960f, 590f), new Vector2(440f, 360f), context.Palette.AccentB);
            CreateCard(context, right, new Vector2(1560f, 590f), new Vector2(440f, 360f), context.Palette.AccentA);
            CreateFooterBand(context, "Built from the current repo state and regenerated automatically.");
        }

        private static void BuildFlowShot(ShotContext context, string title, string subtitle, FlowNodeData[] nodes, string[] footerBullets)
        {
            CreateHeader(context, title, subtitle);

            float[] xs = { 240f, 680f, 1240f, 1680f };
            for (int i = 0; i < nodes.Length; i++)
            {
                CreateFlowNode(context, nodes[i], new Vector2(xs[i], 610f), new Vector2(300f, 180f));
                if (i < nodes.Length - 1)
                {
                    CreateArrow(context.Root, new Vector2(xs[i] + 150f, 610f), new Vector2(xs[i + 1] - 150f, 610f), context.Palette.TextMuted, 10f);
                }
            }

            CreateWideCard(context, new Vector2(960f, 250f), new Vector2(1560f, 220f), "Why this screenshot matters", footerBullets, context.Palette.AccentB);
            CreateFooterBand(context, "All connectors and labels are generated from sale-prep tooling.");
        }

        private static void BuildDetailShot(ShotContext context, string title, string subtitle, CardData left, CardData right, string[] chips, string[] limits)
        {
            CreateHeader(context, title, subtitle);
            CreateCard(context, left, new Vector2(520f, 560f), new Vector2(620f, 430f), context.Palette.AccentA);
            CreateCard(context, right, new Vector2(1400f, 560f), new Vector2(620f, 430f), context.Palette.AccentB);
            CreateChipStrip(context, new Vector2(960f, 220f), chips, context.Palette.AccentA);
            CreateWideCard(context, new Vector2(960f, 120f), new Vector2(1560f, 120f), "Non-goals buyers should know", limits, context.Palette.AccentB, 20);
            CreateFooterBand(context, "Storefront positioning stays explicit about what the package does and does not include.");
        }

        private static void CreateHeader(ShotContext context, string title, string subtitle)
        {
            CreateText(context.Root, "Title", title, new Vector2(190f, -44f), new Vector2(1500f, 90f), 54, FontStyle.Bold, TextAnchor.MiddleLeft, Color.white, new Vector2(0f, 1f), new Vector2(0f, 1f));
            CreateText(context.Root, "Subtitle", subtitle, new Vector2(190f, -108f), new Vector2(1500f, 64f), 24, FontStyle.Normal, TextAnchor.MiddleLeft, context.Palette.TextMuted, new Vector2(0f, 1f), new Vector2(0f, 1f));
            RectTransform badge = CreatePanel(context.Root, "PackageBadge", new Vector2(-52f, -44f), new Vector2(280f, 54f), WithAlpha(context.Palette.AccentA, 0.24f), new Vector2(1f, 1f), new Vector2(1f, 1f));
            CreateText(badge, "BadgeText", context.PackageName, new Vector2(0f, 0f), new Vector2(252f, 42f), 20, FontStyle.Bold, TextAnchor.MiddleCenter, Color.white);
        }

        private static void CreateCard(ShotContext context, CardData data, Vector2 center, Vector2 size, Color accent)
        {
            RectTransform panel = CreatePanel(context.Root, data.Title, center, size, WithAlpha(Color.black, 0.26f));
            CreateImage(panel, "AccentRail", new Vector2(10f, size.y - 48f), new Vector2(12f, size.y - 52f), accent, new Vector2(0f, 1f), new Vector2(0f, 1f));
            CreateText(panel, "Header", data.Title, new Vector2(42f, -38f), new Vector2(size.x - 72f, 48f), 30, FontStyle.Bold, TextAnchor.MiddleLeft, Color.white, new Vector2(0f, 1f), new Vector2(0f, 1f));
            CreateText(panel, "Bullets", FormatBullets(data.Bullets), new Vector2(42f, -98f), new Vector2(size.x - 72f, size.y - 130f), 22, FontStyle.Normal, TextAnchor.UpperLeft, context.Palette.TextMuted, new Vector2(0f, 1f), new Vector2(0f, 1f));
        }

        private static void CreateWideCard(ShotContext context, Vector2 center, Vector2 size, string title, string[] bullets, Color accent, int bodyFontSize = 24)
        {
            RectTransform panel = CreatePanel(context.Root, title, center, size, WithAlpha(Color.black, 0.24f));
            CreateImage(panel, "AccentBar", new Vector2(size.x * 0.5f, size.y - 8f), new Vector2(size.x - 48f, 10f), accent, new Vector2(0.5f, 1f), new Vector2(0.5f, 1f));
            CreateText(panel, "Header", title, new Vector2(36f, -34f), new Vector2(size.x - 72f, 42f), 28, FontStyle.Bold, TextAnchor.MiddleLeft, Color.white, new Vector2(0f, 1f), new Vector2(0f, 1f));
            CreateText(panel, "Bullets", FormatBullets(bullets), new Vector2(36f, -78f), new Vector2(size.x - 72f, size.y - 96f), bodyFontSize, FontStyle.Normal, TextAnchor.UpperLeft, Color.white, new Vector2(0f, 1f), new Vector2(0f, 1f));
        }

        private static void CreateFlowNode(ShotContext context, FlowNodeData data, Vector2 center, Vector2 size)
        {
            RectTransform panel = CreatePanel(context.Root, data.Title, center, size, WithAlpha(Color.black, 0.26f));
            CreateImage(panel, "Badge", new Vector2(44f, -34f), new Vector2(54f, 54f), data.Accent, new Vector2(0f, 1f), new Vector2(0f, 1f));
            CreateText(panel, "Header", data.Title, new Vector2(112f, -34f), new Vector2(size.x - 128f, 42f), 28, FontStyle.Bold, TextAnchor.MiddleLeft, Color.white, new Vector2(0f, 1f), new Vector2(0f, 1f));
            CreateText(panel, "Body", data.Body, new Vector2(24f, -96f), new Vector2(size.x - 48f, size.y - 120f), 22, FontStyle.Normal, TextAnchor.UpperLeft, context.Palette.TextMuted, new Vector2(0f, 1f), new Vector2(0f, 1f));
        }

        private static void CreateChipStrip(ShotContext context, Vector2 center, string[] chips, Color accent)
        {
            float totalWidth = chips.Length * 220f + Mathf.Max(0, chips.Length - 1) * 22f;
            float startX = center.x - totalWidth * 0.5f + 110f;
            for (int i = 0; i < chips.Length; i++)
            {
                RectTransform chip = CreatePanel(context.Root, $"Chip{i}", new Vector2(startX + i * 242f, center.y), new Vector2(220f, 64f), WithAlpha(accent, 0.18f));
                CreateText(chip, "Text", chips[i], Vector2.zero, new Vector2(200f, 48f), 22, FontStyle.Bold, TextAnchor.MiddleCenter, Color.white);
            }
        }

        private static void CreateTagRow(ShotContext context, string[] tags)
        {
            float totalWidth = tags.Length * 210f + Mathf.Max(0, tags.Length - 1) * 18f;
            float startX = 960f - totalWidth * 0.5f + 105f;
            for (int i = 0; i < tags.Length; i++)
            {
                RectTransform chip = CreatePanel(context.Root, $"Tag{i}", new Vector2(startX + i * 228f, 270f), new Vector2(210f, 56f), WithAlpha(context.Palette.AccentB, 0.16f));
                CreateText(chip, "Text", tags[i], Vector2.zero, new Vector2(190f, 40f), 20, FontStyle.Bold, TextAnchor.MiddleCenter, Color.white);
            }
        }

        private static void CreateFooterBand(ShotContext context, string message)
        {
            RectTransform band = CreatePanel(context.Root, "Footer", new Vector2(960f, 44f), new Vector2(1880f, 52f), WithAlpha(Color.black, 0.18f));
            CreateText(band, "FooterText", message, Vector2.zero, new Vector2(1820f, 36f), 18, FontStyle.Normal, TextAnchor.MiddleCenter, context.Palette.TextMuted);
        }

        private static void CreateDecor(RectTransform root, int width, int height, Palette palette)
        {
            CreateImage(root, "DecorA", new Vector2(width * 0.18f, height * 0.82f), new Vector2(420f, 420f), WithAlpha(palette.AccentA, 0.05f));
            CreateImage(root, "DecorB", new Vector2(width * 0.82f, height * 0.22f), new Vector2(520f, 520f), WithAlpha(palette.AccentB, 0.05f));
            CreateImage(root, "Band", new Vector2(width * 0.5f, height * 0.5f), new Vector2(width + 80f, 8f), WithAlpha(Color.white, 0.04f));
            for (int i = 0; i < 4; i++)
            {
                CreateImage(root, $"Grid{i}", new Vector2(120f + i * 420f, 540f), new Vector2(2f, 860f), WithAlpha(Color.white, 0.03f));
            }
        }

        private static RectTransform CreatePanel(Transform parent, string name, Vector2 center, Vector2 size, Color color)
        {
            return CreatePanel(parent, name, center, size, color, new Vector2(0.5f, 0.5f), new Vector2(0.5f, 0.5f));
        }

        private static RectTransform CreatePanel(Transform parent, string name, Vector2 center, Vector2 size, Color color, Vector2 anchorMin, Vector2 anchorMax)
        {
            RectTransform rect = CreateRect(parent, name, center, size, anchorMin, anchorMax);
            Image image = rect.gameObject.AddComponent<Image>();
            image.color = color;
            return rect;
        }

        private static Image CreateImage(Transform parent, string name, Vector2 center, Vector2 size, Color color)
        {
            return CreateImage(parent, name, center, size, color, new Vector2(0.5f, 0.5f), new Vector2(0.5f, 0.5f));
        }

        private static Image CreateImage(Transform parent, string name, Vector2 anchoredPosition, Vector2 size, Color color, Vector2 anchorMin, Vector2 anchorMax)
        {
            RectTransform rect = CreateRect(parent, name, anchoredPosition, size, anchorMin, anchorMax);
            Image image = rect.gameObject.AddComponent<Image>();
            image.color = color;
            return image;
        }

        private static Text CreateText(Transform parent, string name, string value, Vector2 anchoredPosition, Vector2 size, int fontSize, FontStyle fontStyle, TextAnchor anchor, Color color)
        {
            return CreateText(parent, name, value, anchoredPosition, size, fontSize, fontStyle, anchor, color, new Vector2(0.5f, 0.5f), new Vector2(0.5f, 0.5f));
        }

        private static Text CreateText(Transform parent, string name, string value, Vector2 anchoredPosition, Vector2 size, int fontSize, FontStyle fontStyle, TextAnchor anchor, Color color, Vector2 anchorMin, Vector2 anchorMax)
        {
            RectTransform rect = CreateRect(parent, name, anchoredPosition, size, anchorMin, anchorMax);
            Text text = rect.gameObject.AddComponent<Text>();
            text.font = Resources.GetBuiltinResource<Font>("LegacyRuntime.ttf");
            text.text = value;
            text.fontSize = fontSize;
            text.fontStyle = fontStyle;
            text.alignment = anchor;
            text.color = color;
            text.horizontalOverflow = HorizontalWrapMode.Wrap;
            text.verticalOverflow = VerticalWrapMode.Overflow;
            return text;
        }

        private static RectTransform CreateRect(Transform parent, string name, Vector2 anchoredPosition, Vector2 size, Vector2 anchorMin, Vector2 anchorMax)
        {
            GameObject go = new GameObject(name, typeof(RectTransform));
            go.transform.SetParent(parent, false);
            RectTransform rect = go.GetComponent<RectTransform>();
            rect.anchorMin = anchorMin;
            rect.anchorMax = anchorMax;
            rect.pivot = anchorMin == anchorMax ? anchorMin : new Vector2(0.5f, 0.5f);
            if (parent is RectTransform parentRect && parent.GetComponent<Canvas>() != null && anchorMin == new Vector2(0.5f, 0.5f) && anchorMax == new Vector2(0.5f, 0.5f))
            {
                anchoredPosition -= parentRect.sizeDelta * 0.5f;
            }

            rect.anchoredPosition = anchoredPosition;
            rect.sizeDelta = size;
            return rect;
        }

        private static void CreateArrow(Transform parent, Vector2 start, Vector2 end, Color color, float thickness)
        {
            Vector2 direction = end - start;
            float length = direction.magnitude;
            float angle = Mathf.Atan2(direction.y, direction.x) * Mathf.Rad2Deg;

            RectTransform line = CreateRect(parent, "ArrowLine", (start + end) * 0.5f, new Vector2(length, thickness), new Vector2(0.5f, 0.5f), new Vector2(0.5f, 0.5f));
            line.localRotation = Quaternion.Euler(0f, 0f, angle);
            Image image = line.gameObject.AddComponent<Image>();
            image.color = color;

            RectTransform head = CreateRect(parent, "ArrowHead", end, new Vector2(24f, 24f), new Vector2(0.5f, 0.5f), new Vector2(0.5f, 0.5f));
            head.localRotation = Quaternion.Euler(0f, 0f, angle);
            Image headImage = head.gameObject.AddComponent<Image>();
            headImage.color = color;
        }

        private static string FormatBullets(IReadOnlyList<string> bullets)
        {
            List<string> lines = new List<string>(bullets.Count);
            for (int i = 0; i < bullets.Count; i++)
            {
                lines.Add("• " + bullets[i]);
            }

            return string.Join("\n", lines);
        }

        private static byte[] Render(Camera camera, int width, int height)
        {
            RenderTexture renderTexture = new RenderTexture(width, height, 24, RenderTextureFormat.ARGB32);
            RenderTexture previous = RenderTexture.active;
            RenderTexture.active = renderTexture;
            camera.targetTexture = renderTexture;
            camera.Render();

            Texture2D texture = new Texture2D(width, height, TextureFormat.RGBA32, false);
            texture.ReadPixels(new Rect(0f, 0f, width, height), 0, 0);
            texture.Apply(false, false);

            byte[] png = texture.EncodeToPNG();
            camera.targetTexture = null;
            RenderTexture.active = previous;
            UnityEngine.Object.DestroyImmediate(texture);
            renderTexture.Release();
            UnityEngine.Object.DestroyImmediate(renderTexture);
            return png;
        }

        private static Color WithAlpha(Color color, float alpha)
        {
            color.a = alpha;
            return color;
        }

        private static int ParseDimension(string? text, int fallback)
        {
            return int.TryParse(text, out int parsed) && parsed > 0 ? parsed : fallback;
        }

        private readonly struct ShotContext
        {
            public ShotContext(string packageName, Palette palette, Camera camera, RectTransform root, Font font)
            {
                PackageName = packageName;
                Palette = palette;
                Camera = camera;
                Root = root;
                Font = font;
            }

            public string PackageName { get; }
            public Palette Palette { get; }
            public Camera Camera { get; }
            public RectTransform Root { get; }
            public Font Font { get; }
        }

        private readonly struct Palette
        {
            public Palette(Color background, Color accentA, Color accentB)
            {
                Background = background;
                AccentA = accentA;
                AccentB = accentB;
                TextMuted = new Color(0.84f, 0.88f, 0.92f, 0.92f);
            }

            public Color Background { get; }
            public Color AccentA { get; }
            public Color AccentB { get; }
            public Color TextMuted { get; }
        }

        private readonly struct CardData
        {
            public CardData(string title, string[] bullets)
            {
                Title = title;
                Bullets = bullets;
            }

            public string Title { get; }
            public string[] Bullets { get; }
        }

        private readonly struct FlowNodeData
        {
            public FlowNodeData(string title, string body, Color accent)
            {
                Title = title;
                Body = body;
                Accent = accent;
            }

            public string Title { get; }
            public string Body { get; }
            public Color Accent { get; }
        }
    }
}
