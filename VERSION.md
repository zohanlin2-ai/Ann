# Ann Version Information

## Current Release

| Component | Version | Notes |
| --- | --- | --- |
| Ann Core | 0.0.5 | Ann-only GitHub updater and module registry |
| Python | >=3.10 | Development runtime |
| PySide6 | 6.8.0.2 | Desktop UI framework |
| Module Catalog Schema | 1 | GitHub catalog format |

## Version History

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
