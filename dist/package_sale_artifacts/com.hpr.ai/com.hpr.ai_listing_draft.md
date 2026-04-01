# HPR AI Asset Store Listing Draft

## Title
HPR AI

## Short description
Reusable enemy and agent data definitions for AI-driven gameplay packages.

## Long description
Reusable enemy-definition assets for Unity projects that want authored AI archetypes without hardcoding enemy tuning directly into runtime scripts.

Use this package when you want:
- enemy archetypes authored as `ScriptableObject` assets
- stable ids and behavior categories for AI-driven runtime systems
- a reusable data schema for health, speed, range, and attack tuning

Included:
- `EnemyData`
- `EnemyAIType`
- `EnemyAttackStyle`

Installation summary:
- Add `com.hpr.ai` to your Unity project.
- Reference `HPR.Ai.Runtime` from dependent asmdefs.
- Create enemy assets via `Assets > Create > HPR > AI > Enemy`.
- Feed those assets into your own runtime enemy/agent system.

Documentation summary:
Reusable enemy and agent data definitions for AI-driven gameplay packages.

Known product limits:
- this package defines AI data only; it does not include a full runtime behavior tree or navigation system
- combat execution and target selection remain the responsibility of the consuming project

## Technical details
- Package name: `com.hpr.ai`
- Version: `0.1.0`
- Unity version: `6000.4`
- Dependencies: none
- Sample import path: `Samples~/Demo`
- Screenshot: `screenshots/com.hpr.ai.png`
- Artifact info: `com.hpr.ai_info.txt`

## Human-only fields to fill before upload
- Price
- Category/subcategory
- Support email or support URL
- Marketing screenshots selection and ordering
- Package icon / cover art if you want a bespoke visual instead of the captured demo screenshot

## Suggested keywords
- ai
- enemy
- agent
- data
