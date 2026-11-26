#!/usr/bin/env python3
"""Compile the exact first-party shader selector/helper with isolated Unity API stubs.

This is a deterministic source-level C# verification, NOT Unity Editor testing.
Never install packages, touch customer projects, or invoke a Unity executable.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import textwrap

ROOT=Path(__file__).resolve().parents[1]
AUTHOR=ROOT/"HprGameplaySuiteSceneBuilder.cs"
EXPECTED={
    "built_in":"Standard",
    "urp":"Universal Render Pipeline/Lit",
    "hdrp":"HDRP/Lit",
}


def extract_method(source:str,name:str)->str:
    signature=re.compile(
        r"(?m)^\s*(?:internal|private)\s+static\s+(?:string|Shader|void)\s+"+
        re.escape(name)+r"\s*\([^)]*\)\s*\{"
    )
    found=list(signature.finditer(source))
    if len(found)!=1:
        raise ValueError("Expected exactly one genuine first-party method: "+name)
    start=found[0].start()
    cursor=source.index("{",found[0].start())
    depth=0
    for index in range(cursor,len(source)):
        if source[index]=="{":depth+=1
        elif source[index]=="}":
            depth-=1
            if depth==0:
                return source[start:index+1]
    raise ValueError("Unbalanced source method: "+name)


HARNESS=r"""
using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using Microsoft.CodeAnalysis;
using Microsoft.CodeAnalysis.CSharp;
using UnityEngine;
using UnityEngine.Rendering;

namespace UnityEngine
{
    public readonly struct Color
    {
        public readonly float red;
        public Color(float red) { this.red=red; }
    }
    public sealed class Material
    {
        private readonly HashSet<string> supported = new(StringComparer.Ordinal);
        public readonly Dictionary<string,Color> colors = new(StringComparer.Ordinal);
        public Material(params string[] properties) { foreach(var p in properties) supported.Add(p); }
        public bool HasProperty(string property) => supported.Contains(property);
        public void SetColor(string property,Color color)
        {
            if (!HasProperty(property)) throw new InvalidOperationException("Unsupported color property");
            colors[property]=color;
        }
    }
    public sealed class Shader
    {
        public string name;
        public bool isSupported;
        public static readonly Dictionary<string,Shader> Available = new(StringComparer.Ordinal);
        public static Shader Find(string name) => Available.TryGetValue(name,out var hit) ? hit : null;
    }
}
namespace UnityEngine.Rendering
{
    public abstract class RenderPipelineAsset { }
    public sealed class UniversalRenderPipelineAsset : RenderPipelineAsset { }
    public sealed class HDRenderPipelineAsset : RenderPipelineAsset { }
    public sealed class OtherCustomPipelineAsset : RenderPipelineAsset { }
    public static class GraphicsSettings
    {
        public static RenderPipelineAsset currentRenderPipeline;
    }
}
public static class HprGameplaySuiteSceneBuilder
{
__EXACT_METHODS__
}
public static class Verification
{
    static int passed;
    static void Expect(bool ok,string label)
    {
        if (!ok) throw new InvalidOperationException("FAIL "+label);
        passed++;
        Console.WriteLine("PASS "+label);
    }
    static void Refuse(Action action,string label)
    {
        bool refused=false;
        try { action(); } catch (InvalidOperationException) { refused=true; }
        Expect(refused,label);
    }
    static string Name(Shader shader) => shader?.name;
    public static int Main(string[] args)
    {
        if (args.Length != 1 || !File.Exists(args[0]))
            throw new InvalidOperationException("Missing exact first-party C# source path");
        foreach (string[] symbols in new[]{
            new[]{"UNITY_EDITOR", "UNITY_6000_6_OR_NEWER"},
            new[]{"UNITY_EDITOR"},
            Array.Empty<string>()})
        {
            var options = new CSharpParseOptions(LanguageVersion.Preview, preprocessorSymbols:symbols);
            var errors = CSharpSyntaxTree.ParseText(File.ReadAllText(args[0]),options)
                .GetDiagnostics().Where(d => d.Severity == DiagnosticSeverity.Error).ToArray();
            Expect(errors.Length == 0,
                "Original complete builder syntax under symbols " + string.Join(",",symbols) +
                (errors.Length > 0 ? ": " + string.Join("; ",errors.Select(e=>e.ToString())) : ""));
        }
        Shader.Available.Clear();
        foreach(var name in new[]{"Standard","Universal Render Pipeline/Lit","HDRP/Lit"})
            Shader.Available[name]=new Shader{name=name,isSupported=true};
        GraphicsSettings.currentRenderPipeline=null;
        Expect(HprGameplaySuiteSceneBuilder.DemoShaderNameForPipelineType(null)=="Standard",
            "Built-in selection by actual null render-pipeline asset");
        Expect(Name(HprGameplaySuiteSceneBuilder.FindActualShader())=="Standard",
            "Built-in uses Standard shader when all renderers are installed");
        GraphicsSettings.currentRenderPipeline=new UniversalRenderPipelineAsset();
        Expect(HprGameplaySuiteSceneBuilder.DemoShaderNameForPipelineType(
            "UniversalRenderPipelineAsset")=="Universal Render Pipeline/Lit",
            "URP named renderer selects URP and not other discoverable packages");
        Expect(Name(HprGameplaySuiteSceneBuilder.FindActualShader())=="Universal Render Pipeline/Lit",
            "URP shader selected even when HDRP is also installed");
        GraphicsSettings.currentRenderPipeline=new HDRenderPipelineAsset();
        Expect(HprGameplaySuiteSceneBuilder.DemoShaderNameForPipelineType(
            "HDRenderPipelineAsset")=="HDRP/Lit",
            "HDRP named renderer selects HDRP and not first URP shader");
        Expect(Name(HprGameplaySuiteSceneBuilder.FindActualShader())=="HDRP/Lit",
            "HDRP shader selected even when URP is also installed");
        GraphicsSettings.currentRenderPipeline=new OtherCustomPipelineAsset();
        Refuse(()=>HprGameplaySuiteSceneBuilder.FindActualShader(),
            "Unrecognized render pipeline refuses instead of silently authoring wrong materials");
        Refuse(()=>HprGameplaySuiteSceneBuilder.DemoShaderNameForPipelineType("NotUniversalFake"),
            "Near-match pipeline class with Universal substring cannot masquerade as URP");
        Refuse(()=>HprGameplaySuiteSceneBuilder.DemoShaderNameForPipelineType("HDRenderPipelineAssetFake"),
            "Near-match pipeline class with HDRP substring cannot masquerade as HDRP");
        GraphicsSettings.currentRenderPipeline=new HDRenderPipelineAsset();
        Shader.Available.Remove("HDRP/Lit");
        Refuse(()=>HprGameplaySuiteSceneBuilder.FindActualShader(),
            "Missing HDRP shader fails closed rather than selecting installed URP");
        Shader.Available["HDRP/Lit"]=new Shader{name="HDRP/Lit",isSupported=false};
        Refuse(()=>HprGameplaySuiteSceneBuilder.FindActualShader(),
            "Unsupported HDRP shader fails closed");
        GraphicsSettings.currentRenderPipeline=new UniversalRenderPipelineAsset();
        Shader.Available.Remove("Universal Render Pipeline/Lit");
        Refuse(()=>HprGameplaySuiteSceneBuilder.FindActualShader(),
            "Missing URP shader fails closed instead of selecting HDRP");
        Shader.Available["Universal Render Pipeline/Lit"]=new Shader{name="Universal Render Pipeline/Lit",isSupported=false};
        Refuse(()=>HprGameplaySuiteSceneBuilder.FindActualShader(),
            "Unsupported URP shader fails closed");
        var standard = new Material("_Color");
        HprGameplaySuiteSceneBuilder.ExerciseDemoMaterialColor(standard,new Color(.42f));
        Expect(standard.colors.ContainsKey("_Color") && standard.colors["_Color"].red == .42f &&
               !standard.colors.ContainsKey("_BaseColor"), "Built-in Standard color written to _Color");
        var urp = new Material("_BaseColor");
        HprGameplaySuiteSceneBuilder.ExerciseDemoMaterialColor(urp,new Color(.53f));
        Expect(urp.colors.ContainsKey("_BaseColor") && urp.colors["_BaseColor"].red == .53f &&
               !urp.colors.ContainsKey("_Color"), "URP uses its _BaseColor property");
        var hdrp = new Material("_BaseColor");
        HprGameplaySuiteSceneBuilder.ExerciseDemoMaterialColor(hdrp,new Color(.64f));
        Expect(hdrp.colors.ContainsKey("_BaseColor") && hdrp.colors["_BaseColor"].red == .64f,
            "HDRP uses its _BaseColor property");
        var both = new Material("_Color","_BaseColor");
        HprGameplaySuiteSceneBuilder.ExerciseDemoMaterialColor(both,new Color(.75f));
        Expect(both.colors.ContainsKey("_Color") && both.colors.ContainsKey("_BaseColor") &&
               both.colors["_Color"].red == .75f && both.colors["_BaseColor"].red == .75f,
            "Both supported color properties are synchronized");
        var unsupported = new Material("_Unknown");
        Refuse(()=>HprGameplaySuiteSceneBuilder.ExerciseDemoMaterialColor(unsupported,new Color(.8f)),
            "Shader without a color property refuses without inserting fabricated color");
        Expect(unsupported.colors.Count==0,
            "Failed color conversion leaves unsupported material unchanged");
        Console.WriteLine("HPR_PIPELINE_SHADER_SOURCE_PASS assertions="+passed);
        return 0;
    }
}
"""


def run(out: Path)->dict:
    if out.exists() or out.is_symlink():
        raise FileExistsError("Provide fresh private acceptance directory")
    out=out.absolute()
    if "/data/var/marketplace-account-setup/" not in str(out):
        raise ValueError("Tests must use an isolated private evidence directory")
    original=AUTHOR.read_text()
    # Verify both source callers have been redirected, not just the method tested.
    authored=original.split("private static Material CreateMaterial(",1)[1].split(
        "private static GameObject Shape(",1)[0]
    adapted=original.split("public static void AdaptDemoMaterials()",1)[1].split(
        "public static void BuildAndExport()",1)[0]
    if "RequireActiveDemoShader()" not in authored or "RequireActiveDemoShader()" not in adapted:
        raise ValueError("Actual author and adapter not both bound to the shared selection helper")
    if "SetDemoMaterialColor(material, color)" not in authored or "SetDemoMaterialColor(material, color)" not in adapted:
        raise ValueError("Both source paths must update the correct base-color property")
    if authored.index("SetDemoMaterialColor(material, color)") > authored.index("AssetDatabase.CreateAsset(material, path)"):
        raise ValueError("New shader material color is not validated before asset creation")
    if "Shader.Find(\"Universal Render Pipeline/Lit\") ??" in original or 'Shader.Find("Unlit/Color")' in authored:
        raise ValueError("An incompatible fallback remains in original authoring code")
    selector=extract_method(original,"DemoShaderNameForPipelineType")
    resolver=extract_method(original,"RequireActiveDemoShader").replace(
        "private static Shader RequireActiveDemoShader","internal static Shader FindActualShader")
    color=extract_method(original,"SetDemoMaterialColor").replace(
        "private static void SetDemoMaterialColor","internal static void ExerciseDemoMaterialColor")
    out.mkdir(parents=True)
    csharp=HARNESS.replace("__EXACT_METHODS__",selector+"\n"+resolver+"\n"+color)
    (out/"Program.cs").write_text(csharp)
    (out/"HprPipelineShaderOffline.csproj").write_text(
        "<Project Sdk=\"Microsoft.NET.Sdk\"><PropertyGroup>"+
        "<OutputType>Exe</OutputType><TargetFramework>net8.0</TargetFramework>"+
        "<LangVersion>latest</LangVersion><Nullable>disable</Nullable>"+
        "<TreatWarningsAsErrors>true</TreatWarningsAsErrors>"+
        "</PropertyGroup><ItemGroup>"+
        "<Reference Include=\"Microsoft.CodeAnalysis\"><HintPath>$(MSBuildSDKsPath)/../Roslyn/bincore/Microsoft.CodeAnalysis.dll</HintPath></Reference>"+
        "<Reference Include=\"Microsoft.CodeAnalysis.CSharp\"><HintPath>$(MSBuildSDKsPath)/../Roslyn/bincore/Microsoft.CodeAnalysis.CSharp.dll</HintPath></Reference>"+
        "</ItemGroup></Project>"
    )
    (out/"NuGet.Config").write_text(
        '<?xml version="1.0"?><configuration><packageSources><clear /></packageSources></configuration>'
    )
    env=dict(os.environ,DOTNET_CLI_TELEMETRY_OPTOUT="1",DOTNET_NOLOGO="1",
             DOTNET_CLI_HOME=str(out/"dotnet-home"),NUGET_PACKAGES=str(out/"packages"))
    build=subprocess.run(["dotnet","restore",str(out/"HprPipelineShaderOffline.csproj"),
                          "--configfile",str(out/"NuGet.Config"),"-p:NuGetAudit=false"],
                          text=True,capture_output=True,timeout=50,env=env)
    (out/"restore.log").write_text(build.stdout+"\n"+build.stderr)
    if build.returncode:raise RuntimeError("Local offline restore failed")
    build=subprocess.run(["dotnet","build",str(out/"HprPipelineShaderOffline.csproj"),
                          "--no-restore","-c","Release","-m:1","-p:UseSharedCompilation=false"],
                          text=True,capture_output=True,timeout=50,env=env)
    (out/"build.log").write_text(build.stdout+"\n"+build.stderr)
    if build.returncode:raise RuntimeError("Offline C# compile failed")
    executable=out/"bin/Release/net8.0/HprPipelineShaderOffline.dll"
    result=subprocess.run(["dotnet",str(executable),str(AUTHOR)],capture_output=True,text=True,timeout=15,env=env)
    (out/"process.log").write_text(result.stdout+"\n"+result.stderr)
    if result.returncode or "HPR_PIPELINE_SHADER_SOURCE_PASS assertions=22" not in result.stdout:
        raise RuntimeError("Actual C# source selection failed harness checks")
    receipt={
        "status":"OFFLINE_SOURCE_CSHARP_SELECTION_PASS_NOT_NATIVE_UNITY_EDITOR",
        "source_sha256":hashlib.sha256(AUTHOR.read_bytes()).hexdigest(),
        "extracted_selector_sha256":hashlib.sha256(selector.encode()).hexdigest(),
        "extracted_resolver_sha256":hashlib.sha256(resolver.encode()).hexdigest(),
        "extracted_color_helper_sha256":hashlib.sha256(color.encode()).hexdigest(),
        "compiler":"local .NET SDK and UnityEngine stub only",
        "actual_unity_editor_invoked":False,"actual_URP_HDRP_installed_test":False,
        "original_buyer_files_modified":False,
        "unit_assertions":22,
        "full_original_builder_roslyn_syntax_checked_under_three_preprocessor_configs":True,
        "tested_types":["null Built-in","UniversalRenderPipelineAsset","HDRenderPipelineAsset",
                        "OtherCustomPipelineAsset","malformed near-match"],
        "tested_absent_or_unsupported_shaders":True,
        "shader_selection_source_shared_by_author_and_adapter":True,
        "pipeline_color_source_shared_by_author_and_adapter":True,
        "color_validated_before_creating_unity_asset":True,
    }
    (out/"acceptance-receipt.json").write_text(json.dumps(receipt,indent=2)+"\n")
    return receipt


if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("new_private_output",type=Path)
    args=parser.parse_args()
    print(json.dumps(run(args.new_private_output),indent=2))
