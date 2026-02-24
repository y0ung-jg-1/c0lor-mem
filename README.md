# c0lor-mem

为显示领域自媒体人打造的测试图像生成桌面工具。

当前模块：**APL 测试图生成器** —— 输入屏幕分辨率，生成 1%\~100% 白色占比的测试图（黑底白色图形），支持多种色彩空间、HDR Gain Map 导出、静帧视频导出。

## 功能特性

- **APL 测试图案**：矩形 / 圆形，1%\~100% 白色面积占比
- **28+ 设备预设**：iPhone、Samsung、Xiaomi、Pixel、HUAWEI 等主流机型分辨率
- **色彩空间**：sRGB (Rec.709)、Display P3、Rec.2020，自动嵌入 ICC Profile
- **导出格式**：PNG、JPEG、HEIF、H.264 视频、H.265 视频
- **HDR 支持**：Apple Gain Map (MPF JPEG / HEIF)、Ultra HDR (Android)、10-bit PQ 视频
- **批量导出**：自定义 APL 范围和步长，WebSocket 实时进度，支持取消
- **跨平台**：Windows + macOS

## 技术栈

| 层 | 技术 |
|---|------|
| 桌面框架 | Electron + electron-vite |
| 前端 | React + TypeScript + Ant Design (暗色主题) + Zustand |
| 后端 | Python + FastAPI |
| 图像处理 | Pillow + pillow-heif + colour-science |
| 视频编码 | FFmpeg (子进程调用) |
| 打包 | PyInstaller (Python) + electron-builder (Electron) |

## 环境要求

- **Node.js** >= 18
- **Python** >= 3.10
- **FFmpeg**（视频导出需要，需加入 PATH）

## 快速开始

### 1. 克隆仓库

```bash
git clone https://github.com/y0ung-jg-1/c0lor-mem.git
cd c0lor-mem
```

### 2. 安装前端依赖

```bash
npm install
```

### 3. 安装 Python 后端依赖

```bash
cd python
python -m venv .venv

# Windows
.venv\Scripts\pip install -e ".[dev]"

# macOS / Linux
.venv/bin/pip install -e ".[dev]"
```

### 4. 启动开发环境

```bash
# 回到项目根目录
cd ..
npm run dev
```

Electron 会自动启动 Python 后端（从项目 venv），打开应用窗口后底部状态栏显示「后端就绪」即可正常使用。

## 运行测试

```bash
cd python

# Windows
.venv\Scripts\python -m pytest tests/ -v

# macOS / Linux
.venv/bin/python -m pytest tests/ -v
```

## 生产构建

### 完整打包流程

#### Windows

```bash
scripts\build.bat
```

#### macOS / Linux

```bash
chmod +x scripts/build.sh
./scripts/build.sh mac    # 仅 macOS
./scripts/build.sh win    # 仅 Windows
./scripts/build.sh all    # 全平台
```

### 手动分步构建

```bash
# 1. 打包 Python 后端
cd python
.venv\Scripts\pip install pyinstaller
.venv\Scripts\pyinstaller backend.spec --clean --noconfirm
cd ..

# 2. 构建 Electron 前端
npm run build

# 3. 打包安装程序
npm run build:win   # Windows NSIS 安装包
npm run build:mac   # macOS DMG
```

产物输出到 `dist/` 目录。

## 项目结构

```
c0lor-mem/
├── src/
│   ├── main/                        # Electron 主进程
│   │   ├── index.ts                 # 窗口创建、生命周期
│   │   ├── python-bridge.ts         # 启动/监控 Python 后端
│   │   └── ipc-handlers.ts          # IPC：文件对话框等
│   ├── preload/
│   │   └── index.ts                 # contextBridge API
│   └── renderer/src/
│       ├── App.tsx                   # Ant Design 暗色主题入口
│       ├── api/                      # HTTP 客户端 + WebSocket
│       ├── stores/                   # Zustand 状态管理
│       ├── components/Layout/        # 应用布局、侧栏、状态栏
│       ├── modules/test-pattern/     # APL 测试图 UI 组件
│       └── utils/                    # 预览数学计算、设备预设
├── python/
│   ├── app/
│   │   ├── main.py                  # FastAPI 入口
│   │   ├── api/modules/             # API 端点
│   │   ├── core/                    # 图案生成、色彩空间、HDR、视频
│   │   └── services/                # 导出服务、批量服务
│   ├── tests/                       # pytest 测试
│   ├── pyproject.toml
│   └── backend.spec                 # PyInstaller 配置
├── resources/                       # ICC profiles、图标、entitlements
├── scripts/                         # 构建脚本
├── electron-builder.yml
└── electron.vite.config.ts
```

## License

ISC
