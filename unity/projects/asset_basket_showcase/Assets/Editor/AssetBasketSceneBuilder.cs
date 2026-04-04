using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using UnityEditor;
using UnityEditor.Animations;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.SceneManagement;

namespace HPR.AssetBasketShowcase
{
    public static class AssetBasketSceneBuilder
    {
        private enum ShowcaseKind
        {
            Structure,
            Nature,
            Prop,
            Weapon,
            Character,
            Fx
        }

        private sealed class RenderableEntry
        {
            public string Path;
            public string Root;
            public string Name;
            public GameObject Asset;
            public ShowcaseKind Kind;
            public Bounds Bounds;
            public bool HasAnimator;
            public bool HasSkinnedMesh;
        }

        private sealed class MaterialEntry
        {
            public string Path;
            public string Root;
            public string Name;
            public Material Asset;
        }

        private sealed class TextureEntry
        {
            public string Path;
            public string Root;
            public string Name;
            public Texture2D Asset;
        }

        private sealed class AnimationEntry
        {
            public string Path;
            public string Root;
            public string Name;
            public AnimationClip Clip;
            public bool HumanMotion;
        }

        public static void BuildShowcaseSceneFromArgs()
        {
            var args = AssetBasketShowcaseTools.ParseArgs(Environment.GetCommandLineArgs());
            var scenePath = args.TryGetValue("scenePath", out var sceneValue) && !string.IsNullOrWhiteSpace(sceneValue)
                ? sceneValue
                : "Assets/Scenes/AssetBasketShowcase.unity";
            var reportPath = args.TryGetValue("reportPath", out var reportValue) && !string.IsNullOrWhiteSpace(reportValue)
                ? reportValue
                : "Assets/Scenes/AssetBasketShowcase_Report.txt";
            var roots = AssetBasketShowcaseTools.GetScanRoots(args);
            var projectRoot = Directory.GetParent(Application.dataPath)?.FullName ?? Application.dataPath;

            ResetGeneratedFolder("Assets/Generated/Showcase");
            Directory.CreateDirectory(Path.Combine(projectRoot, Path.GetDirectoryName(scenePath) ?? "Assets/Scenes"));
            Directory.CreateDirectory(Path.Combine(projectRoot, "Assets/Generated/Showcase/Controllers"));
            Directory.CreateDirectory(Path.Combine(projectRoot, "Assets/Generated/Showcase/Materials"));

            var renderables = CollectRenderables(roots);
            var materials = CollectMaterials(roots);
            var textures = CollectTextures(roots);
            var animations = CollectAnimations(roots);
            var scene = EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);

            var root = new GameObject("AssetBasketShowcase").transform;
            CreateLighting(root);
            CreateEntryCamera(root);

            var structures = renderables.Where(item => item.Kind == ShowcaseKind.Structure).ToList();
            var natures = renderables.Where(item => item.Kind == ShowcaseKind.Nature).ToList();
            var props = renderables.Where(item => item.Kind == ShowcaseKind.Prop).ToList();
            var weapons = renderables.Where(item => item.Kind == ShowcaseKind.Weapon).ToList();
            var characters = renderables.Where(item => item.Kind == ShowcaseKind.Character).ToList();
            var effects = renderables.Where(item => item.Kind == ShowcaseKind.Fx).ToList();

            const float districtGap = 160f;
            var structureSize = GetSectionSize(structures.Count, 7, 90f, 90f, 120f, 120f);
            var natureSize = GetSectionSize(natures.Count, 7, 80f, 80f, 120f, 120f);
            var propSize = GetSectionSize(props.Count, 14, 28f, 28f, 100f, 100f);
            var weaponSize = GetSectionSize(weapons.Count, 12, 22f, 22f, 100f, 100f);
            var characterSize = GetSectionSize(characters.Count, 14, 28f, 28f, 100f, 100f);
            var fxSize = GetSectionSize(effects.Count, 10, 32f, 32f, 100f, 100f);
            var materialSize = GetSectionSize(materials.Count, 18, 18f, 18f, 120f, 100f);
            var textureSize = GetSectionSize(textures.Count, 18, 18f, 18f, 120f, 100f);
            var animationSize = GetSectionSize(animations.Count, 10, 36f, 36f, 140f, 120f);

            var renderableRoot = CreateSectionRoot(root, "RenderableDistricts", Vector3.zero);
            var structureRoot = CreateSectionRoot(renderableRoot, "Structures", new Vector3(0f, 0f, 0f));
            var natureRoot = CreateSectionRoot(renderableRoot, "Nature", new Vector3(structureSize.x + districtGap, 0f, 0f));
            var propRoot = CreateSectionRoot(renderableRoot, "Props", new Vector3(structureSize.x + natureSize.x + districtGap * 2f, 0f, 0f));
            var weaponRoot = CreateSectionRoot(renderableRoot, "Weapons", new Vector3(structureSize.x + natureSize.x + propSize.x + districtGap * 3f, 0f, 0f));
            var characterRoot = CreateSectionRoot(renderableRoot, "Characters", new Vector3(structureSize.x + natureSize.x + propSize.x + weaponSize.x + districtGap * 4f, 0f, 0f));
            var fxRoot = CreateSectionRoot(renderableRoot, "Effects", new Vector3(structureSize.x + natureSize.x + propSize.x + weaponSize.x + characterSize.x + districtGap * 5f, 0f, 0f));

            var galleryZ = Mathf.Max(structureSize.y, natureSize.y, propSize.y, weaponSize.y, characterSize.y, fxSize.y) + 260f;
            var materialRoot = CreateSectionRoot(root, "MaterialGallery", new Vector3(0f, 0f, galleryZ));
            var textureRoot = CreateSectionRoot(root, "TextureGallery", new Vector3(materialSize.x + districtGap, 0f, galleryZ));
            var animationRoot = CreateSectionRoot(root, "AnimationTheater", new Vector3(materialSize.x + textureSize.x + districtGap * 2f, 0f, galleryZ));

            CreateFloor(structureRoot, structureSize.x, structureSize.y, new Color(0.35f, 0.34f, 0.3f));
            CreateFloor(natureRoot, natureSize.x, natureSize.y, new Color(0.22f, 0.32f, 0.2f));
            CreateFloor(propRoot, propSize.x, propSize.y, new Color(0.3f, 0.3f, 0.34f));
            CreateFloor(weaponRoot, weaponSize.x, weaponSize.y, new Color(0.28f, 0.28f, 0.32f));
            CreateFloor(characterRoot, characterSize.x, characterSize.y, new Color(0.33f, 0.31f, 0.28f));
            CreateFloor(fxRoot, fxSize.x, fxSize.y, new Color(0.15f, 0.15f, 0.18f));
            CreateFloor(materialRoot, materialSize.x, materialSize.y, new Color(0.3f, 0.28f, 0.24f));
            CreateFloor(textureRoot, textureSize.x, textureSize.y, new Color(0.25f, 0.28f, 0.3f));
            CreateFloor(animationRoot, animationSize.x, animationSize.y, new Color(0.27f, 0.24f, 0.3f));

            LayoutRenderables(structures, structureRoot, 90f, 90f, 7, true);
            LayoutRenderables(natures, natureRoot, 80f, 80f, 7, true);
            LayoutRenderables(props, propRoot, 28f, 28f, 14, false);
            LayoutRenderables(weapons, weaponRoot, 22f, 22f, 12, false);
            LayoutRenderables(characters, characterRoot, 28f, 28f, 14, false);
            LayoutRenderables(effects, fxRoot, 32f, 32f, 10, false);

            // Batch preview asset creation so the large imported catalog does not spend
            // minutes refreshing the AssetDatabase after every generated material/controller.
            AssetDatabase.StartAssetEditing();
            try
            {
                LayoutMaterials(materials, materialRoot, 18f, 18f, 18);
                LayoutTextures(textures, textureRoot, 18f, 18f, 18);
                LayoutAnimations(animations, characters, animationRoot, 36f, 36f, 10);
            }
            finally
            {
                AssetDatabase.StopAssetEditing();
            }

            EditorSceneManager.SaveScene(scene, scenePath);
            AssetDatabase.SaveAssets();
            AssetDatabase.Refresh(ImportAssetOptions.ForceSynchronousImport);
            WriteReport(reportPath, scenePath, roots, structures, natures, props, weapons, characters, effects, materials, textures, animations);
            Debug.Log($"SHOWCASE scene saved: {scenePath}");
        }

        private static List<RenderableEntry> CollectRenderables(IEnumerable<string> roots)
        {
            var entries = new List<RenderableEntry>();
            foreach (var root in roots)
            {
                var guidSet = new HashSet<string>(AssetDatabase.FindAssets("t:Prefab", new[] { root }));
                foreach (var guid in AssetDatabase.FindAssets("t:Model", new[] { root }))
                {
                    guidSet.Add(guid);
                }

                var seenModelNames = new HashSet<string>(StringComparer.OrdinalIgnoreCase);
                foreach (var guid in guidSet.OrderBy(value => AssetDatabase.GUIDToAssetPath(value)))
                {
                    var path = AssetDatabase.GUIDToAssetPath(guid);
                    if (path.Contains("/Editor/", StringComparison.OrdinalIgnoreCase))
                    {
                        continue;
                    }

                    var asset = AssetDatabase.LoadAssetAtPath<GameObject>(path);
                    if (asset == null)
                    {
                        continue;
                    }

                    var isModel = path.EndsWith(".fbx", StringComparison.OrdinalIgnoreCase) || path.EndsWith(".obj", StringComparison.OrdinalIgnoreCase);
                    if (isModel)
                    {
                        var stem = Path.GetFileNameWithoutExtension(path);
                        if (seenModelNames.Contains(stem))
                        {
                            continue;
                        }

                        var siblingPrefab = AssetDatabase.FindAssets(stem + " t:Prefab", new[] { Path.GetDirectoryName(path)?.Replace('\\', '/') ?? root })
                            .Select(AssetDatabase.GUIDToAssetPath)
                            .FirstOrDefault(candidate => Path.GetFileNameWithoutExtension(candidate).Equals(stem, StringComparison.OrdinalIgnoreCase));
                        if (!string.IsNullOrWhiteSpace(siblingPrefab))
                        {
                            continue;
                        }

                        seenModelNames.Add(stem);
                    }

                    if (!TryMeasure(asset, out var bounds, out var hasAnimator, out var hasSkinnedMesh, out var hasParticleSystem, out var hasTerrain))
                    {
                        continue;
                    }

                    entries.Add(new RenderableEntry
                    {
                        Path = path,
                        Root = root,
                        Name = asset.name,
                        Asset = asset,
                        Bounds = bounds,
                        HasAnimator = hasAnimator,
                        HasSkinnedMesh = hasSkinnedMesh,
                        Kind = Classify(path, asset.name, bounds, hasAnimator, hasSkinnedMesh, hasParticleSystem, hasTerrain),
                    });
                }
            }
            return entries;
        }

        private static List<MaterialEntry> CollectMaterials(IEnumerable<string> roots)
        {
            var entries = new List<MaterialEntry>();
            foreach (var root in roots)
            {
                foreach (var guid in AssetDatabase.FindAssets("t:Material", new[] { root }).OrderBy(value => AssetDatabase.GUIDToAssetPath(value)))
                {
                    var path = AssetDatabase.GUIDToAssetPath(guid);
                    var asset = AssetDatabase.LoadAssetAtPath<Material>(path);
                    if (asset == null)
                    {
                        continue;
                    }

                    entries.Add(new MaterialEntry { Path = path, Root = root, Name = asset.name, Asset = asset });
                }
            }
            return entries;
        }

        private static List<TextureEntry> CollectTextures(IEnumerable<string> roots)
        {
            var entries = new List<TextureEntry>();
            foreach (var root in roots)
            {
                foreach (var guid in AssetDatabase.FindAssets("t:Texture2D", new[] { root }).OrderBy(value => AssetDatabase.GUIDToAssetPath(value)))
                {
                    var path = AssetDatabase.GUIDToAssetPath(guid);
                    if (path.Contains("/Editor/", StringComparison.OrdinalIgnoreCase))
                    {
                        continue;
                    }

                    var asset = AssetDatabase.LoadAssetAtPath<Texture2D>(path);
                    if (asset == null)
                    {
                        continue;
                    }

                    entries.Add(new TextureEntry { Path = path, Root = root, Name = asset.name, Asset = asset });
                }
            }
            return entries;
        }

        private static List<AnimationEntry> CollectAnimations(IEnumerable<string> roots)
        {
            var entries = new List<AnimationEntry>();
            foreach (var root in roots)
            {
                foreach (var guid in AssetDatabase.FindAssets("t:AnimationClip", new[] { root }).OrderBy(value => AssetDatabase.GUIDToAssetPath(value)))
                {
                    var path = AssetDatabase.GUIDToAssetPath(guid);
                    if (path.Contains("__preview__", StringComparison.OrdinalIgnoreCase) || path.Contains("/Editor/", StringComparison.OrdinalIgnoreCase))
                    {
                        continue;
                    }

                    var clip = AssetDatabase.LoadAssetAtPath<AnimationClip>(path);
                    if (clip == null || clip.empty)
                    {
                        continue;
                    }

                    entries.Add(new AnimationEntry
                    {
                        Path = path,
                        Root = root,
                        Name = clip.name,
                        Clip = clip,
                        HumanMotion = clip.humanMotion,
                    });
                }
            }
            return entries;
        }

        private static void LayoutRenderables(IReadOnlyList<RenderableEntry> entries, Transform parent, float cellWidth, float cellDepth, int columns, bool largePlots)
        {
            for (int index = 0; index < entries.Count; index++)
            {
                var entry = entries[index];
                var row = index / columns;
                var column = index % columns;
                var localOrigin = new Vector3((column - (columns - 1) * 0.5f) * cellWidth, 0f, row * cellDepth + 20f);
                var holder = new GameObject(entry.Name);
                holder.transform.SetParent(parent, false);
                holder.transform.localPosition = localOrigin;
                CreatePedestal(holder.transform, largePlots ? 24f : 8f, largePlots ? 24f : 8f, largePlots ? 0.5f : 0.25f);
                var instance = PrefabUtility.InstantiatePrefab(entry.Asset) as GameObject;
                if (instance == null)
                {
                    continue;
                }

                instance.name = entry.Name;
                instance.transform.SetParent(holder.transform, false);
                FitInstance(instance, largePlots ? cellWidth * 0.75f : cellWidth * 0.55f, largePlots ? 22f : 6f);
                CreateLabel(holder.transform, $"{Path.GetFileName(entry.Root)}\n{entry.Name}", new Vector3(0f, largePlots ? 18f : 7f, 0f));
            }
        }

        private static void LayoutMaterials(IReadOnlyList<MaterialEntry> entries, Transform parent, float cellWidth, float cellDepth, int columns)
        {
            for (int index = 0; index < entries.Count; index++)
            {
                var entry = entries[index];
                var row = index / columns;
                var column = index % columns;
                var holder = new GameObject(entry.Name);
                holder.transform.SetParent(parent, false);
                holder.transform.localPosition = new Vector3((column - (columns - 1) * 0.5f) * cellWidth, 0f, row * cellDepth + 15f);
                CreatePedestal(holder.transform, 4f, 4f, 0.3f);
                var preview = GameObject.CreatePrimitive(index % 2 == 0 ? PrimitiveType.Sphere : PrimitiveType.Cube);
                preview.name = entry.Name + " Preview";
                preview.transform.SetParent(holder.transform, false);
                preview.transform.localPosition = new Vector3(0f, 1.2f, 0f);
                preview.transform.localScale = Vector3.one * 2f;
                preview.GetComponent<Renderer>().sharedMaterial = entry.Asset;
                CreateLabel(holder.transform, $"{Path.GetFileName(entry.Root)}\n{entry.Name}", new Vector3(0f, 3.6f, 0f));

                if ((index + 1) % 250 == 0)
                {
                    Debug.Log($"SHOWCASE material previews: {index + 1}/{entries.Count}");
                }
            }
        }

        private static void LayoutTextures(IReadOnlyList<TextureEntry> entries, Transform parent, float cellWidth, float cellDepth, int columns)
        {
            for (int index = 0; index < entries.Count; index++)
            {
                var entry = entries[index];
                var row = index / columns;
                var column = index % columns;
                var holder = new GameObject(entry.Name);
                holder.transform.SetParent(parent, false);
                holder.transform.localPosition = new Vector3((column - (columns - 1) * 0.5f) * cellWidth, 0f, row * cellDepth + 15f);
                CreatePedestal(holder.transform, 4f, 4f, 0.3f);
                var quad = GameObject.CreatePrimitive(PrimitiveType.Quad);
                quad.name = entry.Name + " Panel";
                quad.transform.SetParent(holder.transform, false);
                quad.transform.localPosition = new Vector3(0f, 2f, 0f);
                quad.transform.localScale = new Vector3(3f, 3f, 1f);
                var shader = Shader.Find(IsNormalTexture(entry.Name) ? "Standard" : "Unlit/Texture") ?? Shader.Find("Standard");
                var material = new Material(shader)
                {
                    name = entry.Name + "_GeneratedPreview"
                };
                if (IsNormalTexture(entry.Name) && material.HasProperty("_BumpMap"))
                {
                    material.SetTexture("_MainTex", Texture2D.grayTexture);
                    material.SetTexture("_BumpMap", entry.Asset);
                    material.EnableKeyword("_NORMALMAP");
                }
                else if (material.HasProperty("_MainTex"))
                {
                    material.SetTexture("_MainTex", entry.Asset);
                }
                AssetDatabase.CreateAsset(material, AssetDatabase.GenerateUniqueAssetPath($"Assets/Generated/Showcase/Materials/{SanitizeName(entry.Name)}.mat"));
                quad.GetComponent<Renderer>().sharedMaterial = material;
                CreateLabel(holder.transform, $"{Path.GetFileName(entry.Root)}\n{entry.Name}", new Vector3(0f, 4.2f, 0f));

                if ((index + 1) % 250 == 0)
                {
                    Debug.Log($"SHOWCASE texture panels: {index + 1}/{entries.Count}");
                }
            }
        }

        private static void LayoutAnimations(IReadOnlyList<AnimationEntry> animations, IReadOnlyList<RenderableEntry> characters, Transform parent, float cellWidth, float cellDepth, int columns)
        {
            if (animations.Count == 0)
            {
                return;
            }

            var supportCharacters = characters.Count > 0 ? characters.ToList() : new List<RenderableEntry>();
            if (supportCharacters.Count == 0)
            {
                var fallback = GameObject.CreatePrimitive(PrimitiveType.Capsule);
                fallback.name = "AnimationFallbackCapsule";
                PrefabUtility.SaveAsPrefabAsset(fallback, "Assets/Generated/Showcase/AnimationFallbackCapsule.prefab");
                UnityEngine.Object.DestroyImmediate(fallback);
                var fallbackPrefab = AssetDatabase.LoadAssetAtPath<GameObject>("Assets/Generated/Showcase/AnimationFallbackCapsule.prefab");
                supportCharacters.Add(new RenderableEntry
                {
                    Asset = fallbackPrefab,
                    Name = fallbackPrefab.name,
                    Root = "Assets/Generated/Showcase",
                    Bounds = new Bounds(Vector3.zero, new Vector3(1f, 2f, 1f)),
                    HasAnimator = false,
                    HasSkinnedMesh = false,
                    Kind = ShowcaseKind.Character,
                    Path = "Assets/Generated/Showcase/AnimationFallbackCapsule.prefab",
                });
            }

            for (int index = 0; index < animations.Count; index++)
            {
                var animation = animations[index];
                var row = index / columns;
                var column = index % columns;
                var holder = new GameObject(animation.Name);
                holder.transform.SetParent(parent, false);
                holder.transform.localPosition = new Vector3((column - (columns - 1) * 0.5f) * cellWidth, 0f, row * cellDepth + 20f);
                CreatePedestal(holder.transform, 8f, 8f, 0.3f);

                var support = supportCharacters[index % supportCharacters.Count];
                var instance = PrefabUtility.InstantiatePrefab(support.Asset) as GameObject;
                if (instance == null)
                {
                    continue;
                }

                instance.name = support.Name + "_" + animation.Name;
                instance.transform.SetParent(holder.transform, false);
                FitInstance(instance, cellWidth * 0.45f, 6f);
                var animator = instance.GetComponent<Animator>();
                if (animator == null)
                {
                    animator = instance.AddComponent<Animator>();
                }

                var controllerPath = AssetDatabase.GenerateUniqueAssetPath($"Assets/Generated/Showcase/Controllers/{SanitizeName(animation.Root)}_{SanitizeName(animation.Name)}.controller");
                var controller = AnimatorController.CreateAnimatorControllerAtPath(controllerPath);
                var stateMachine = controller.layers[0].stateMachine;
                var state = stateMachine.states.Length > 0
                    ? stateMachine.states[0].state
                    : stateMachine.AddState("Play");
                state.motion = animation.Clip;
                stateMachine.defaultState = state;
                animator.runtimeAnimatorController = controller;
                CreateLabel(holder.transform, $"{Path.GetFileName(animation.Root)}\n{animation.Name}", new Vector3(0f, 7f, 0f));

                if ((index + 1) % 50 == 0)
                {
                    Debug.Log($"SHOWCASE animation stages: {index + 1}/{animations.Count}");
                }
            }
        }

        private static bool TryMeasure(GameObject asset, out Bounds bounds, out bool hasAnimator, out bool hasSkinnedMesh, out bool hasParticleSystem, out bool hasTerrain)
        {
            bounds = new Bounds(Vector3.zero, Vector3.zero);
            hasAnimator = false;
            hasSkinnedMesh = false;
            hasParticleSystem = false;
            hasTerrain = false;

            var instance = PrefabUtility.InstantiatePrefab(asset) as GameObject;
            if (instance == null)
            {
                return false;
            }

            try
            {
                hasAnimator = instance.GetComponentInChildren<Animator>(true) != null;
                hasSkinnedMesh = instance.GetComponentsInChildren<SkinnedMeshRenderer>(true).Length > 0;
                hasParticleSystem = instance.GetComponentsInChildren<ParticleSystem>(true).Length > 0;
                var terrains = instance.GetComponentsInChildren<Terrain>(true);
                hasTerrain = terrains.Length > 0;

                var renderers = instance.GetComponentsInChildren<Renderer>(true);
                if (renderers.Length > 0)
                {
                    bounds = renderers[0].bounds;
                    foreach (var renderer in renderers.Skip(1))
                    {
                        bounds.Encapsulate(renderer.bounds);
                    }
                    return true;
                }

                if (terrains.Length > 0)
                {
                    var terrainSize = terrains[0].terrainData != null ? terrains[0].terrainData.size : new Vector3(10f, 1f, 10f);
                    bounds = new Bounds(terrains[0].transform.position + terrainSize * 0.5f, terrainSize);
                    return true;
                }

                return false;
            }
            finally
            {
                UnityEngine.Object.DestroyImmediate(instance);
            }
        }

        private static ShowcaseKind Classify(string path, string name, Bounds bounds, bool hasAnimator, bool hasSkinnedMesh, bool hasParticleSystem, bool hasTerrain)
        {
            var key = (path + " " + name).ToLowerInvariant();
            if (hasParticleSystem || key.Contains("particle") || key.Contains("vfx") || key.Contains("fx"))
            {
                return ShowcaseKind.Fx;
            }
            if (key.Contains("weapon") || key.Contains("gun") || key.Contains("sword") || key.Contains("rifle") || key.Contains("pistol") || key.Contains("bow") || key.Contains("melee"))
            {
                return ShowcaseKind.Weapon;
            }
            if (hasSkinnedMesh || hasAnimator || key.Contains("character") || key.Contains("girl") || key.Contains("officer") || key.Contains("scavenger") || key.Contains("croc") || key.Contains("npc") || key.Contains("adventure") || key.Contains("sailor") || key.Contains("suit "))
            {
                return ShowcaseKind.Character;
            }
            if (hasTerrain || key.Contains("terrain") || key.Contains("rock") || key.Contains("stone") || key.Contains("forest") || key.Contains("grass") || key.Contains("flower") || key.Contains("tree") || key.Contains("nature") || key.Contains("flood") || key.Contains("ground") || key.Contains("boulder"))
            {
                return ShowcaseKind.Nature;
            }
            var maxDimension = Mathf.Max(bounds.size.x, bounds.size.y, bounds.size.z);
            if (key.Contains("house") || key.Contains("apartment") || key.Contains("garage") || key.Contains("office") || key.Contains("warehouse") || key.Contains("shop") || key.Contains("tavern") || key.Contains("port") || key.Contains("lab") || key.Contains("interior") || maxDimension > 9f)
            {
                return ShowcaseKind.Structure;
            }
            return ShowcaseKind.Prop;
        }

        private static void FitInstance(GameObject instance, float maxFootprint, float maxHeight)
        {
            var renderers = instance.GetComponentsInChildren<Renderer>(true);
            var terrains = instance.GetComponentsInChildren<Terrain>(true);
            Bounds bounds;
            if (renderers.Length > 0)
            {
                bounds = renderers[0].bounds;
                foreach (var renderer in renderers.Skip(1))
                {
                    bounds.Encapsulate(renderer.bounds);
                }
            }
            else if (terrains.Length > 0)
            {
                var terrainSize = terrains[0].terrainData != null ? terrains[0].terrainData.size : new Vector3(10f, 1f, 10f);
                bounds = new Bounds(terrains[0].transform.position + terrainSize * 0.5f, terrainSize);
            }
            else
            {
                return;
            }

            var footprint = Mathf.Max(bounds.size.x, bounds.size.z, 0.001f);
            var height = Mathf.Max(bounds.size.y, 0.001f);
            var scale = Mathf.Min(maxFootprint / footprint, maxHeight / height, 1f);
            if (scale < 1f)
            {
                instance.transform.localScale *= scale;
                bounds = RecalculateBounds(instance, terrains.Length > 0);
            }

            instance.transform.position += new Vector3(-bounds.center.x, -bounds.min.y, -bounds.center.z);
        }

        private static Bounds RecalculateBounds(GameObject instance, bool includeTerrain)
        {
            var renderers = instance.GetComponentsInChildren<Renderer>(true);
            if (renderers.Length > 0)
            {
                var bounds = renderers[0].bounds;
                foreach (var renderer in renderers.Skip(1))
                {
                    bounds.Encapsulate(renderer.bounds);
                }
                return bounds;
            }

            if (includeTerrain)
            {
                var terrain = instance.GetComponentInChildren<Terrain>(true);
                if (terrain != null)
                {
                    var terrainSize = terrain.terrainData != null ? terrain.terrainData.size : new Vector3(10f, 1f, 10f);
                    return new Bounds(terrain.transform.position + terrainSize * 0.5f, terrainSize);
                }
            }

            return new Bounds(instance.transform.position, Vector3.one);
        }

        private static Vector2 GetSectionSize(int count, int columns, float cellWidth, float cellDepth, float paddingX, float paddingZ)
        {
            var rows = Mathf.Max(1, Mathf.CeilToInt(count / (float)Mathf.Max(1, columns)));
            var width = Mathf.Max(columns * cellWidth + paddingX, cellWidth * 3f + paddingX);
            var depth = Mathf.Max(rows * cellDepth + paddingZ + 40f, cellDepth * 3f + paddingZ);
            return new Vector2(width, depth);
        }

        private static void ResetGeneratedFolder(string assetPath)
        {
            if (AssetDatabase.IsValidFolder(assetPath))
            {
                AssetDatabase.DeleteAsset(assetPath);
            }
            AssetDatabase.Refresh(ImportAssetOptions.ForceSynchronousImport);
        }

        private static Transform CreateSectionRoot(Transform parent, string name, Vector3 localPosition)
        {
            var section = new GameObject(name).transform;
            section.SetParent(parent, false);
            section.localPosition = localPosition;
            CreateLabel(section, name, new Vector3(0f, 8f, -12f), 6);
            return section;
        }

        private static void CreateLighting(Transform parent)
        {
            var lightObject = new GameObject("Directional Light");
            lightObject.transform.SetParent(parent, false);
            lightObject.transform.rotation = Quaternion.Euler(42f, -35f, 0f);
            var light = lightObject.AddComponent<Light>();
            light.type = LightType.Directional;
            light.intensity = 1.2f;
            RenderSettings.ambientMode = UnityEngine.Rendering.AmbientMode.Flat;
            RenderSettings.ambientLight = new Color(0.5f, 0.5f, 0.52f);
        }

        private static void CreateEntryCamera(Transform parent)
        {
            var cameraObject = new GameObject("Main Camera");
            cameraObject.tag = "MainCamera";
            cameraObject.transform.SetParent(parent, false);
            cameraObject.transform.position = new Vector3(120f, 180f, -240f);
            cameraObject.transform.rotation = Quaternion.Euler(28f, 25f, 0f);
            var camera = cameraObject.AddComponent<Camera>();
            camera.farClipPlane = 12000f;
        }

        private static void CreateFloor(Transform parent, float width, float depth, Color color)
        {
            var floor = GameObject.CreatePrimitive(PrimitiveType.Cube);
            floor.name = parent.name + " Floor";
            floor.transform.SetParent(parent, false);
            floor.transform.localPosition = new Vector3(0f, -0.5f, depth * 0.5f);
            floor.transform.localScale = new Vector3(width, 1f, depth);
            var material = new Material(Shader.Find("Standard"))
            {
                color = color
            };
            floor.GetComponent<Renderer>().sharedMaterial = material;
        }

        private static void CreatePedestal(Transform parent, float width, float depth, float height)
        {
            var pedestal = GameObject.CreatePrimitive(PrimitiveType.Cube);
            pedestal.name = "Pedestal";
            pedestal.transform.SetParent(parent, false);
            pedestal.transform.localPosition = new Vector3(0f, height * 0.5f, 0f);
            pedestal.transform.localScale = new Vector3(width, height, depth);
            var material = new Material(Shader.Find("Standard"))
            {
                color = new Color(0.42f, 0.42f, 0.45f)
            };
            pedestal.GetComponent<Renderer>().sharedMaterial = material;
        }

        private static void CreateLabel(Transform parent, string text, Vector3 localPosition, int fontSize = 4)
        {
            var label = new GameObject("Label");
            label.transform.SetParent(parent, false);
            label.transform.localPosition = localPosition;
            var mesh = label.AddComponent<TextMesh>();
            mesh.text = text;
            mesh.characterSize = 0.35f;
            mesh.fontSize = fontSize * 10;
            mesh.anchor = TextAnchor.MiddleCenter;
            mesh.alignment = TextAlignment.Center;
            mesh.color = Color.white;
        }

        private static void WriteReport(string reportPath, string scenePath, IReadOnlyList<string> roots, IReadOnlyList<RenderableEntry> structures, IReadOnlyList<RenderableEntry> natures, IReadOnlyList<RenderableEntry> props, IReadOnlyList<RenderableEntry> weapons, IReadOnlyList<RenderableEntry> characters, IReadOnlyList<RenderableEntry> effects, IReadOnlyList<MaterialEntry> materials, IReadOnlyList<TextureEntry> textures, IReadOnlyList<AnimationEntry> animations)
        {
            var lines = new List<string>
            {
                "Asset basket showcase build report",
                $"Generated: {DateTime.UtcNow:O}",
                $"Scene: {scenePath}",
                $"Roots: {string.Join(", ", roots)}",
                string.Empty,
                $"structures={structures.Count}",
                $"nature={natures.Count}",
                $"props={props.Count}",
                $"weapons={weapons.Count}",
                $"characters={characters.Count}",
                $"effects={effects.Count}",
                $"materials={materials.Count}",
                $"textures={textures.Count}",
                $"animations={animations.Count}",
            };

            Directory.CreateDirectory(Path.GetDirectoryName(reportPath) ?? ".");
            File.WriteAllLines(reportPath, lines);
        }

        private static string SanitizeName(string value)
        {
            var chars = value.Select(ch => char.IsLetterOrDigit(ch) || ch == '_' || ch == '-' ? ch : '_').ToArray();
            return new string(chars);
        }

        private static bool IsNormalTexture(string name)
        {
            var lower = name.ToLowerInvariant();
            return lower.Contains("normal") || lower.EndsWith("_n") || lower.EndsWith("_normal") || lower.Contains("nrm");
        }
    }
}
