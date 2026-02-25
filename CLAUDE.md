# c0lor-mem

Display testing image generation desktop tool for display reviewers.
First module: APL test pattern generator (black bg + white shape at X% area).

## Tech Stack

- **Desktop**: Electron + electron-vite (vite@5.x required for electron-vite@2.3.0 compat)
- **Frontend**: React 18 + TypeScript + Ant Design 5 (dark theme) + Zustand 5
- **Backend**: Python 3.14 + FastAPI + Pillow + pillow-heif + colour-science
- **Video**: FFmpeg (subprocess)
- **Communication**: HTTP + WebSocket (Electron spawns Python, polls /health)

## Architecture

- Electron main → spawns Python FastAPI (port 18100-18200)
- `src/main/python-bridge.ts`: free port → spawn uvicorn → poll /health → IPC backend URL
- Dev: project venv `python/.venv/`, Prod: PyInstaller bundled exe
- Preload exposes: openDirectory, saveFile, openPath, showItemInFolder, onBackendUrl
- WebSocket `/ws/progress` for batch progress updates

## Project Structure

### Python Backend (`python/app/`)

- `core/models.py` - Pydantic models, HdrMode enum (`none`, `ultra-hdr`, `hdr10-pq`)
- `core/pattern_generator.py` - Rectangle/Circle APL math + image generation
- `core/color_space.py` - ICC profile generation (sRGB/P3/Rec.2020), custom binary builder
- `core/hdr_gainmap.py` - Ultra HDR (ISO 21496-1) MPF JPEG with gain map
- `core/pq.py` - PQ (ST 2084) OETF math + 16-bit PNG with cICP chunk
- `core/video_encoder.py` - FFmpeg H.264/H.265, 10-bit PQ for HDR (imports from pq.py)
- `services/export_service.py` - Single export orchestrator (all formats + HDR)
- `services/batch_service.py` - Async batch with progress callback
- `routers/test_pattern.py` - FastAPI route definitions

### Electron Frontend (`src/`)

- `main/index.ts` - Electron main process
- `main/python-bridge.ts` - Python process lifecycle management
- `preload/index.ts` - IPC bridge
- `renderer/src/modules/test-pattern/PatternConfigForm.tsx` - Main config UI
- `renderer/src/stores/testPatternStore.ts` - Zustand store, HdrMode type

## API Endpoints

- GET `/api/v1/health`
- POST `/api/v1/test-pattern/preview`
- POST `/api/v1/test-pattern/generate`
- POST `/api/v1/test-pattern/batch` (202 async)
- GET `/api/v1/test-pattern/batch/{id}/status`
- POST `/api/v1/test-pattern/batch/{id}/cancel`
- WS `/ws/progress`

## HDR Modes

- **Ultra HDR** (`ultra-hdr`): ISO 21496-1 JPEG with gain map (1/4 downsampled), JPEG format only
- **HDR10 PQ** (`hdr10-pq`): ST 2084 PQ transfer, 16-bit PNG (cICP chunk) + H.264/H.265 10-bit video
- Apple Gain Map was removed in v0.1.0 (pillow-heif cannot write gain map aux image, MakerApple EXIF unreliable)

## Format Compatibility Matrix

| HDR Mode | Allowed Formats |
|----------|----------------|
| `none` (SDR) | png, jpeg, heif, h264, h265 |
| `ultra-hdr` | jpeg |
| `hdr10-pq` | png, h264, h265 |

Frontend enforces this in `PatternConfigForm.tsx` via `FORMAT_BY_HDR` mapping.

## Commands

```bash
# Dev
npm run dev

# Build frontend
npx electron-vite build

# Python tests
cd python && .venv/Scripts/python -m pytest tests/ -v

# Full production build (3 steps)
cd python && .venv/Scripts/pyinstaller backend.spec --noconfirm
npx electron-vite build
npx electron-builder --win nsis --config
```

## Build Notes

- PyInstaller spec: `python/backend.spec` — hiddenimports include all `app.core.*` and `app.services.*` modules
- electron-builder config: `electron-builder.yml` — copies `python/dist/c0lor-mem-backend/` into resources
- Output installer: `dist/c0lor-mem Setup X.X.X.exe`
