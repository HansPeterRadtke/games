# Package Validation Tools

This folder contains repeatable helpers for validating local HPR Unity packages outside the main game project.

Current entry point:
- `validate_local_packages.sh` - creates a clean temporary Unity project, links the requested local packages plus their local HPR dependencies, opens the project in batch mode, and fails on compile/import errors found in the Unity log.

Use this before claiming a package is reusable outside `fps_demo`.
