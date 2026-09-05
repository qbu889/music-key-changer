# 项目记忆 · Music Key Changer（音乐升降调）

> 本文件记录项目现状、技术要点与每日工作轨迹，便于后续快速接手。
> 最后更新：2026-09-05

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
| 后端 | FastAPI（async / uvicorn）+ librosa（核心 `pitch_shift`，`kaiser_best`）+ demucs+diffq（声部分离，模型 `mdx_q`）+ soundfile（WAV `PCM_16` 编码）+ numpy + torch |
| 前端 | 原生 HTML/CSS/JS（无框架、无构建）；自实现 Canvas 波形 + Web Audio API transport；离线兜底为自写 FFT（radix-2 Cooley-Tukey）+ 相位声码器 |
| 测试 | pytest（`backend/tests/`）；前端用 Playwright（`.testenv/`，`~/.cache/ms-playwright` 已装 Chromium） |

> 注：需求里写前端用 Wavesurfer.js + Tailwind，实际为自实现 Canvas，未引入。

---

## 3. 目录结构

```
music-key-changer/
├── backend/
│   ├── main.py              # FastAPI 入口/路由/会话中间件（安全：上传大小限制/安全头/session 隔离下载）/静态托管/后台清理线程
│   ├── audio/
│   │   ├── config.py        # 格式/大小/时长限制、路径、错误码、FRONTEND_DIR、ProcessingConfig
│   │   ├── processor.py     # 校验 + pitch_shift_separated(分离+Librosa)+ WAV 编码（与 FastAPI 解耦）
│   │   └── separators.py    # Demucs 声部分离（mdx_q）；懒加载+缓存；HF→hf-mirror 镜像；MPS/CPU 自动切换
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

## 5. 今日工作日志

### 5.1 今日工作（2026-09-03）
- ✅ **时长限制放宽**：300s → 600s（10 分钟）。改动点：
  - `backend/audio/config.py`：`MAX_DURATION = 600`
  - `frontend/app.js`：`MAX_DURATION = 600` + 超限提示文案改为"10 分钟"
  - 文档同步：`docs/requirements.md`、`frontend/index.html`、`README.md`、`CLAUDE.md` 一处不漏全部更新（含大小参考表"10 分钟大小"列数值翻倍）
- ✅ **清理前端诊断代码**：移除 `app.js` 中调试用的 `console.log`（playFrom/tick 内）与 `window.__mkcState` 钩子，代码恢复干净。
- ✅ **测试**：`pytest` 13 passed（音频单测 + API 端到端）。

### 5.2 今日工作（2026-09-04）
- ✅ **升降调改走"声部分离式"处理，显著改善人声质感**。
  - **背景/根因**：原实现把整首混音（人声+伴奏混在一起）直接做 `librosa.pitch_shift`（相位声码器+WSOLA）。算法本身没问题（`kaiser_best`、保留共振峰），但人声与伴奏频谱纠缠在一起拉伸时产生频谱弥散/幅度抖动，在人声谐波上最明显 → 人声质感变差。
  - **方案**（专业降调 App 的做法）：先分离 → 分别升降调 → 再混回。输出仍"人声+伴奏"，但人声清晰度回升。
  - **实现**：
    - 新文件 `backend/audio/separators.py`：`SourceSeparator` 包装 Demucs `mdx_q`（2 音轨→实际输出 4 音轨 `drums/bass/other/vocals`），`get_separator()` 懒加载 + `lru_cache`。
    - `processor.py::pitch_shift_separated`：分离出人声/伴奏 → 各做保留共振峰的 `pitch_shift` → 混回 + 采样率还原 → `_match_level` 电平均衡(峰值对齐原曲、封顶 0.98 防 PCM 削波) → `_match_length` 对齐长度。**任一异常自动回退到整体直接升降调**（`except Exception` → `pitch_shift`）。
    - `config.py::ProcessingConfig`：`USE_SEPARATION=True`（默认开）、`SEPARATION_MODEL="mdx_q"`，可开关/换模型。
    - 依赖：`requirements.txt` 新增 `demucs>=4.1.0`、`diffq>=0.2.4`、`torch>=2.1`（diffq 是 mdx_q 量化模型必需）。
  - **排过的坑**（环境/API）：
    1. Demucs 4.x 权重走 `torch.hub` 从 HuggingFace 拉 safetensors，**torch.hub 忽略 `HF_ENDPOINT` 镜像变量**；HF 被墙时权重下不下来。→ `separators.py` 里**提前把 `huggingface.co`/`hf.co` URL 改写为 `hf-mirror.com`**（`DEMUCS_HF_MIRROR=0` 可关）。
    2. `mdx_q` 是 DiffQ 量化模型，**必须装 `diffq`**，否则加载失败。
    3. `apply_model(model, x)` 返回 **4D `(batch=1, sources, channels, samples)`** → 需 `[0]` 去掉 batch 维再按音轨索引。
    4. Demucs 模型**输入必须是立体声(2 通道)**：`_to_tensor` 把 mono 上混为立体声喂模型，分离后再按输入声道数下混（`mono_in` 判断），保持输入输出声道一致。
    5. 分离路径输出声道 = 输入声道（librosa pitch_shift 保持），`_match_length` 处理两次采样率变换带来的 ± 长度偏差。
    6. **混回后峰值超 1.0 会削波**：真曲（橄榄树 273s）实测分离式 `peak=1.216`（直接式为 1.116，已削波）。→ 新增 `_match_level`：把输出峰值对齐到原曲峰值、封顶 0.98，既防 PCM 削波又保持感知音量（rms 与原曲一致）。实测修复后 `peak=0.980`、0 clip。
  - **验证**：`process()` 端到端（立体声文件输入 → librosa mono → 分离 → 升降调 → WAV）输出正确 mono WAV；`pytest` **16 passed**（新增 3 个测试：分离关闭=直接升降调、注入失败回退、模型端到端 1.5s 音频校验 shape/length/实际改变）。
- ⚠️ **已知遗留（未影响功能）**：`save_wav` 对**立体声**数组用 `sf.write` 写空 BytesIO 会报 "Format not recognised"（soundfile/libsndfile 对 librosa↔soundfile 声道约定+空 buffer 检格式的坑）。当前 `process()` 因 `librosa.load(mono=True)` 恒输出 mono，**不受影响**；若将来启用立体声输出需修复 `save_wav`。

### 5.3 已解决的问题（2026-09-03）
- ✅ **进度条/seek 与实际不符（已修复）**：用户反馈"处理后歌曲进度条一下子就全部跑完"。
  - 现象：播放后 `state.offset` 迅速到达 `buffer.duration`、seek 瞬间到 1000，但音频实际时长正确（后端 WAV 经 soundfile 确认为 48000 Hz / 20s，buffer 解码也正确）。
  - **真正根因（非 audioCtx.currentTime）**：`tick()` 每帧执行 `state.offset = state.offset + (时钟 - startTime)`，而 `startTime` 固定为播放起点，于是每帧都把"总流逝时间"重复加到已累积的 offset 上 → **二次增长（复利）**，按抛物线暴涨，瞬间跑满。
  - 修复（`frontend/app.js`）：
    - `tick()` 里 `state.offset` 作为播放(重)开始时的**固定起点**，只算 `pos` 用于显示，**不再写回** `state.offset`。
    - `pause()` 一次性把流逝时间累加到 `state.offset`（每帧只调一次，不受复利影响）。
    - 播放进度统一改用可靠的单调墙钟 `performance.now()`，避免 `audioCtx.currentTime` 在部分浏览器/headless 环境下推进不可靠。
  - 验证：后端路径与本地相位声码器路径均用 20s 音频测得 seek 按 1.0x 线性（1s=50、3s=150、5s=250）；pause 保持、resume 从断点继续、跳段、下载均正常；`pytest` 13 passed。
  - 提交：`73a6f1f`（已 push 到 origin/master）。

### 5.4 今日工作（2026-09-05）
- ✅ **后端安全加固（首次系统安全审查）**。改动集中在 `backend/main.py`。
  - **🔴 路径遍历 + IDOR（`/api/v1/download/{file_id}`）**：原 `file_id` 直接拼进文件系统路径，攻击者可用 `../../` 读服务器任意文件、或遍历其他会话文件。
    - 新增 `_resolve_session_file()`：`file_id` 必须匹配 `^[a-f0-9]{32}$`（即 `uuid4.hex`），且用 `target.relative_to(base)` 确认文件**物理位于本会话目录**内；否则返回 `None` → 404。一处同时消除路径遍历与跨会话访问（IDOR），对攻击者统一返回 404 不泄露是否检测到攻击。
  - **🟠 上传 DoS**：原 `await file.read()` 在**校验之前**把整包读入内存且无上限 → OOM。新增 `limit_request_size` 中间件，读取前按 `Content-Length` 拒绝（`MAX_UPLOAD_BYTES = 55MB` = 50MB 文件 + 5MB multipart 开销），超限返回 `413`。实测合法 50MB 文件仍 `200`。
  - **🟡 内存泄漏**：`_sessions` 字典只增不减；`_cleanup_expired()` 清理过期会话时同步 `_sessions.pop()`。
  - **🟢 Cookie secure**：按 `request.url.scheme` 动态置 `secure`（仅 HTTPS/WSS），本地 HTTP 不受影响。
  - **🟢 安全响应头**：新增 `set_security_headers` 中间件，加 `X-Content-Type-Options: nosniff`、`X-Frame-Options: DENY`、`Referrer-Policy: no-referrer`。
  - **验证**：新增 4 个安全测试（路径遍历、跨会话访问、超限上传、安全头）。`pytest` **23 passed**（API 端到端 10 + 音频单测 13）。功能不受影响：正常上传/处理/下载/播放全部验证通过。
  - 提交：`b87c631`（尚未 push，本地领先 origin/master 7 个提交）。
  - ⚠️ **已知遗留（可后续处理）**：`limit_request_size` 仅校验 `Content-Length`（分片/无 Content-Length 上传防护弱）；`process` 通用异常仍 `str(exc)` 回传，可能泄露内部细节。限流需求文档已有 SlowAPI 计划（见 §6 非功能项）。

### 5.5 今日工作（2026-09-05，安全加固续）
- ✅ **剩余安全项修复**（基于首次审查的"已知遗留"与后续审计）：
  - **🟠 上传 DoS 补漏**：原 `limit_request_size` 仅校验 `Content-Length`，分片/伪造/无 Content-Length 上传可绕过 → `await file.read()` 整包入内存 OOM。新增 `_bounded_read()` 从底层 spooled 文件**分块读取**（`asyncio.to_thread` 不阻塞事件循环），硬性封顶 `MAX_UPLOAD_BYTES`；`process_audio` 读取后复核 `len(data) > MAX_FILE_SIZE` → 413。两条防线互补。
  - **🟠 内部信息泄露**：`process` 通用 `except Exception` 原 `str(exc)` 回传（暴露路径/库内部）。改为服务端 `logger.error` 记录、返回泛化 `"处理失败，请稍后重试"`（`UNKNOWN_ERROR`）。
  - **🟡 Content-Length 解析健壮性**：`isdigit()` 对 unicode 数字（如 '²'）返回 True 但 `int()` 抛异常→500。加 `isascii()` 守卫。
  - **🟡 文件名净化（纵深防御）**：`process_audio` 仅用 `Path(filename).name`（去路径成分）、拒绝空文件名；文件名本就不落盘（输出用随机 `file_id`）。
- **验证**：新增 5 个测试（`_bounded_read` 封顶/读满、意外异常不泄露、空 filename、无 Content-Length 超限）。`pytest` **28 passed**（原 23 + 本轮 5）。
- 提交：待提交。

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
