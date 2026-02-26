# Repository Guidelines

## Project Structure & Module Organization

- `src/main/`: Electron main process (window lifecycle, IPC handlers, Python bridge).
- `src/preload/`: `contextBridge` API exposed to the renderer.
- `src/renderer/src/`: React + TypeScript UI (`components/`, `modules/test-pattern/`, `stores/`, `api/`, `utils/`).
- `python/app/`: FastAPI backend (`api/modules/` endpoints, `core/` image/color/HDR logic, `services/` export workflows).
- `python/tests/`: `pytest` tests for backend/core logic.
- `scripts/`: cross-platform build helpers (`build.bat`, `build.sh`).
- `resources/`: packaging assets (icons, entitlements, profiles).

## Build, Test, and Development Commands

- `npm install`: install Electron/renderer dependencies.
- `cd python && python -m venv .venv && .venv\Scripts\pip install -e ".[dev]"`: create backend venv and install dev deps (use `.venv/bin/pip` on macOS/Linux).
- `npm run dev`: start Electron dev mode; the app launches the Python backend automatically.
- `cd python && .venv\Scripts\python -m pytest tests -v`: run backend tests (`.venv/bin/python` on macOS/Linux).
- `npm run build`: build Electron main/preload/renderer bundles.
- `scripts\build.bat` (Windows) or `./scripts/build.sh [win|mac|all]`: package backend + desktop app.

## Coding Style & Naming Conventions

- TypeScript/React: 2-space indentation, single quotes, no semicolons in existing files.
- Use `PascalCase` for React components (`AppLayout.tsx`), `camelCase` for functions/variables, and `useXStore` for Zustand stores.
- Python: 4-space indentation, `snake_case` functions/modules, type hints for public/core functions.
- Keep backend domain logic in `python/app/core/`; keep HTTP routing concerns in `python/app/api/modules/`.

## Testing Guidelines

- Framework: `pytest` (configured in `python/pyproject.toml`).
- Add tests under `python/tests/` using `test_*.py` filenames and `test_*` function names.
- Prioritize coverage for math, image generation, color-space, and export-path changes.
- No frontend test suite is configured yet; include manual verification steps for UI changes.

## Commit & Pull Request Guidelines

- Follow the existing conventional style: `feat: ...`, `fix: ...`, `docs: ...` (imperative, concise subject).
- Keep commits focused by area (renderer, backend core, packaging).
- PRs should include: summary, affected modules/paths, test/manual verification, and screenshots for UI changes.
- Link related issues when applicable and note platform-specific validation (Windows/macOS) for packaging changes.

## Build Artifacts & Environment Tips

- Do not commit generated outputs such as `dist/`, `out/`, `node_modules/`, or local venvs.
- PyInstaller outputs may appear under `python/build/` and `python/dist/`; clean them before opening a PR unless the change is packaging-related.
- Video export features depend on `FFmpeg` being available on `PATH`.
