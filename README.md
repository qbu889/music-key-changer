# 🎵 Music Key Changer · 音乐升降调

简单、免费、在线的音乐升降调工具。上传音频 → 选择升降调半音数 → 即时试听并下载。
前端为 **Apple 风格**设计，后端为 **FastAPI + Librosa**，全程会话隔离、24h 自动清理。

```
用户旅程：上传 → 调整 → 试听 → 下载
```

## 快速开始

```bash
# 1. 初始化后端环境（首次运行）
cd backend
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt

# 2. 启动后端（会自动托管 frontend/ 目录）
.venv/bin/python -m uvicorn main:app --reload
# 或：./run.sh

# 3. 打开浏览器
http://localhost:8000/
```

处理引擎会自动选择：

- **有后端**：上传到 `/api/v1/process`，由 Librosa 处理，结果从 `/api/v1/download/{id}` 下载。
- **离线 / `file://`**：自动回退到浏览器内相位声码器，无需后端。

## 目录结构

```
music-key-changer/
├── frontend/                    # Apple 风格前端（原生 HTML/CSS/JS）
│   ├── index.html
│   ├── styles.css
│   └── app.js                   # 引擎自动选择 + 音频 DSP + 波形
├── backend/                     # FastAPI 后端
│   ├── main.py                  # 路由、会话中间件、静态托管、后台清理
│   ├── audio/
│   │   ├── config.py            # 格式/大小/时长限制、路径、错误码
│   │   └── processor.py         # 校验 + Librosa pitch_shift + WAV 编码
│   ├── tests/                   # 处理器单测 + API 端到端测试
│   ├── requirements.txt
│   └── run.sh
└── docs/requirements.md         # 需求设计文档
```

## 功能

| 模块 | 说明 |
|------|------|
| 📤 上传 | 拖拽/点击，格式（MP3·WAV·FLAC·AAC·OGG）、大小（≤50MB）、时长（≤10min）校验 |
| 🎚️ 升降调 | -12 ~ +12 半音滑块 + 常用预设，实时显示目标调性 |
| 🧠 处理 | 后端：Librosa `pitch_shift`（kaiser_best）；本地：自实现 FFT + 相位声码器 |
| 📊 可视化 | Canvas 波形 + 播放/暂停/拖动进度 |
| 📥 下载 | 一键下载 16-bit PCM WAV |

## 隐私与安全

- 每个会话文件隔离在 `user_data/<session_id>/` 下。
- 后台线程每小时清理 24 小时前的过期会话。
- 处理不存储用户文件超过 24h，无用户系统。

## 测试

```bash
cd backend
.venv/bin/pip install -r requirements.txt   # 含 pytest
.venv/bin/python -m pytest -q
```

覆盖：音频校验、升降调长度保持、WAV 回读、API 上传→处理→下载全流程、错误码、前端托管。

## API

| 方法 | 端点 | 说明 |
|------|------|------|
| GET | `/api/health` | 健康检查 / 支持格式 |
| POST | `/api/v1/process` | 上传并处理（`file` + `semitones`）→ `{file_id, output_url}` |
| GET | `/api/v1/download/{file_id}` | 下载处理结果（WAV） |
| GET | `/api/v1/session/info` | 会话信息 |
| DELETE | `/api/v1/session/cleanup` | 清理会话文件 |

## 技术选型

- **前端**：原生 HTML/CSS/JS（无框架、无构建），Apple 设计系统。
- **后端**：FastAPI + uvicorn，Librosa 音频处理，soundfile 读写，numpy。
- **处理算法**：Librosa `effects.pitch_shift`（时域升降调，保持 tempo 与时长）。
