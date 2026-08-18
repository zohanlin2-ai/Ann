# Changelog

All notable changes to this project will be documented in this file.

This project intends to follow the principles of [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and [Semantic Versioning](https://semver.org/).

## [0.0.4] - TBD

### Added

- Initial project documentation for Ann.
- A modular architecture direction for the Ann AI Assistant.
- A GitHub-based module catalog and update concept.
- Python project metadata and pinned runtime dependency records.
- Dependency-aware application launcher that reports missing or incompatible packages.
- Initial PySide6 desktop interface with a draggable status bubble and command chat window.

### Changed

- Display the full "Ann" name in the Bubble.
- Keep Ann running when the command chat window is closed; the Bubble remains available.
- Position the Bubble at the primary screen's bottom-right corner when Ann starts.

### Added

- Bubble right-click menu with Update, About Ann, and Exit Ann actions.
- About Ann dialog that displays the declared current-release information from `VERSION.md`.
- `exit` and `quit` commands with case-insensitive Y/N confirmation.
- Modular `Ann_core/` directory, root launcher, and staged `backup_ann/` Core update flow.
- GitHub-backed Ann Updater system module and catalog format.
- Persistent Module Registry, Module List checkboxes, and module enable/disable commands.
- Chat commands for checking, downloading, and applying Core or module updates.
- Register Ann Core as a required system module with its own manifest and documentation.

### Changed

- Rename Bubble context-menu actions from `Update…` and `Modules…` to `Update` and `Modules`.

### Fixed

- Pinned PySide6 to 6.8.0.2 so the initial release supports Python 3.13.
- Set the minimum supported Python version to 3.10.
- Documented the separation between Python-based development and bundled end-user releases.
- Added the verified Windows CPython virtual-environment setup instructions.
- Documented the project versioning rules.

## [0.0.1] - TBD

### Added

- Initial public project structure.
