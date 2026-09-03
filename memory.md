# 项目记忆 · Music Key Changer（音乐升降调）

> 本文件记录项目现状、技术要点与每日工作轨迹，便于后续快速接手。
> 最后更新：2026-09-03

---

## 1. 项目概述

**Music Key Changer** 是一个在线音乐升降调工具：上传音频 → 选择 ±12 半音 → 处理 → 试听 → 下载。
核心卖点：简单、免费、隐私优先（文件不出浏览器，24h 自动清理），Apple 风格界面。

- 产品规格全文档：`docs/requirements.md`（编码前必读）
- 开发者指引：`CLAUDE.md`（每次改动需同步更新其中的 `Project Status` 与 `Unfinished` 段）
- 无用户系统、无登录、无数据库、无 git 仓库（目前未初始化 git）

---

## 2. 技术栈（已落地）

| 层 | 选型 |
|----|------|
| 后端 | FastAPI（async / uvicorn）+ librosa（核心 `pitch_shift`，`kaiser_best`）+ soundfile（WAV `PCM_16` 编码）+ numpy |
| 前端 | 原生 HTML/CSS/JS（无框架、无构建）；自实现 Canvas 波形 + Web Audio API transport；离线兜底为自写 FFT（radix-2 Cooley-Tukey）+ 相位声码器 |
| 测试 | pytest（`backend/tests/`）；前端用 Playwright（`.testenv/`，`~/.cache/ms-playwright` 已装 Chromium） |

> 注：需求里写前端用 Wavesurfer.js + Tailwind，实际为自实现 Canvas，未引入。

---

## 3. 目录结构

```
music-key-changer/
├── backend/
│   ├── main.py              # FastAPI 入口/路由/会话中间件/静态托管/后台清理线程
│   ├── audio/
│   │   ├── config.py        # 格式/大小/时长限制、路径、错误码、FRONTEND_DIR
│   │   └── processor.py     # 校验 + Librosa pitch_shift + WAV 编码（与 FastAPI 解耦）
│   ├── tests/               # test_processor.py（音频单测）+ test_api.py（端到端）
│   ├── conftest.py          # 让 `import audio` / `import main` 可用
│   ├── requirements.txt
│   └── run.sh               # 起服务（自动托管 frontend/）
├── frontend/
│   ├── index.html           # Apple 风格界面
│   ├── styles.css           # 设计系统 + 响应式
│   └── app.js               # 引擎自动选择 + DSP + 波形 + transport
├── docs/requirements.md     # 完整需求设计文档
├── CLAUDE.md                # 开发者指引（需与代码同步）
└── user_data/               # 会话隔离临时文件（<session_id>/，24h 清理）
```

---

## 4. 关键约束（硬编码，勿改忘同步）

- 支持格式：MP3、WAV、FLAC、AAC、OGG（外加 m4a/mp4）
- 单文件限制：**≤ 50 MB，≤ 600 s（10 分钟）** —— 最初需求为 5 分钟（300s），2026-09-03 已放宽到 10 分钟
- 升降调范围：semitones −12 ~ +12（默认 0；负值降调，正值升调）
- 输出格式：**当前恒为 16-bit PCM WAV**（需求要求"默认跟随输入格式"，未实现）
- 文件临时、会话隔离、24h 自动清理（`audio/config.py::Paths.TTL_SECONDS`）

---

## 5. 今日工作（2026-09-03）

### 5.1 完成
- ✅ **时长限制放宽**：300s → 600s（10 分钟）。改动点：
  - `backend/audio/config.py`：`MAX_DURATION = 600`
  - `frontend/app.js`：`MAX_DURATION = 600` + 超限提示文案改为"10 分钟"
  - 文档同步：`docs/requirements.md`、`frontend/index.html`、`README.md`、`CLAUDE.md` 一处不漏全部更新（含大小参考表"10 分钟大小"列数值翻倍）
- ✅ **清理前端诊断代码**：移除 `app.js` 中调试用的 `console.log`（playFrom/tick 内）与 `window.__mkcState` 钩子，代码恢复干净。
- ✅ **测试**：`pytest` 13 passed（音频单测 + API 端到端）。

### 5.2 进行中的问题（需跟进）
- ⚠️ **进度条/seek 与实际不符**：用户反馈"处理后歌曲进度条一下子就全部跑完"。
  - 现象：播放后 `state.offset` 迅速到达 `buffer.duration`、seek 卡在 1000，但音频实际播放时长正确。
  - 排查：`tick()` 中 `pos = offset + (audioCtx.currentTime - startTime)` 计算出的 pos 增长远快于真实播放位置（约 10 倍），疑似 `AudioContext.currentTime` 与 buffer 采样率/时长对不上。
  - 状态：**根因未定**。用页内 console.log 帧级记录时跟踪正常，用 evaluate 采样时复现异常——存在测量方式干扰的可能。需在不加诊断代码、用真实音频文件下稳定复现后定位。

---

## 6. 待开发项（按需求文档优先级，详见 `CLAUDE.md::Unfinished`）

**P1（重要）：**
1. 调性自动检测（US-07）— 真正识别原曲调性（需求建议 CREPE / Magenta MelodyRNN）；当前 `describeKey()` 仅按"假设输入=C 大调"估算。
2. 输出格式跟随输入 — 后端当前恒输出 WAV。

**P2（锦上添花）：**
3. 批量处理（`/api/v1/batch-process`）
4. 历史记录（持久化）
5. 音质增强 / 和声生成 / AI 推荐调性 / 社交分享 / API 开放

**非功能 / 合规：**
6. 限流（SlowAPI）+ 配额管理
7. WebSocket 实时进度
8. 免责声明 / 条款确认弹窗

**文档：**
9. `docs/api.md`（需求 §8.2 引用，尚未创建）

---

## 7. 常用命令

```bash
# 后端依赖（首次）
cd backend && python3 -m venv .venv && .venv/bin/pip install -r requirements.txt

# 启动（前端在 http://localhost:8000/）
cd backend && .venv/bin/python -m uvicorn main:app --reload   # 或 ./run.sh

# 测试
cd backend && .venv/bin/python -m pytest -q

# 前端离线预览（纯本地 DSP 引擎）
cd frontend && python3 -m http.server 8091   # http://localhost:8091/index.html

# Playwright（前端 E2E，独立 venv .testenv）
. .testenv/bin/activate && playwright install chromium
```

---

## 8. 环境备忘

- 后端 venv：`backend/.venv`（Python 3.13）
- Playwright venv：`.testenv`（`.testenv/bin/playwright`），浏览器缓存在 `~/.cache/ms-playwright`
- 后端默认在 8000 端口运行，`--reload` 开启；`app.js` 为静态托管，改动后浏览器刷新即生效，无需重启
