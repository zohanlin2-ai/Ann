# Changelog

All notable changes to this project will be documented in this file.

This project intends to follow the principles of [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and [Semantic Versioning](https://semver.org/).

## [Unreleased]

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

### Fixed

- Pinned PySide6 to 6.8.0.2 so the initial release supports Python 3.13.
- Set the minimum supported Python version to 3.10.
- Documented the separation between Python-based development and bundled end-user releases.
- Added the verified Windows CPython virtual-environment setup instructions.

## [0.1.0] - TBD

### Added

- Initial public project structure.
