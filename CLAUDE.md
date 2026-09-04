# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.
本文件为 Claude Code (claude.ai/code) 在本仓库中开发提供指引（中英文对照）。

> ⚠️ **每次改动后请同步更新本文档的 `Project Status` 与 `Unfinished` 段落。**
> Please keep the `Project Status` and `Unfinished` sections of this file in sync after every change.

---

## Project Status / 项目状态

**Last updated: 2026-09-04**

This repository is in a **working MVP state**. The core product is implemented and tested:
本仓库已处于**可用的 MVP 状态**，核心功能已实现并通过测试（`pytest` 16 passed）。

- ✅ 完整实现见 `backend/`（FastAPI + Librosa + Demucs）与 `frontend/`（原生 HTML/CSS/JS）。
- ✅ 核心流程：上传 → 选音 → 处理 → 试听 → 下载，端到端可用。
- ✅ **升降调默认先做声部分离（人声/伴奏），分别处理后混回**，显著改善人声质感（见下方 `Actual Stack`）。
- ✅ 双引擎：有后端走 Librosa/Demucs；`file://` 离线自动回退到浏览器内相位声码器。
- ⬜ `docs/requirements.md` 中列出的 **P1/P2 高级功能尚未实现**（见下方 `Unfinished`）。
- ⬜ `docs/api.md` 尚未创建（需求 §8.2 引用了它）。

编码前请先读 `docs/requirements.md`（完整规格）和本文档的 `Unfinished` 段。

---

## What This Project Is / 项目简介

"Music Key Changer"（音乐升降调处理平台）— a web tool that shifts an audio track's key by ±12 semitones. User flow: upload audio → choose semitone shift → process → preview → download. Full spec (user stories, architecture, data models, API design, roadmap) lives in `docs/requirements.md`.
"Music Key Changer" 是一个音乐升降调网页工具，可将音频的调性整体平移 ±12 半音。用户流程：上传音频 → 选择升降调半音数 → 处理 → 试听 → 下载。完整规格见 `docs/requirements.md`。

---

## Actual Stack (implemented) / 实际技术栈

- **Backend / 后端:** FastAPI (async, uvicorn) + `librosa`（核心 `pitch_shift`，`kaiser_best`）+ `demucs`+`diffq`（声部分离，模型 `mdx_q`）+ `soundfile`（WAV 编码 `PCM_16`）+ numpy + `torch`。会话隔离存储于 `user_data/<session_id>/`，后台线程每小时清理 24h 过期文件。
  FastAPI（异步）+ librosa（升降调）+ Demucs/diffq（声部分离）+ soundfile（WAV 编码）+ torch + numpy；会话隔离 + 定时清理。

  **升降调管线（`audio/processor.py::pitch_shift_separated`）**：先由 `audio/separators.py` 用 Demucs 把音频拆成人声/伴奏 → 分别做保留共振峰的 `librosa.pitch_shift` → 混回并采样率还原到输入。任一环节出错（如模型未下载/网络故障）**自动回退到整体直接升降调**，保证功能可用。`audio/config.py::ProcessingConfig` 可开关（`USE_SEPARATION`）与换模型（`SEPARATION_MODEL`）。
- **Frontend / 前端:** 原生 HTML/CSS/JS（无框架、无构建）。自定义 Canvas 波形 + Web Audio API transport（播放/暂停/拖动）。**未用** Tailwind / Wavesurfer.js（需求里写的是 Wavesurfer，实际用自实现 Canvas）。离线兜底为自写 FFT（radix-2 Cooley-Tukey）+ 相位声码器。
  Vanilla HTML/CSS/JS（无框架）；自实现 Canvas 波形 + Web Audio；离线自写 FFT 相位声码器。
- **Tests / 测试:** pytest，位于 `backend/tests/`（`test_processor.py` 音频单测 + `test_api.py` 端到端）。

---

## Key Constraints / 关键约束

- Supported formats / 支持格式: MP3, WAV, FLAC, AAC, OGG（外加 m4a/mp4）。
- Per-file limits / 单文件限制: ≤ 50 MB，≤ 600 s（10 分钟）。
- Shift range / 升降调范围: semitones −12 ~ +12（默认 0；负值降调，正值升调）。
- Output format / 输出格式: ⚠️ **当前始终输出 16-bit PCM WAV**；需求要求"默认跟随输入格式"（尚未实现）。
- Files are temporary / 文件为临时文件：会话隔离，24h 自动清理（`audio/config.py::Paths.TTL_SECONDS`）。
- 无用户系统、无持久化历史、无限流、无配额。

---

## Unfinished / 待开发（按需求文档优先级）

**P1（重要）：**
1. **调性自动检测**（US-07）— 真正识别原曲调性（需求建议 CREPE / Magenta MelodyRNN）。当前 `frontend/app.js::describeKey()` 仅按"假设输入=C 大调"估算。
2. **输出格式跟随输入** — 当前后端恒输出 WAV，需求要求默认跟随输入格式（MP3/WAV/FLAC）。

**P2（锦上添花）：**
3. **批量处理** — 无 `/api/v1/batch-process`，前端仅单文件。
4. **历史记录** — 仅有内存 process_count 计数，无持久化。
5. **音质增强** — ✅ **声部分离式升降调已实现**（`pitch_shift_separated`，Demucs `mdx_q`，默认开启，失败自动回退）。**和声生成 / AI 推荐调性 / 社交分享 / API 开放** — 仍为需求 P2/P3。

**非功能 / 合规：**
6. **限流（SlowAPI）与配额管理** — 需求 §4 建议 10次/小时、每日上传/处理上限。
7. **WebSocket 实时进度** — 当前为同步阻塞 + 前端模拟进度条。
8. **免责声明 / 条款确认** — 需求 §4.4，当前仅一句隐私文案，无正式弹窗。

**文档：**
9. **`docs/api.md`** — 需求 §8.2 引用，尚未创建。

---

## Project Layout / 项目结构（实际）

```
backend/
├── main.py                 # FastAPI 入口/路由/会话中间件/静态托管/后台清理
├── audio/
│   ├── config.py           # 格式/大小/时长限制、路径、错误码、FRONTEND_DIR、ProcessingConfig
│   ├── processor.py        # 校验 + pitch_shift_separated(分离+Librosa)+ WAV 编码（与 FastAPI 解耦）
│   └── separators.py       # Demucs 声部分离（mdx_q）；懒加载 + 缓存；HF→hf-mirror 镜像路由；MPS/CPU 自动切换
├── tests/                  # test_processor.py（单测）+ test_api.py（端到端）
├── conftest.py
├── requirements.txt
└── run.sh
frontend/
├── index.html              # Apple 风格界面
├── styles.css
└── app.js                  # 引擎自动选择 + 音频 DSP(FFT/相位声码器) + 波形 + transport
docs/requirements.md        # 完整需求设计文档（编码前必读）
```

---

## Common Commands / 常用命令

- Install deps / 安装依赖: `cd backend && python3 -m venv .venv && .venv/bin/pip install -r requirements.txt`
  - ⚠️ 首次运行升降调会**下载 Demucs `mdx_q` 模型**（约 500MB，缓存到 `~/.cache/huggingface`）。若 HuggingFace 不可达（如国内网络），`separators.py` 会自动把权重下载路由到 `hf-mirror.com`；如需手动禁用镜像设环境变量 `DEMUCS_HF_MIRROR=0`。已安装 `diffq`（mdx_q 为量化模型，必需）。
- Run app / 启动应用: `cd backend && .venv/bin/python -m uvicorn main:app --reload`（或 `./run.sh`），前端在 http://localhost:8000/
- Run tests / 运行测试: `cd backend && .venv/bin/python -m pytest -q`
- Run a single test / 运行单个测试: `cd backend && .venv/bin/python -m pytest tests/test_file.py::test_name`

---

## Conventions / 开发约定

- Keep the audio-processing logic decoupled from FastAPI handlers so it can be unit-tested without spinning up the server.
  将音频处理逻辑与 FastAPI 处理函数解耦，便于不启动服务即可单元测试（见 `audio/processor.py`）。
- Validate uploads (extension, size, duration) before invoking librosa.
  调用 librosa 前先校验上传文件（扩展名、大小、时长）。
- Clean up temporary files in a `finally` block / periodic thread so failures don't leak data.
  失败时用 `finally` 清理，并有后台线程定期清理过期会话。
- Error handling / 错误处理: 用 `audio/processor.py::AudioError` 携带 `ErrorCode`，主路由映射为 400/500 JSON。
