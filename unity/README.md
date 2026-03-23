# Unity Workspace

This repo uses the intended Unity package workflow:
- `projects/` contains Unity projects.
- `packages/` contains reusable local UPM packages.
- `tools/` contains bootstrap scripts and project-specific generation helpers.

Recommended pattern:
- keep shared code in `packages/com.hpr.*`
- reference those packages from each Unity project via `Packages/manifest.json`
- only keep project-specific scenes/assets/scripts inside each project folder

Local package dependency example:
```json
{
  "dependencies": {
    "com.hpr.foundation": "file:../../../packages/com.hpr.foundation"
  }
}
```
