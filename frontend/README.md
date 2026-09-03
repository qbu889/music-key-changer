# 升降调 · Music Key Changer（前端）

Apple 风格的音乐升降调工具前端。处理引擎**自动选择**：由 FastAPI 后端处理时优先走服务端，离线 / `file://` 打开时自动回退到浏览器本地 DSP。

## 特性

- 🎨 Apple 设计语言：SF Pro 字体栈、`#f5f5f7` / 纯黑背景、`#0071e3` 强调色、药丸按钮、毛玻璃卡片、细腻动效
- 🌗 自动深色模式（`prefers-color-scheme`），全局毛玻璃导航栏
- 📤 拖拽 / 点击上传，格式与大小校验（MP3·WAV·FLAC·AAC·OGG，≤50MB）
- 🎚️ -12 ~ +12 半音滑块 + 常用预设，实时显示目标调性
- ☁️ **后端优先**：处理请求走 `/api/v1/process`，结果从 `/api/v1/download/{id}` 获取
- 🧠 **本地回退**：无后端时，浏览器内 FFT + 相位声码器（Phase Vocoder）独立完成
- 📊 Canvas 波形可视化 + 播放/暂停/拖动进度
- 📥 一键下载处理结果（16-bit PCM WAV）
- ♿ 键盘可用、尊重 `prefers-reduced-motion`、隐私优先（文件不出浏览器）

## 文件

| 文件 | 说明 |
|------|------|
| `index.html` | 页面结构 |
| `styles.css` | Apple 风格设计系统与响应式布局 |
| `app.js` | 引擎选择、音频解码、DSP、波形、播放控制、下载 |

## 运行

### 方式 A：对接后端（推荐）

启动后端，它会自动托管本目录：

```bash
cd backend
python -m uvicorn main:app --reload          # 或 ./run.sh
# 访问 http://localhost:8000/  → 自动加载 frontend/index.html
```

### 方式 B：纯前端离线运行

```bash
cd frontend
python3 -m http.server 8091
# 访问 http://localhost:8091/index.html   ← 自动使用本地 DSP 引擎
```

## 引擎选择逻辑

`app.js` 中的 `detectBackend()` 在首次处理时探测 `GET /api/health`：

- 成功（同源后端在运行）→ `processViaBackend()`：上传文件到 `/api/v1/process`，解码返回的 WAV 用于播放/下载；下载按钮直接指向服务端 URL。
- 失败（`file://` 或无后端）→ `processClientSide()`：沿用自实现的相位声码器。

这样同一套界面在服务端与离线场景下都能无缝工作。
