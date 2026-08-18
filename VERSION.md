# Ann Version Information

## Current Release

| Component | Version | Notes |
| --- | --- | --- |
| Ann Core | 0.0.8 | Security Monitor dependency included in root installation |
| Python | >=3.10 | Development runtime |
| PySide6 | 6.8.0.2 | Desktop UI framework |
| Module Catalog Schema | 1 | GitHub catalog format |

## Version History

### 0.0.8

- Include the Security Monitor packet-capture dependency in the root installation flow.

### 0.0.7

- Download and validate a complete staged Ann project before applying it automatically.
- Preserve local virtual environments, Git history, Module Registry, downloaded modules, and the stable launcher during updates.

### 0.0.6

- Add local optional-module discovery and safe enabled-module loading.
- Add the Ann Security Monitor MVP and Security Center settings UI.
- Add session-only security pause and resume controls.

### 0.0.5

- Rename the Core update action to Update Ann.
- Limit Ann Updater to checking and updating Ann Core.
- Show Ann Updater in update checks as bundled with Ann Core.

### 0.0.4

- Register Ann Core as a required system module.
- Remove the context-menu ellipses from Update and Modules.

### 0.0.3

- Move Ann Core into `Ann_core/` and add the stable root launcher.
- Add the GitHub-backed Ann Updater, module registry, and staged Core update flow.
- Add Module List checkboxes and module/update chat commands.

### 0.0.2

- Add a bottom-right initial Bubble position.
- Add Bubble right-click actions for Update, About Ann, and Exit Ann.
- Add `exit` and `quit` commands with case-insensitive Y/N confirmation.

### 0.0.1

- Initial Ann desktop prototype.
