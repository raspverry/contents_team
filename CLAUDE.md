# CLAUDE.md - AI Assistant Guide for contents_team

## Project Overview

This is the `contents_team` repository. It is currently in its initial setup phase.

> **Note:** This file should be updated as the project evolves. When adding new tools,
> frameworks, directories, or conventions, reflect those changes here.

## Repository Structure

```
contents_team/
├── CLAUDE.md          # This file - AI assistant guide
└── .git/              # Git configuration
```

<!-- Update the tree above as the project grows. -->

## Development Setup

### Prerequisites

<!-- List required tools, runtimes, and versions here as they are adopted. Example: -->
<!-- - Node.js >= 18 -->
<!-- - Python >= 3.11 -->
<!-- - Docker -->

_To be defined as the project takes shape._

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd contents_team

# Install dependencies (update when a package manager is chosen)
# npm install / pip install -r requirements.txt / etc.
```

## Build, Test, and Lint Commands

<!-- Fill in actual commands as tooling is configured. -->

| Action | Command |
|--------|---------|
| Install dependencies | _TBD_ |
| Run all tests | _TBD_ |
| Run a single test | _TBD_ |
| Lint / format check | _TBD_ |
| Build | _TBD_ |
| Start dev server | _TBD_ |

## Git Workflow

- **Default branch:** `main`
- Feature branches should use descriptive names (e.g., `feature/add-auth`, `fix/header-bug`).
- Write clear, concise commit messages describing _why_ a change was made.
- Keep commits focused on a single logical change.

## Code Conventions

<!-- Update these as the team establishes patterns. -->

- Follow the style enforced by the project's linter/formatter once configured.
- Prefer clarity over cleverness.
- Keep functions small and single-purpose.
- Write tests for new functionality.

## Architecture

<!-- Describe high-level architecture, key modules, data flow, and design decisions here. -->

_To be documented as the codebase develops._

## Key Files and Directories

<!-- Map out important files as they are created. Example: -->
<!-- - `src/` - Application source code -->
<!-- - `tests/` - Test suites -->
<!-- - `docs/` - Documentation -->
<!-- - `scripts/` - Build and utility scripts -->

_To be populated as the project structure is established._

## AI Assistant Guidelines

When working in this repository:

1. **Read before editing** - Always read a file before modifying it.
2. **Minimal changes** - Only make changes that are directly requested or clearly necessary.
3. **No over-engineering** - Keep solutions simple; don't add speculative features.
4. **Update this file** - When adding significant new tooling, directories, or conventions, update this CLAUDE.md to keep it current.
5. **Check for tests** - Run the test suite after making changes (once tests exist).
6. **Check for lint** - Run the linter after making changes (once a linter is configured).
7. **Security** - Do not commit secrets, credentials, or `.env` files.
