using System;
using System.Collections;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Reflection;
using UnityEditor;
using UnityEngine;

public static class HprAssetStoreToolsValidatorRunner
{
    public static void ValidateFromEnvironment()
    {
        string resultsPath = Environment.GetEnvironmentVariable("HPR_AST_RESULTS") ?? string.Empty;
        string rawPaths = Environment.GetEnvironmentVariable("HPR_AST_PATHS") ?? string.Empty;
        if (string.IsNullOrWhiteSpace(resultsPath) || string.IsNullOrWhiteSpace(rawPaths))
        {
            Debug.LogError("HPR_AST_RESULTS or HPR_AST_PATHS is missing.");
            EditorApplication.Exit(1);
            return;
        }

        Assembly? assetStoreAssembly = AppDomain.CurrentDomain.GetAssemblies()
            .FirstOrDefault(assembly => string.Equals(assembly.GetName().Name, "asset-store-tools-editor", StringComparison.Ordinal));
        if (assetStoreAssembly == null)
        {
            Debug.LogError("asset-store-tools-editor assembly was not loaded.");
            EditorApplication.Exit(1);
            return;
        }

        Type settingsType = assetStoreAssembly.GetType("AssetStoreTools.Validator.Data.CurrentProjectValidationSettings", true)!;
        Type validationTypeEnum = assetStoreAssembly.GetType("AssetStoreTools.Validator.Data.ValidationType", true)!;
        Type validatorType = assetStoreAssembly.GetType("AssetStoreTools.Validator.CurrentProjectValidator", true)!;

        object settings = Activator.CreateInstance(settingsType, true)!;
        settingsType.GetField("Category", BindingFlags.Instance | BindingFlags.Public | BindingFlags.NonPublic)?.SetValue(settings, string.Empty);
        settingsType.GetField("ValidationPaths", BindingFlags.Instance | BindingFlags.Public | BindingFlags.NonPublic)?.SetValue(
            settings,
            rawPaths.Split(new[] { ';' }, StringSplitOptions.RemoveEmptyEntries).ToList());
        settingsType.GetField("ValidationType", BindingFlags.Instance | BindingFlags.Public | BindingFlags.NonPublic)?.SetValue(
            settings,
            Enum.Parse(validationTypeEnum, "UnityPackage"));

        object validator = Activator.CreateInstance(
            validatorType,
            BindingFlags.Instance | BindingFlags.Public | BindingFlags.NonPublic,
            binder: null,
            args: new[] { settings },
            culture: null)!;

        object? validationResult = validatorType.GetMethod("Validate", BindingFlags.Instance | BindingFlags.Public | BindingFlags.NonPublic)?.Invoke(validator, null);
        if (validationResult == null)
        {
            Debug.LogError("Asset Store Tools validator returned null.");
            EditorApplication.Exit(1);
            return;
        }

        Type resultType = validationResult.GetType();
        string status = resultType.GetField("Status", BindingFlags.Instance | BindingFlags.Public | BindingFlags.NonPublic)?.GetValue(validationResult)?.ToString() ?? "Unknown";
        bool hadCompilationErrors = (bool)(resultType.GetField("HadCompilationErrors", BindingFlags.Instance | BindingFlags.Public | BindingFlags.NonPublic)?.GetValue(validationResult) ?? false);
        Exception? exception = resultType.GetField("Exception", BindingFlags.Instance | BindingFlags.Public | BindingFlags.NonPublic)?.GetValue(validationResult) as Exception;
        IEnumerable<object> tests = (((IEnumerable?)resultType.GetField("Tests", BindingFlags.Instance | BindingFlags.Public | BindingFlags.NonPublic)?.GetValue(validationResult)) ?? Array.Empty<object>())
            .Cast<object>();

        var lines = new List<string>
        {
            $"status: {status}",
            $"hadCompilationErrors: {hadCompilationErrors}"
        };

        if (exception != null)
        {
            lines.Add($"exception: {exception}");
        }

        int issueCount = 0;
        foreach (object test in tests)
        {
            Type testType = test.GetType();
            string title = testType.GetField("Title", BindingFlags.Instance | BindingFlags.Public | BindingFlags.NonPublic)?.GetValue(test)?.ToString() ?? testType.Name;
            object? testResult = testType.GetField("Result", BindingFlags.Instance | BindingFlags.Public | BindingFlags.NonPublic)?.GetValue(test);
            if (testResult == null)
            {
                continue;
            }

            Type testResultType = testResult.GetType();
            string testStatus = testResultType.GetField("Status", BindingFlags.Instance | BindingFlags.Public | BindingFlags.NonPublic)?.GetValue(testResult)?.ToString() ?? "Unknown";
            if (string.Equals(testStatus, "Pass", StringComparison.Ordinal))
            {
                continue;
            }

            issueCount++;
            lines.Add($"test: {title}");
            lines.Add($"  result: {testStatus}");

            int messageCount = (int)(testResultType.GetProperty("MessageCount", BindingFlags.Instance | BindingFlags.Public | BindingFlags.NonPublic)?.GetValue(testResult) ?? 0);
            MethodInfo? getMessage = testResultType.GetMethod("GetMessage", BindingFlags.Instance | BindingFlags.Public | BindingFlags.NonPublic);
            for (int index = 0; index < messageCount; index++)
            {
                object? message = getMessage?.Invoke(testResult, new object[] { index });
                if (message == null)
                {
                    continue;
                }

                string? messageText = message.GetType().GetMethod("GetText", BindingFlags.Instance | BindingFlags.Public | BindingFlags.NonPublic)?.Invoke(message, null)?.ToString();
                if (!string.IsNullOrWhiteSpace(messageText))
                {
                    lines.Add($"    - {messageText}");
                }
            }
        }

        Directory.CreateDirectory(Path.GetDirectoryName(resultsPath) ?? ".");
        File.WriteAllLines(resultsPath, lines);

        if (!string.Equals(status, "RanToCompletion", StringComparison.Ordinal) || hadCompilationErrors || exception != null || issueCount > 0)
        {
            Debug.LogError($"Asset Store Tools validation failed. Results: {resultsPath}");
            EditorApplication.Exit(1);
            return;
        }

        Debug.Log($"Asset Store Tools validation passed. Results: {resultsPath}");
        EditorApplication.Exit(0);
    }
}
