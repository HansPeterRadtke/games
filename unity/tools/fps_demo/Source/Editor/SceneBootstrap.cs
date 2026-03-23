using System.Collections.Generic;
using System.IO;
using HPR.Foundation.Utils;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.Rendering;

public static class SceneBootstrap
{
    private const string ScenePath = "Assets/Scenes/Main.unity";

    public static void CreateScene()
    {
        Directory.CreateDirectory("Assets/Scenes");
        var scene = EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);
        ConfigureRenderSettings();

        var sharedMaterials = CreateMaterialPalette();
        CreateLighting(sharedMaterials);
        CreateWorld(sharedMaterials);
        var player = CreatePlayer(sharedMaterials);
        var mapCamera = CreateMapCamera(player.transform);
        CreateGameSystems(player, mapCamera);

        EditorBuildSettings.scenes = new[]
        {
            new EditorBuildSettingsScene(ScenePath, true)
        };

        EditorSceneManager.SaveScene(scene, ScenePath);
        AssetDatabase.SaveAssets();
        Debug.Log($"Created {ScenePath}");
    }

    public static void BuildLinux()
    {
        CreateScene();
        Directory.CreateDirectory("Build/Linux");
        var report = BuildPipeline.BuildPlayer(new[] { ScenePath }, "Build/Linux/FPSDemo.x86_64", BuildTarget.StandaloneLinux64, BuildOptions.StrictMode);
        if (report.summary.result != UnityEditor.Build.Reporting.BuildResult.Succeeded)
        {
            throw new System.Exception($"Build failed: {report.summary.result}");
        }
        Debug.Log("Build succeeded");
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

    private static void CreateLighting(Dictionary<string, Material> materials)
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

    private static void CreateWorld(Dictionary<string, Material> materials)
    {
        var world = new GameObject("World").transform;
        CreateBlock(world, "Ground", new Vector3(0f, -0.5f, 0f), new Vector3(62f, 1f, 62f), materials["Ground"]);
        CreateBlock(world, "PerimeterNorth", new Vector3(0f, 2f, 31f), new Vector3(62f, 4f, 1f), materials["Wall"]);
        CreateBlock(world, "PerimeterSouth", new Vector3(0f, 2f, -31f), new Vector3(62f, 4f, 1f), materials["Wall"]);
        CreateBlock(world, "PerimeterEast", new Vector3(31f, 2f, 0f), new Vector3(1f, 4f, 62f), materials["Wall"]);
        CreateBlock(world, "PerimeterWest", new Vector3(-31f, 2f, 0f), new Vector3(1f, 4f, 62f), materials["Wall"]);

        CreateBlock(world, "HubNorthLeft", new Vector3(-7f, 2f, 10f), new Vector3(6f, 4f, 1f), materials["Wall"]);
        CreateBlock(world, "HubNorthRight", new Vector3(7f, 2f, 10f), new Vector3(6f, 4f, 1f), materials["Wall"]);
        CreateBlock(world, "HubSouthLeft", new Vector3(-7f, 2f, -10f), new Vector3(6f, 4f, 1f), materials["Wall"]);
        CreateBlock(world, "HubSouthRight", new Vector3(7f, 2f, -10f), new Vector3(6f, 4f, 1f), materials["Wall"]);
        CreateBlock(world, "HubEastTop", new Vector3(10f, 2f, 7f), new Vector3(1f, 4f, 6f), materials["Wall"]);
        CreateBlock(world, "HubEastBottom", new Vector3(10f, 2f, -7f), new Vector3(1f, 4f, 6f), materials["Wall"]);
        CreateBlock(world, "HubWestTop", new Vector3(-10f, 2f, 7f), new Vector3(1f, 4f, 6f), materials["Wall"]);
        CreateBlock(world, "HubWestBottom", new Vector3(-10f, 2f, -7f), new Vector3(1f, 4f, 6f), materials["Wall"]);

        CreateBlock(world, "NorthRoomFront", new Vector3(0f, 2f, 30f), new Vector3(22f, 4f, 1f), materials["Wall"]);
        CreateBlock(world, "SouthRoomFront", new Vector3(0f, 2f, -30f), new Vector3(22f, 4f, 1f), materials["Wall"]);
        CreateBlock(world, "EastRoomFront", new Vector3(30f, 2f, 0f), new Vector3(1f, 4f, 22f), materials["Wall"]);
        CreateBlock(world, "WestRoomFront", new Vector3(-30f, 2f, 0f), new Vector3(1f, 4f, 22f), materials["Wall"]);

        CreateDoor(world, "door_east", new Vector3(10f, 0f, 0f), Vector3.zero, string.Empty, materials["Door"]);
        CreateDoor(world, "door_west", new Vector3(-10f, 0f, 0f), new Vector3(0f, 180f, 0f), string.Empty, materials["Door"]);
        CreateDoor(world, "door_north", new Vector3(0f, 0f, 10f), new Vector3(0f, 90f, 0f), "Red", materials["SecurityDoor"]);
        CreateDoor(world, "door_south", new Vector3(0f, 0f, -10f), new Vector3(0f, -90f, 0f), "Blue", materials["BlueDoor"]);

        CreateCoverAndDecor(world, materials);
        CreatePickups(world, materials);
        CreateEnemies(world, materials);
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

    private static void CreatePickups(Transform parent, Dictionary<string, Material> materials)
    {
        CreatePickup(parent, "pickup_red_key", new Vector3(19f, 0.7f, 0f), PickupKind.RedKey, 1, materials["KeyRed"], PrimitiveType.Cube, new Vector3(0.5f, 0.15f, 0.9f));
        CreatePickup(parent, "pickup_shotgun_ammo", new Vector3(16f, 0.6f, -3f), PickupKind.AmmoScatter, 8, materials["Pickup"], PrimitiveType.Cube, new Vector3(0.5f, 0.5f, 0.5f));
        CreatePickup(parent, "pickup_launcher_ammo", new Vector3(20f, 0.6f, 3f), PickupKind.AmmoLauncher, 2, materials["Pickup"], PrimitiveType.Cube, new Vector3(0.5f, 0.5f, 0.5f));
        CreatePickup(parent, "pickup_medkit", new Vector3(-19f, 0.6f, 0f), PickupKind.Medkit, 1, materials["Pickup"], PrimitiveType.Sphere, new Vector3(0.7f, 0.7f, 0.7f));
        CreatePickup(parent, "pickup_armor", new Vector3(-16f, 0.6f, -3f), PickupKind.ArmorPatch, 1, materials["Pickup"], PrimitiveType.Capsule, new Vector3(0.4f, 0.7f, 0.4f));
        CreatePickup(parent, "pickup_blue_key", new Vector3(0f, 0.7f, -21f), PickupKind.BlueKey, 1, materials["KeyBlue"], PrimitiveType.Cube, new Vector3(0.5f, 0.15f, 0.9f));
        CreatePickup(parent, "pickup_pistol_ammo", new Vector3(0f, 0.6f, -17f), PickupKind.AmmoPistol, 20, materials["Pickup"], PrimitiveType.Cube, new Vector3(0.5f, 0.5f, 0.5f));
        CreatePickup(parent, "pickup_needler_ammo", new Vector3(0f, 0.6f, 20f), PickupKind.AmmoNeedler, 36, materials["Pickup"], PrimitiveType.Cube, new Vector3(0.5f, 0.5f, 0.5f));
    }

    private static void CreateEnemies(Transform parent, Dictionary<string, Material> materials)
    {
        CreateEnemy(parent, "sentry_hub", new Vector3(0f, 0.2f, 4f), new Vector3(-4f, 0.2f, 4f), new Vector3(4f, 0.2f, 4f), materials, true);
        CreateEnemy(parent, "sweeper_armory", new Vector3(18f, 0.2f, -6f), new Vector3(14f, 0.2f, -6f), new Vector3(22f, 0.2f, -1f), materials, false);
        CreateEnemy(parent, "medbay_intruder", new Vector3(-18f, 0.2f, 6f), new Vector3(-22f, 0.2f, 1f), new Vector3(-14f, 0.2f, 6f), materials, false);
        CreateEnemy(parent, "security_guard", new Vector3(0f, 0.2f, 20f), new Vector3(-4f, 0.2f, 18f), new Vector3(4f, 0.2f, 22f), materials, true);
        CreateEnemy(parent, "power_walker", new Vector3(0f, 0.2f, -18f), new Vector3(-5f, 0.2f, -22f), new Vector3(5f, 0.2f, -16f), materials, true);
    }

    private static PlayerController CreatePlayer(Dictionary<string, Material> materials)
    {
        var player = new GameObject("Player");
        player.transform.position = new Vector3(0f, 1.3f, -1.5f);
        player.transform.rotation = Quaternion.Euler(0f, 0f, 0f);
        var controller = player.AddComponent<CharacterController>();
        controller.height = 1.8f;
        controller.radius = 0.35f;
        controller.center = new Vector3(0f, 0.9f, 0f);

        player.AddComponent<PlayerStats>();
        player.AddComponent<PlayerInventory>();
        player.AddComponent<WeaponSystem>();
        var playerController = player.AddComponent<PlayerController>();

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

        return playerController;
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

    private static GameManager CreateGameSystems(PlayerController player, Camera mapCamera)
    {
        var systems = new GameObject("GameSystems");
        var ui = systems.AddComponent<GameUiController>();
        var manager = systems.AddComponent<GameManager>();
        manager.AssignReferences(player, mapCamera, ui);
        return manager;
    }

    private static DoorController CreateDoor(Transform parent, string saveId, Vector3 position, Vector3 euler, string requiredKey, Material material)
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
        var leaf = CreateBlock(leafRoot.transform, "LeafMesh", new Vector3(1f, 1.6f, 0f), new Vector3(2f, 3.2f, 0.35f), material);
        var controller = pivot.AddComponent<DoorController>();
        controller.Configure(saveId, leafRoot.transform, requiredKey);
        return controller;
    }

    private static PickupItem CreatePickup(Transform parent, string saveId, Vector3 position, PickupKind kind, int amount, Material material, PrimitiveType primitive, Vector3 scale)
    {
        var pickup = GameObject.CreatePrimitive(primitive);
        pickup.name = saveId;
        pickup.transform.SetParent(parent, false);
        pickup.transform.position = position;
        pickup.transform.localScale = scale;
        pickup.GetComponent<Renderer>().sharedMaterial = material;
        var pickupItem = pickup.AddComponent<PickupItem>();
        pickupItem.Configure(saveId, kind, amount);
        return pickupItem;
    }

    private static EnemyAgent CreateEnemy(Transform parent, string saveId, Vector3 position, Vector3 patrolA, Vector3 patrolB, Dictionary<string, Material> materials, bool rangedAttacker)
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
        enemy.Configure(saveId, waypointA.transform, waypointB.transform, muzzle.transform, rangedAttacker);
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
}
