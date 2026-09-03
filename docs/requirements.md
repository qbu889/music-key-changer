# 🎵 Music Key Changer - 需求设计文档 v1.0

> 音乐升降调处理平台需求规格说明书

---

## 📋 目录

1. [项目概述](#1-项目概述)
2. [用户故事](#2-用户故事)
3. [功能需求](#3-功能需求)
4. [非功能需求](#4-非功能需求)
5. [系统架构](#5-系统架构)
6. [技术选型](#6-技术选型)
7. [数据模型](#7-数据模型)
8. API 设计
9. [开发计划](#9-开发计划)
10. [风险评估](#10-风险评估)

---

## 1. 项目概述

### 1.1 项目名称

**Music Key Changer** - 音乐升降调处理平台

### 1.2 项目背景

音乐创作者、歌手、DJ 和音乐制作人经常需要调整音乐的调性（Key）来满足以下需求：

| 场景 | 描述 |
|------|------|
| 🎤 歌手演唱 | 调整歌曲调性以适应歌手音域 |
| 🎧 DJ 混音 | 统一多首歌曲的调性以便无缝混音 |
| 🎹 编曲改编 | 将乐曲改编到不同调性 |
| 🎬 影视配乐 | 调整音乐调性匹配画面情绪 |
| 📱 短视频创作 | 快速调整音乐调性用于视频制作 |

**现有痛点**：

| 痛点 | 描述 |
|------|------|
| 🔧 工具复杂 | 专业软件（如 Ableton、FL Studio）学习成本高 |
| 💰 付费门槛 | 在线工具大多需要付费订阅 |
| 🌐 语言障碍 | 国外工具界面不支持中文 |
| 📦 安装麻烦 | 需要下载安装大型软件 |

### 1.3 解决方案

提供一个**简单、免费、在线**的音乐升降调工具：

- ✅ **上传音频** - 支持多种常见音频格式
- 🎚️ **升降调控制** - 直观滑块控制，支持 -12 ~ +12 半音
- 🎧 **在线试听** - 处理完成后即时播放
- 📥 **一键下载** - 下载处理后的音频文件

### 1.4 项目目标

| 目标类型 | 描述 | 衡量标准 |
|---------|------|---------|
| 🎯 短期目标 | 实现核心升降调功能 | 支持 MP3/WAV/FLAC，处理准确率 > 95% |
| 🎯 中期目标 | 完善用户体验 | 页面加载 < 2s，处理延迟 < 10s |
| 🎯 长期目标 | 扩展高级功能 | 支持批量处理、API 开放 |

---

## 2. 用户故事

### 2.1 用户画像

| 用户类型 | 占比 | 需求特点 |
|---------|------|---------|
| 🎤 业余歌手 | 35% | 快速调整歌曲调性用于演唱 |
| 🎧 DJ/制作人 | 25% | 精确调性调整用于混音 |
| 📱 短视频创作者 | 20% | 快速调整音乐用于视频 |
| 🎓 音乐学生 | 15% | 学习调性概念，练习改编 |
| 🏢 其他用户 | 5% | 偶尔使用，追求简单 |

### 2.2 用户故事地图

```
用户旅程：上传 → 调整 → 试听 → 下载

P0（必须）          P1（重要）         P2（锦上添花）
─────────────────────────────────────────────────────
上传音频文件    →    实时预览效果    →    批量处理
选择升降调      →    调性自动检测    →    和声生成
处理音频        →    音质增强        →    AI 推荐调性
在线试听        →    预设调性模板    →    社交分享
下载结果        →    历史记录        →    API 开放
```

### 2.3 核心用户故事

| ID | 作为... | 我想要... | 以便于... | 优先级 |
|----|---------|-----------|-----------|--------|
| US-01 | 普通用户 | 上传 MP3/WAV 文件 | 开始处理音乐 | P0 |
| US-02 | 普通用户 | 通过滑块选择升降调半音数 | 精确控制调性 | P0 |
| US-03 | 普通用户 | 点击按钮处理音频 | 生成新调性的音频 | P0 |
| US-04 | 普通用户 | 在线播放处理后的音频 | 确认效果 | P0 |
| US-05 | 普通用户 | 下载处理后的音频文件 | 使用到其他地方 | P0 |
| US-06 | DJ | 支持 FLAC 无损格式 | 保持音质 | P1 |
| US-07 | 歌手 | 自动检测原曲调性 | 了解当前调性 | P1 |
| US-08 | 制作人 | 支持 -12 ~ +12 半音范围 | 完整调性覆盖 | P1 |
| US-09 | 创作者 | 批量处理多首歌曲 | 提高效率 | P2 |
| US-10 | 所有用户 | 中文界面 | 更容易理解 | P1 |

---

## 3. 功能需求

### 3.1 功能模块总览

```
Music Key Changer
├── 📤 上传模块
│   ├── 文件上传
│   ├── 格式验证
│   └── 大小限制
├── 🎛️ 处理模块
│   ├── 升降调控制
│   ├── 音频处理
│   └── 进度反馈
├── 🎧 播放模块
│   ├── 在线播放
│   ├── 播放控制
│   └── 波形可视化
├── 📥 下载模块
│   ├── 文件下载
│   ├── 格式选择
│   └── 批量下载
└── ⚙️ 系统模块
    ├── 用户管理（可选）
    ├── 历史记录
    └── 系统配置
```

### 3.2 详细功能需求

#### 3.2.1 上传模块

| 功能 | 描述 | 技术实现 |
|------|------|---------|
| **文件上传** | 支持拖拽上传和点击上传 | HTML5 File API |
| **格式支持** | MP3, WAV, FLAC, AAC, OGG | Librosa 自动识别 |
| **大小限制** | 单文件最大 50MB | 后端配置限制 |
| **时长限制** | 单文件最长 10 分钟 | 后端验证 |
| **格式验证** | 检查文件类型、大小、时长 | 前端 + 后端双重验证 |
| **上传进度** | 显示上传进度条 | Axios 进度事件 |

**文件大小参考**：

| 格式 | 采样率 | 位深 | 声道 | 每分钟大小 | 10 分钟大小 |
|------|--------|------|------|-----------|------------|
| MP3 | 44.1kHz | 128kbps | 立体声 | 1MB | 10MB |
| WAV | 44.1kHz | 16-bit | 立体声 | 10MB | 100MB |
| FLAC | 44.1kHz | 16-bit | 立体声 | 5MB | 50MB |
| AAC | 44.1kHz | 192kbps | 立体声 | 1.5MB | 15MB |

**输入**：
- 音频文件（MP3/WAV/FLAC/AAC/OGG）
- 文件大小 ≤ 50MB
- 音频时长 ≤ 10 分钟

**输出**：
- 上传成功：文件 ID、文件名、时长、采样率
- 上传失败：错误信息（格式不支持、文件过大、时长超限）

**文件验证实现**：

```python
class FileConfig:
    MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
    MAX_DURATION = 600  # 10 分钟（秒）
    SUPPORTED_FORMATS = ['.mp3', '.wav', '.flac', '.aac', '.ogg']

async def validate_file(file: UploadFile) -> dict:
    """验证上传文件"""
    # 1. 检查扩展名
    ext = Path(file.filename).suffix.lower()
    if ext not in FileConfig.SUPPORTED_FORMATS:
        raise ValueError(f"不支持的格式：{ext}")
    
    # 2. 检查文件大小
    file_size = len(await file.read())
    if file_size > FileConfig.MAX_FILE_SIZE:
        raise ValueError(f"文件大小超过限制：{file_size / 1024 / 1024:.1f}MB > 50MB")
    
    # 3. 检查音频时长
    audio, sr = librosa.load(io.BytesIO(file.content), sr=None)
    duration = len(audio) / sr
    if duration > FileConfig.MAX_DURATION:
        raise ValueError(f"音频时长超过限制：{duration:.1f}s > 600s")
    
    return {
        "file_size": file_size,
        "duration": duration,
        "sample_rate": sr,
        "channels": len(audio.shape) if len(audio.shape) > 1 else 1
    }
```

#### 3.2.2 处理模块

| 功能 | 描述 | 技术实现 |
|------|------|---------|
| **升降调控制** | 滑块选择 -12 ~ +12 半音 | 前端 UI 组件 |
| **实时预览** | 10 秒片段试听 | Web Audio API + Librosa |
| **音频处理** | 核心升降调算法 | Librosa `pitch_shift` + `kaiser_best` |
| **进度反馈** | 每步骤更新进度 | WebSocket/SSE |
| **错误处理** | 具体错误提示 | 异常捕获 + 错误码 |

**升降调参数**：

| 参数 | 范围 | 默认值 | 说明 |
|------|------|--------|------|
| semitones | -12 ~ +12 | 0 | 半音数，负值降调，正值升调 |
| quality | 低/中/高 | 中 | 处理质量（Phase 2+） |
| output_format | MP3/WAV/FLAC | 原格式 | 输出格式 |

**处理时间预期**：

| 音频时长 | 预期处理时间 | 硬件配置 |
|---------|-------------|---------|
| 1 分钟 | < 3 秒 | 4 核 2.5GHz, 8GB |
| 3 分钟 | < 15 秒 | 4 核 2.5GHz, 8GB |
| 10 分钟 | < 60 秒 | 4 核 2.5GHz, 8GB |

**同步/异步处理方案**：

| 阶段 | 处理方式 | 说明 |
|------|---------|------|
| **MVP** | 同步处理 | 简单直接，限制音频 ≤ 3 分钟 |
| **Phase 2** | 异步任务 | Celery + Redis，支持更长音频 |
| **Phase 3** | 流式处理 | 实时反馈，支持大文件 |

**MVP 同步处理实现**：

```python
from fastapi import FastAPI, UploadFile, File
import librosa
import numpy as np

app = FastAPI()

@app.post("/api/v1/process")
async def process_audio(file: UploadFile = File(...), semitones: int = 2):
    """同步处理音频"""
    try:
        # 1. 保存临时文件
        temp_path = await save_temp_file(file)
        
        # 2. 加载音频
        audio, sr = librosa.load(temp_path, sr=None)
        
        # 3. 升降调处理
        processed = librosa.effects.pitch_shift(
            audio, 
            sr=sr, 
            n_steps=semitones,
            res_type='kaiser_best'
        )
        
        # 4. 保存结果
        output_path = save_output(processed, sr)
        
        # 5. 清理临时文件
        cleanup(temp_path)
        
        return {
            "status": "success",
            "output_url": f"/api/v1/download/{output_path}"
        }
        
    except Exception as e:
        return {"status": "error", "message": str(e)}
```

#### 3.2.3 播放模块

| 功能 | 描述 | 技术实现 |
|------|------|---------|
| **在线播放** | 浏览器内播放音频 | HTML5 Audio |
| **播放控制** | 播放/暂停/进度条 | Web Audio API |
| **波形可视化** | 显示音频波形 | Wavesurfer.js |
| **片段播放** | 选中片段循环播放 | 自定义实现 |
| **实时预览** | 10 秒片段试听 | Web Audio API + Librosa |

**实时预览方案**：

```python
def preview_audio(audio: np.ndarray, sr: int, semitones: int, duration: float = 10.0):
    """
    生成 10 秒预览音频
    
    Args:
        audio: 完整音频数据
        sr: 采样率
        semitones: 升降调半音数
        duration: 预览时长（秒）
    
    Returns:
        预览音频数据
    """
    # 取中间 10 秒
    start_sample = int(len(audio) * 0.4)  # 从 40% 处开始
    end_sample = start_sample + int(sr * duration)
    
    preview = audio[start_sample:end_sample]
    processed = librosa.effects.pitch_shift(preview, sr, n_steps=semitones)
    
    return processed
```

**前端实现**：

```javascript
// static/js/main.js
async function previewAudio(file, semitones) {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('semitones', semitones);
    formData.append('preview', true);
    
    const response = await fetch('/api/v1/preview', {
        method: 'POST',
        body: formData
    });
    
    const blob = await response.blob();
    const audioUrl = URL.createObjectURL(blob);
    
    const audio = new Audio(audioUrl);
    audio.play();
    
    return audio;
}
```

**预览参数**：

| 参数 | 值 | 说明 |
|------|------|------|
| 预览时长 | 10 秒 | 固定时长 |
| 预览位置 | 音频 40% 处 | 避免开头静音 |
| 预览延迟 | < 2 秒 | 从请求到播放 |
| 更新频率 | 每 500ms | 滑块拖动时更新 |

#### 3.2.4 下载模块

| 功能 | 描述 | 技术实现 |
|------|------|---------|
| **单文件下载** | 下载处理后的音频 | FastAPI FileResponse |
| **格式选择** | 选择输出格式 | 后端转换 |
| **批量下载** | 下载多个处理结果（未来） | ZIP 打包 |
| **下载管理** | 查看下载历史 | 本地存储 |

### 3.3 高级功能（Phase 2+）

| 功能 | 描述 | 优先级 |
|------|------|--------|
| **调性自动检测** | 自动识别原曲调性（C 大调、A 小调等） | P1 |
| **预设调性模板** | 常用调性预设（如"升 2 半音"、"降 3 半音"） | P1 |
| **批量处理** | 一次上传多个文件批量处理 | P2 |
| **音质增强** | 升降调后自动修复音质损失 | P2 |
| **和声生成** | 升降调后自动添加和声 | P3 |
| **历史记录** | 保存用户处理历史 | P2 |
| **用户系统** | 注册登录，云端存储 | P3 |

#### 3.3.1 批量处理方案（Phase 2）

**批量处理实现**：

```python
@app.post("/api/v1/batch-process")
async def batch_process(files: list[UploadFile], semitones: int):
    """
    批量处理音频
    
    Args:
        files: 音频文件列表
        semitones: 升降调半音数（统一参数）
    
    Returns:
        处理结果列表
    """
    results = []
    
    for file in files:
        try:
            # 处理单个文件
            result = await process_single_file(file, semitones)
            results.append({
                "filename": file.filename,
                "status": "success",
                "output_url": result["output_url"]
            })
        except Exception as e:
            results.append({
                "filename": file.filename,
                "status": "failed",
                "error": str(e)
            })
    
    return {"results": results}
```

**批量处理限制**：

```python
class BatchConfig:
    MAX_FILES = 10  # 最多 10 个文件
    MAX_TOTAL_DURATION = 600  # 总时长不超过 10 分钟
```

**前端实现**：

```javascript
// static/js/main.js
async function batchProcess(files, semitones) {
    if (files.length > 10) {
        alert('最多支持 10 个文件');
        return;
    }
    
    const formData = new FormData();
    files.forEach(file => {
        formData.append('files', file);
    });
    formData.append('semitones', semitones);
    
    const response = await fetch('/api/v1/batch-process', {
        method: 'POST',
        body: formData
    });
    
    const results = await response.json();
    displayResults(results);
}
```

**失败处理策略**：跳过失败文件，继续处理其他文件

---

## 4. 非功能需求

### 4.1 性能需求

| 指标 | 要求 | 说明 |
|------|------|------|
| **页面加载时间** | < 2 秒 | 首屏加载 |
| **上传响应时间** | < 1 秒 | 文件验证响应 |
| **处理延迟** | < 15 秒（3 分钟音频） | 端到端处理时间（4 核 2.5GHz, 8GB） |
| **并发用户** | ≥ 10 | 同时使用人数（MVP 阶段） |
| **API 响应时间** | < 500ms | 非处理类接口 |

**性能测试基准**：

| 硬件配置 | CPU | 内存 | 预期处理时间（3 分钟音频） |
|---------|-----|------|--------------------------|
| 低端 | 2 核 2.0GHz | 4GB | 15-20 秒 |
| 中端 | 4 核 2.5GHz | 8GB | 8-12 秒 |
| 高端 | 8 核 3.0GHz | 16GB | 5-8 秒 |

**并发处理方案**：

```python
from slowapi import Limiter
from slowapi.util import get_remote_address
from concurrent.futures import ThreadPoolExecutor

app = FastAPI()
limiter = Limiter(key_func=get_remote_address)

# 并发限制配置
class ConcurrencyConfig:
    MAX_CONCURRENT_USERS = 10  # MVP 阶段
    MAX_FILES_PER_USER = 5  # 每用户最多 5 个并发任务
    MAX_PROCESSING_TIME = 60  # 最大处理时间（秒）

# 使用限流器
@app.post("/api/v1/process")
@limiter.limit("5/minute")  # 每分钟 5 次
@limiter.limit("20/hour")  # 每小时 20 次
async def process_audio_limited(request: Request, file: UploadFile = File(...)):
    """带限流的处理接口"""
    # 处理逻辑...

# 使用线程池（限制并发数）
executor = ThreadPoolExecutor(max_workers=4)

def process_with_pool(file_path: str, semitones: int):
    """使用线程池处理"""
    future = executor.submit(process_single, file_path, semitones)
    return future.result()
```

### 4.2 可靠性需求

| 指标 | 要求 |
|------|------|
| **系统可用性** | > 99% |
| **数据处理成功率** | > 95% |
| **错误恢复** | 自动重试机制 |
| **数据备份** | 临时文件 24 小时自动清理 |

### 4.3 兼容性需求

| 类别 | 要求 |
|------|------|
| **浏览器** | Chrome 90+, Firefox 88+, Safari 14+, Edge 90+ |
| **移动端** | iOS Safari, Android Chrome |
| **音频格式** | MP3, WAV, FLAC, AAC, OGG |
| **屏幕尺寸** | 响应式设计，支持 320px+ |

### 4.4 安全性需求

| 需求 | 描述 |
|------|------|
| **文件验证** | 检查文件类型、大小、恶意内容 |
| **上传限制** | 限制单用户上传频率（10 次/小时） |
| **数据隔离** | 用户文件隔离，防止越权访问 |
| **临时文件清理** | 处理后自动清理，保留不超过 24 小时 |
| **HTTPS** | 生产环境强制 HTTPS |
| **免责声明** | 明确用户使用责任 |
| **版权保护** | 不存储用户文件，自动清理 |
| **用户配额** | 限制单用户每日处理次数 |

#### 4.4.1 多用户支持方案

**用户会话管理**：

```python
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from typing import Optional
import uuid
import time

app = FastAPI()

# 用户会话存储（MVP 使用内存，生产环境使用 Redis）
class UserSessionStore:
    def __init__(self):
        self.sessions = {}
        self.user_quotas = {}  # 用户配额
    
    def create_session(self, ip_address: str, user_agent: str) -> str:
        """创建新用户会话"""
        session_id = str(uuid.uuid4())
        self.sessions[session_id] = {
            "session_id": session_id,
            "ip_address": ip_address,
            "user_agent": user_agent,
            "created_at": time.time(),
            "last_active": time.time(),
            "upload_count": 0,
            "process_count": 0,
            "is_active": True
        }
        return session_id
    
    def get_session(self, session_id: str) -> Optional[dict]:
        """获取用户会话"""
        session = self.sessions.get(session_id)
        if session and session.get("is_active"):
            session["last_active"] = time.time()
            return session
        return None
    
    def increment_upload_count(self, session_id: str) -> bool:
        """增加上传次数"""
        session = self.sessions.get(session_id)
        if not session:
            return False
        
        # 检查每日配额
        if session["upload_count"] >= 10:  # 每日 10 次
            return False
        
        session["upload_count"] += 1
        session["last_active"] = time.time()
        return True
    
    def increment_process_count(self, session_id: str) -> bool:
        """增加处理次数"""
        session = self.sessions.get(session_id)
        if not session:
            return False
        
        # 检查每日配额
        if session["process_count"] >= 5:  # 每日 5 次
            return False
        
        session["process_count"] += 1
        session["last_active"] = time.time()
        return True
    
    def cleanup_expired_sessions(self):
        """清理过期会话（24 小时）"""
        current_time = time.time()
        expired_sessions = []
        
        for session_id, session in self.sessions.items():
            if current_time - session["last_active"] > 86400:  # 24 小时
                expired_sessions.append(session_id)
        
        for session_id in expired_sessions:
            del self.sessions[session_id]

# 全局会话存储
session_store = UserSessionStore()

# 会话中间件
@app.middleware("http")
async def session_middleware(request: Request, call_next):
    """会话中间件"""
    # 获取 session_id（从 cookie 或 header）
    session_id = request.cookies.get("session_id") or request.headers.get("x-session-id")
    
    # 如果没有 session_id，创建新的
    if not session_id:
        session_id = session_store.create_session(
            request.client.host,
            request.headers.get("user-agent", "")
        )
    
    # 验证会话有效性
    session = session_store.get_session(session_id)
    if not session:
        return JSONResponse(
            status_code=401,
            content={"status": "error", "message": "会话已过期，请刷新页面"}
        )
    
    # 将 session 添加到 request.state
    request.state.session = session
    request.state.session_id = session_id
    
    # 设置响应 cookie
    response = await call_next(request)
    response.set_cookie(key="session_id", value=session_id)
    
    return response
```

**用户文件隔离**：

```python
import os
from pathlib import Path

# 用户文件目录结构
# uploads/
# ├── session_abc123/
# │   ├── original/     # 原始文件
# │   ├── processed/    # 处理结果
# │   └── temp/         # 临时文件
# ├── session_def456/
# │   ├── original/
# │   ├── processed/
# │   └── temp/

class UserManager:
    def __init__(self, base_dir: str = "user_data"):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(exist_ok=True)
    
    def get_user_dir(self, session_id: str) -> Path:
        """获取用户目录"""
        user_dir = self.base_dir / session_id
        user_dir.mkdir(exist_ok=True)
        
        # 创建子目录
        (user_dir / "original").mkdir(exist_ok=True)
        (user_dir / "processed").mkdir(exist_ok=True)
        (user_dir / "temp").mkdir(exist_ok=True)
        
        return user_dir
    
    def save_uploaded_file(self, session_id: str, file) -> Path:
        """保存用户上传的文件"""
        user_dir = self.get_user_dir(session_id)
        original_dir = user_dir / "original"
        
        # 生成唯一文件名
        import hashlib
        file_hash = hashlib.md5(file.filename.encode()).hexdigest()
        file_ext = Path(file.filename).suffix
        unique_filename = f"{file_hash}{file_ext}"
        
        file_path = original_dir / unique_filename
        file_path.write_bytes(file.read())
        
        return file_path
    
    def save_processed_file(self, session_id: str, audio_data, sr, filename: str) -> Path:
        """保存处理后的文件"""
        user_dir = self.get_user_dir(session_id)
        processed_dir = user_dir / "processed"
        
        file_path = processed_dir / filename
        # 保存音频数据...
        
        return file_path
    
    def cleanup_user_files(self, session_id: str):
        """清理用户文件"""
        user_dir = self.base_dir / session_id
        if user_dir.exists():
            import shutil
            shutil.rmtree(user_dir)

# 全局用户管理器
user_manager = UserManager()
```

**用户配额管理**：

```python
from datetime import datetime, timedelta

class QuotaManager:
    def __init__(self):
        self.quotas = {}  # session_id -> quota_info
    
    def check_upload_quota(self, session_id: str) -> dict:
        """检查上传配额"""
        quota = self.quotas.get(session_id, {
            "daily_count": 0,
            "daily_reset": datetime.now().date() + timedelta(days=1),
            "max_daily": 10
        })
        
        # 检查是否是新的一天
        if datetime.now().date() > quota["daily_reset"]:
            quota["daily_count"] = 0
            quota["daily_reset"] = datetime.now().date() + timedelta(days=1)
        
        if quota["daily_count"] >= quota["max_daily"]:
            return {
                "allowed": False,
                "message": f"今日上传次数已达上限（{quota['max_daily']}次）",
                "reset_time": quota["daily_reset"]
            }
        
        return {"allowed": True}
    
    def check_process_quota(self, session_id: str) -> dict:
        """检查处理配额"""
        quota = self.quotas.get(session_id, {
            "daily_count": 0,
            "daily_reset": datetime.now().date() + timedelta(days=1),
            "max_daily": 5
        })
        
        # 检查是否是新的一天
        if datetime.now().date() > quota["daily_reset"]:
            quota["daily_count"] = 0
            quota["daily_reset"] = datetime.now().date() + timedelta(days=1)
        
        if quota["daily_count"] >= quota["max_daily"]:
            return {
                "allowed": False,
                "message": f"今日处理次数已达上限（{quota['max_daily']}次）",
                "reset_time": quota["daily_reset"]
            }
        
        return {"allowed": True}
    
    def increment_quota(self, session_id: str, quota_type: str):
        """增加配额计数"""
        if session_id not in self.quotas:
            self.quotas[session_id] = {}
        
        quota = self.quotas[session_id]
        if quota_type == "upload":
            quota["daily_count"] = quota.get("upload_count", 0) + 1
        elif quota_type == "process":
            quota["daily_count"] = quota.get("process_count", 0) + 1

# 全局配额管理器
quota_manager = QuotaManager()
```

**并发处理限制**：

```python
from concurrent.futures import ThreadPoolExecutor
import threading

class ConcurrencyManager:
    def __init__(self, max_workers: int = 4):
        self.max_workers = max_workers
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.active_tasks = {}  # session_id -> task_count
        self.lock = threading.Lock()
    
    def can_accept_task(self, session_id: str) -> bool:
        """检查是否可以接受新任务"""
        with self.lock:
            # 检查全局并发数
            total_active = sum(self.active_tasks.values())
            if total_active >= self.max_workers:
                return False
            
            # 检查用户并发数
            user_active = self.active_tasks.get(session_id, 0)
            if user_active >= 2:  # 每用户最多 2 个并发任务
                return False
            
            return True
    
    def add_task(self, session_id: str):
        """添加任务"""
        with self.lock:
            self.active_tasks[session_id] = self.active_tasks.get(session_id, 0) + 1
    
    def remove_task(self, session_id: str):
        """移除任务"""
        with self.lock:
            if session_id in self.active_tasks:
                self.active_tasks[session_id] -= 1
                if self.active_tasks[session_id] <= 0:
                    del self.active_tasks[session_id]

# 全局并发管理器
concurrency_manager = ConcurrencyManager(max_workers=4)
```

**多用户 API 端点**：

```python
@app.get("/api/v1/session/info")
async def get_session_info(request: Request):
    """获取当前会话信息"""
    session = request.state.session
    
    # 检查配额
    upload_quota = quota_manager.check_upload_quota(request.state.session_id)
    process_quota = quota_manager.check_process_quota(request.state.session_id)
    
    return {
        "status": "success",
        "session_id": request.state.session_id,
        "upload_count": session["upload_count"],
        "process_count": session["process_count"],
        "upload_quota": upload_quota,
        "process_quota": process_quota
    }

@app.delete("/api/v1/session/cleanup")
async def cleanup_session(request: Request):
    """清理当前会话文件"""
    session_id = request.state.session_id
    
    # 清理用户文件
    user_manager.cleanup_user_files(session_id)
    
    # 失效会话
    session = session_store.get_session(session_id)
    if session:
        session["is_active"] = False
    
    return {"status": "success", "message": "会话文件已清理"}
```

**定时清理任务**：

```python
import schedule
import time

def cleanup_expired_sessions():
    """清理过期会话和文件"""
    # 清理过期会话
    session_store.cleanup_expired_sessions()
    
    # 清理过期用户文件（24 小时）
    from datetime import datetime, timedelta
    cutoff_time = datetime.now() - timedelta(hours=24)
    
    for user_dir in user_manager.base_dir.iterdir():
        if user_dir.is_dir():
            # 检查最后修改时间
            if datetime.fromtimestamp(user_dir.stat().st_mtime) < cutoff_time:
                import shutil
                shutil.rmtree(user_dir)
                print(f"已清理过期用户目录：{user_dir.name}")

# 每小时执行一次
schedule.every().hour.do(cleanup_expired_sessions)

# 每天凌晨 2 点执行深度清理
schedule.every().day.at("02:00").do(lambda: cleanup_expired_sessions())
```

**多用户性能考虑**：

| 用户数 | 并发任务 | 内存需求 | CPU 需求 | 建议配置 |
|--------|---------|---------|---------|---------|
| 1-10 | 4 | 4GB | 2 核 | 基础配置 |
| 10-50 | 8 | 8GB | 4 核 | 标准配置 |
| 50-100 | 16 | 16GB | 8 核 | 高级配置 |
| 100+ | 32 | 32GB | 16 核 | 企业配置 |

**多用户安全考虑**：

| 安全项 | 措施 |
|--------|------|
| 文件隔离 | 每个用户独立目录，防止越权访问 |
| 配额限制 | 限制每用户每日上传/处理次数 |
| 并发限制 | 限制每用户并发任务数 |
| 频率限制 | 限制每用户请求频率 |
| 数据清理 | 24 小时后自动清理用户文件 |
| 会话过期 | 24 小时无活动自动过期 |

#### 4.4.2 版权风险处理方案

**免责声明**：

```
⚠️ 免责声明

1. 请勿上传您没有版权的音乐
2. 本工具仅供个人学习、研究使用
3. 用户需自行承担上传内容的法律责任
4. 本平台不存储用户上传的音频文件
5. 处理完成后，所有文件将在 24 小时内自动删除
```

**用户确认流程**：

```python
@app.post("/api/v1/upload")
async def upload_audio(file: UploadFile = File(...), request: Request = ...):
    """上传音频"""
    # 检查用户是否同意条款
    if not request.headers.get("x-agreed-terms"):
        return {
            "status": "error",
            "message": "请先阅读并同意使用条款",
            "terms_url": "/terms"
        }
    
    # 继续处理...
```

**自动清理定时任务**：

```python
import schedule
import time
from datetime import datetime, timedelta

def cleanup_old_files():
    """每天凌晨 2 点清理旧文件"""
    import os
    
    cutoff_time = datetime.now() - timedelta(hours=24)
    
    for file in os.listdir(OUTPUT_DIR):
        file_path = os.path.join(OUTPUT_DIR, file)
        file_time = datetime.fromtimestamp(os.path.getmtime(file_path))
        
        if file_time < cutoff_time:
            os.remove(file_path)
            print(f"已删除：{file}")

# 每天执行
schedule.every().day.at("02:00").do(cleanup_old_files)
```

**上传频率限制**：

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.post("/api/v1/upload")
@limiter.limit("10/hour")  # 每小时最多 10 次上传
async def upload_audio_limited(file: UploadFile = File(...)):
    """带频率限制的上传"""
    # 处理逻辑...
```

### 4.5 可维护性需求

| 需求 | 描述 |
|------|------|
| **代码规范** | PEP 8 + ESLint |
| **日志记录** | 结构化日志，便于排查问题 |
| **错误监控** | Sentry 错误追踪 |
| **文档完整** | API 文档、用户指南、开发指南 |

---

## 5. 系统架构

### 5.1 整体架构

```
┌─────────────────────────────────────────────────────────────────┐
│                      客户端 (Browser)                            │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐     │
│  │  Upload UI  │  │ Control UI  │  │    Player UI        │     │
│  │  (拖拽上传)  │  │ (滑块控制)  │  │  (波形 + 播放控制)   │     │
│  └──────┬──────┘  └──────┬──────┘  └──────────┬──────────┘     │
│         │                │                     │                │
│         └────────────────┼─────────────────────┘                │
│                          │ HTTP/WebSocket                       │
└──────────────────────────┼───────────────────────────────────────┘
                           │
┌──────────────────────────┼───────────────────────────────────────┐
│                      服务端 (FastAPI)                              │
│                           │                                      │
│  ┌───────────────────────▼────────────────────────────────┐      │
│  │                    API Gateway                         │      │
│  │         (路由 + 会话管理 + 限流 + 配额)                 │      │
│  └───────────────────────┬────────────────────────────────┘      │
│                          │                                       │
│         ┌────────────────┼────────────────┐                      │
│         ▼                ▼                ▼                      │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │
│  │ Upload      │  │ Process     │  │ Stream/     │             │
│  │ Service     │  │ Service     │  │ Download    │             │
│  │             │  │             │  │ Service     │             │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘             │
│         │                │                │                      │
│         └────────────────┼────────────────┘                      │
│                          │                                       │
│              ┌───────────▼───────────┐                           │
│              │   Audio Processor     │                           │
│              │   (Librosa +          │                           │
│              │    Soundfile)         │                           │
│              └───────────────────────┘                           │
│                                                                  │
│  ┌──────────────────────────────────────────────────┐           │
│  │           多用户管理组件                          │           │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────┐  │           │
│  │  │ Session     │  │ Quota       │  │Concurrent│  │           │
│  │  │ Manager     │  │ Manager     │  │ Manager  │  │           │
│  │  └─────────────┘  └─────────────┘  └─────────┘  │           │
│  └──────────────────────────────────────────────────┘           │
└─────────────────────────────────────────────────────────────────┘
                           │
┌──────────────────────────┼───────────────────────────────────────┐
│                        存储层                                     │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐     │
│  │ User Data   │  │ User Data   │  │   Redis/SQLite      │     │
│  │ /session_1/ │  │ /session_2/ │  │   (会话/配额/进度)   │     │
│  │ ...         │  │ ...         │  │                     │     │
│  └─────────────┘  └─────────────┘  └─────────────────────┘     │
└─────────────────────────────────────────────────────────────────┘
```

### 5.2 数据流图

```
用户                    前端                      后端                  存储
 │                       │                         │                    │
 │  1. 选择文件           │                         │                    │
 │───┤                      │                         │                    │
 │                       │                         │                    │
 │                       │  2. 上传文件             │                    │
 │                       │───┤                         │                    │
 │                       │                         │───┤                │
 │                       │                         │  3. 保存临时文件    │
 │                       │                         │───┤                │
 │                       │                         │                    │
 │                       │  4. 返回文件 ID          │                    │
 │                       │<──┤                         │                    │
 │                       │                         │                    │
 │  5. 选择升降调         │                         │                    │
 │───┤                      │                         │                    │
 │                       │                         │                    │
 │                       │  6. 发起处理请求          │                    │
 │                       │───┤                         │                    │
 │                       │                         │───┤                │
 │                       │                         │  7. 加载音频        │
 │                       │                         │───┤                │
 │                       │                         │                    │
 │                       │                         │  8. 升降调处理      │
 │                       │                         │───────────────────▶│
 │                       │                         │                    │
 │                       │                         │  9. 保存结果        │
 │                       │                         │◀───────────────────│
 │                       │                         │                    │
 │                       │  10. 返回处理结果         │                    │
 │                       │<──┤                         │                    │
 │                       │                         │                    │
 │  11. 播放/下载         │                         │                    │
 │───┤                      │                         │                    │
 │                       │  12. 获取音频流            │                    │
 │                       │───┤                         │───┤            │
 │                       │                         │                    │
 │  13. 播放音频 ◄───────┤─────────────────────────────────────────────│
```

---

## 6. 技术选型

### 6.1 后端技术栈

| 类别 | 技术 | 版本 | 说明 |
|------|------|------|------|
| **Web 框架** | FastAPI | 0.104+ | 高性能异步框架，自动生成交互式 API 文档 |
| **音频处理** | Librosa | 0.10+ | 专业音频分析库，支持升降调 |
| **音频读写** | Soundfile | 0.12+ | 支持 WAV/FLAC 等格式 |
| **音频转换** | Pydub | 0.25+ | 格式转换、简单编辑 |
| **异步任务** | Celery + Redis | - | 可选，用于批量处理 |
| **数据库** | SQLite | - | 轻量级，可选 |
| **文件存储** | 本地文件系统 | - | 临时文件 + 输出文件 |
| **限流** | SlowAPI | - | 请求频率限制 |

#### 6.1.1 音质处理方案

**MVP 阶段**：使用 Librosa + 高质量重采样

```python
import librosa
import soundfile as sf

def pitch_shift_librosa(audio, sample_rate, semitones):
    """
    使用 Librosa 进行升降调
    
    Args:
        audio: 音频数据
        sample_rate: 采样率
        semitones: 升降调半音数 (-12 ~ +12)
    
    Returns:
        处理后的音频数据
    """
    # 使用 kaiser_best 重采样算法，音质最佳
    processed = librosa.effects.pitch_shift(
        audio, 
        sr=sample_rate, 
        n_steps=semitones,
        res_type='kaiser_best'  # 高质量重采样
    )
    return processed
```

**Phase 2 升级方案**：使用 Torchaudio（GPU 加速）

```python
import torchaudio
import torch

def pitch_shift_torchaudio(audio_path, output_path, sample_rate, semitones):
    """
    使用 Torchaudio 进行高质量升降调
    
    Args:
        audio_path: 输入音频路径
        output_path: 输出音频路径
        sample_rate: 采样率
        semitones: 升降调半音数
    """
    # 加载音频
    waveform, sr = torchaudio.load(audio_path)
    
    # 升降调（使用相位声码器算法）
    processor = torchaudio.transforms.PitchShift(
        sample_rate=sample_rate,
        n_steps=semitones
    )
    processed = processor(waveform)
    
    # 保存结果
    torchaudio.save(output_path, processed, sample_rate)
```

**方案对比**：

| 方案 | 音质 | 速度 | 复杂度 | 推荐阶段 |
|------|------|------|--------|---------|
| Librosa + `kaiser_best` | 中等 | 快 | 低 | MVP |
| Torchaudio + GPU | 高 | 快（GPU） | 中 | Phase 2+ |
| WSOLA 算法 | 高 | 中 | 中 | Phase 2+ |
| PSOLA 算法 | 高 | 中 | 高 | Phase 2+ |

### 6.2 前端技术栈

| 类别 | 技术 | 版本 | 说明 |
|------|------|------|------|
| **框架** | 原生 HTML/CSS/JS | - | MVP 阶段无需框架 |
| **UI 库** | Tailwind CSS | 3.x | 快速构建响应式界面 |
| **音频可视化** | Wavesurfer.js | 6.x | 波形显示、片段选择 |
| **HTTP 客户端** | Axios | 1.x | 文件上传、API 调用 |
| **状态管理** | Vanilla JS | - | 简单状态管理 |

### 6.3 AI 模型需求

#### ❌ MVP 阶段不需要 AI 模型

**升降调是传统信号处理问题**，使用算法即可解决，不需要深度学习模型。

#### ✅ 未来可扩展的 AI 功能

| 功能 | AI 模型 | 用途 | 优先级 |
|------|---------|------|--------|
| **调性检测** | CREPE / Magenta MelodyRNN | 自动识别原曲调性 | P1 |
| **音质增强** | Demucs / SpectralMask | 修复升降调音质损失 | P2 |
| **和声生成** | MusicVAE / MusicLM | 自动生成和声 | P3 |
| **智能推荐** | 推荐系统 | 根据原曲推荐合适调性 | P3 |

### 6.4 技术选型理由

#### 为什么选择 Librosa？

| 优势 | 说明 |
|------|------|
| 🎯 **专业音频库** | 专为音乐信息检索设计 |
| 🚀 **性能优秀** | 基于 NumPy/SciPy，效率高 |
| 📦 **简单易用** | `librosa.effects.pitch_shift()` 一行代码实现升降调 |
| 🌐 **社区活跃** | 文档完善，示例丰富 |
| 🆓 **开源免费** | MIT 许可证 |

#### 为什么选择 FastAPI？

| 优势 | 说明 |
|------|------|
| ⚡ **高性能** | 基于 Starlette，支持异步 |
| 📚 **自动文档** | 自动生成 Swagger UI |
| 🔧 **类型安全** | Pydantic 数据验证 |
| 🎯 **现代化** | Python 3.7+ 语法支持 |

---

## 7. 数据模型

### 7.1 核心数据模型

#### AudioFile（音频文件）

```python
class AudioFile(BaseModel):
    """音频文件模型"""
    file_id: str                    # 文件唯一标识
    original_filename: str          # 原始文件名
    file_size: int                  # 文件大小（字节）
    duration: float                 # 时长（秒）
    sample_rate: int                # 采样率
    channels: int                   # 声道数
    format: str                     # 格式 (mp3/wav/flac)
    upload_time: datetime           # 上传时间
    status: str                     # 状态 (uploaded/processing/completed/failed)
```

#### ProcessingJob（处理任务）

```python
class ProcessingJob(BaseModel):
    """处理任务模型"""
    job_id: str                     # 任务唯一标识
    file_id: str                    # 关联的文件 ID
    semitones: int                  # 升降调半音数
    input_format: str               # 输入格式
    output_format: str              # 输出格式
    status: str                     # 状态 (pending/processing/completed/failed)
    progress: float                 # 进度 (0-100)
    output_file_id: str = None      # 输出文件 ID
    error_message: str = None       # 错误信息
    created_at: datetime            # 创建时间
    completed_at: datetime = None   # 完成时间
```

#### UserSession（用户会话）

```python
class UserSession(BaseModel):
    """用户会话模型"""
    session_id: str                 # 会话 ID
    ip_address: str                 # IP 地址
    user_agent: str                 # 用户代理
    upload_count: int = 0           # 上传次数
    process_count: int = 0          # 处理次数
    created_at: datetime            # 创建时间
    last_active: datetime           # 最后活跃时间
    is_active: bool = True          # 会话是否有效
    daily_upload_limit: int = 10    # 每日上传限制
    daily_process_limit: int = 5    # 每日处理限制
```

#### UserFile（用户文件）

```python
class UserFile(BaseModel):
    """用户文件模型"""
    file_id: str                    # 文件唯一标识
    session_id: str                 # 所属会话 ID
    filename: str                   # 文件名
    file_path: str                  # 文件路径
    file_size: int                  # 文件大小（字节）
    file_type: str                  # 文件类型（original/processed/temp）
    upload_time: datetime           # 上传时间
    expires_at: datetime            # 过期时间（24 小时后）
    status: str                     # 状态（active/deleted）
```

### 7.2 数据库表设计（可选）

```sql
-- 音频文件表
CREATE TABLE audio_files (
    id TEXT PRIMARY KEY,
    original_filename TEXT NOT NULL,
    file_size INTEGER NOT NULL,
    duration REAL,
    sample_rate INTEGER,
    channels INTEGER,
    format TEXT,
    upload_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    status TEXT DEFAULT 'uploaded'
);

-- 处理任务表
CREATE TABLE processing_jobs (
    id TEXT PRIMARY KEY,
    file_id TEXT NOT NULL,
    semitones INTEGER NOT NULL,
    input_format TEXT,
    output_format TEXT,
    status TEXT DEFAULT 'pending',
    progress REAL DEFAULT 0,
    output_file_id TEXT,
    error_message TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    completed_at DATETIME,
    FOREIGN KEY (file_id) REFERENCES audio_files(id)
);
```

---

## 8. API 设计

### 8.1 API 概览

| 方法 | 端点 | 描述 | 认证 |
|------|------|------|------|
| GET | `/api/v1/session/info` | 获取会话信息 | 是 |
| DELETE | `/api/v1/session/cleanup` | 清理会话文件 | 是 |
| POST | `/api/v1/upload` | 上传音频文件 | 是 |
| POST | `/api/v1/process` | 发起处理任务 | 是 |
| GET | `/api/v1/jobs/{job_id}` | 查询任务状态 | 是 |
| GET | `/api/v1/output/{file_id}` | 获取处理结果 | 是 |
| GET | `/api/v1/stream/{file_id}` | 流式播放音频 | 是 |
| GET | `/api/v1/download/{file_id}` | 下载音频文件 | 是 |
| DELETE | `/api/v1/files/{file_id}` | 删除文件 | 是 |

### 8.2 详细 API 文档

详见 `docs/api.md`

#### 8.2.1 会话管理 API

**GET /api/v1/session/info**

获取当前会话信息

```python
@app.get("/api/v1/session/info")
async def get_session_info(request: Request):
    """获取当前会话信息"""
    session = request.state.session
    
    # 检查配额
    upload_quota = quota_manager.check_upload_quota(request.state.session_id)
    process_quota = quota_manager.check_process_quota(request.state.session_id)
    
    return {
        "status": "success",
        "session_id": request.state.session_id,
        "upload_count": session["upload_count"],
        "process_count": session["process_count"],
        "upload_quota": upload_quota,
        "process_quota": process_quota
    }
```

**响应示例**：

```json
{
    "status": "success",
    "session_id": "abc123-def456",
    "upload_count": 3,
    "process_count": 2,
    "upload_quota": {
        "allowed": true,
        "remaining": 7,
        "max_daily": 10
    },
    "process_quota": {
        "allowed": true,
        "remaining": 3,
        "max_daily": 5
    }
}
```

**DELETE /api/v1/session/cleanup**

清理当前会话文件

```python
@app.delete("/api/v1/session/cleanup")
async def cleanup_session(request: Request):
    """清理当前会话文件"""
    session_id = request.state.session_id
    
    # 清理用户文件
    user_manager.cleanup_user_files(session_id)
    
    # 失效会话
    session = session_store.get_session(session_id)
    if session:
        session["is_active"] = False
    
    return {"status": "success", "message": "会话文件已清理"}
```

### 8.3 WebSocket 事件（可选）

| 事件 | 方向 | 描述 |
|------|------|------|
| `progress` | 服务端 → 客户端 | 处理进度更新 |
| `completed` | 服务端 → 客户端 | 处理完成通知 |
| `error` | 服务端 → 客户端 | 错误通知 |

#### 8.3.1 进度更新方案

**进度更新实现**：

```python
from fastapi import WebSocket

async def process_with_progress(websocket: WebSocket, file_path: str, semitones: int):
    """带进度更新的处理"""
    
    # 步骤 1：加载音频
    await websocket.send_json({"type": "progress", "value": 10, "message": "正在加载音频..."})
    audio, sr = librosa.load(file_path, sr=None)
    
    # 步骤 2：预处理
    await websocket.send_json({"type": "progress", "value": 30, "message": "正在预处理..."})
    # 预处理逻辑...
    
    # 步骤 3：升降调
    await websocket.send_json({"type": "progress", "value": 50, "message": "正在升降调..."})
    processed = librosa.effects.pitch_shift(audio, sr, n_steps=semitones)
    
    # 步骤 4：后处理
    await websocket.send_json({"type": "progress", "value": 80, "message": "正在后处理..."})
    # 后处理逻辑...
    
    # 步骤 5：保存结果
    await websocket.send_json({"type": "progress", "value": 100, "message": "处理完成！"})
    save_audio(processed, sr, output_path)
```

**进度更新频率**：每步骤更新一次（加载、处理、保存）

**错误处理方案**：

```python
from fastapi import HTTPException

@app.post("/api/v1/process")
async def process_audio_safe(file: UploadFile = File(...), semitones: int = 2):
    """带错误处理的音频处理"""
    try:
        # 1. 验证文件
        if not file.filename:
            raise HTTPException(status_code=400, detail="请选择文件")
        
        # 2. 保存临时文件
        temp_path = await save_temp_file(file)
        
        try:
            # 3. 处理音频
            audio, sr = librosa.load(temp_path, sr=None)
            processed = librosa.effects.pitch_shift(audio, sr, n_steps=semitones)
            
            # 4. 保存结果
            output_path = save_output(processed, sr)
            
            return {
                "status": "success",
                "output_url": f"/api/v1/download/{output_path}"
            }
            
        finally:
            # 5. 清理临时文件（无论成功失败）
            if os.path.exists(temp_path):
                os.remove(temp_path)
                
    except HTTPException:
        raise
    except Exception as e:
        # 记录错误日志
        logger.error(f"处理失败：{str(e)}")
        
        return {
            "status": "error",
            "message": "处理失败，请重试",
            "error_code": get_error_code(e)
        }
```

**错误码映射**：

| 错误码 | 错误信息 | 解决建议 |
|--------|---------|---------|
| `FILE_FORMAT_INVALID` | 不支持的音频格式 | 请上传 MP3/WAV/FLAC 格式 |
| `FILE_SIZE_EXCEEDED` | 文件大小超过限制 | 请上传小于 50MB 的文件 |
| `DURATION_EXCEEDED` | 音频时长超过限制 | 请上传小于 10 分钟的音频 |
| `PROCESSING_FAILED` | 处理失败 | 请重试，如持续失败请联系客服 |
| `UNKNOWN_ERROR` | 未知错误 | 请联系客服 |

**错误反馈渠道**：

```python
@app.post("/api/v1/feedback")
async def submit_feedback(error_code: str, description: str):
    """提交错误反馈"""
    # 发送到邮件或日志系统
    send_email("admin@example.com", f"错误报告：{error_code}", description)
    
    return {"status": "success", "message": "感谢您的反馈"}
```

---

## 9. 开发计划

### 9.1 Phase 1 - MVP（2 周）

**目标**：实现核心升降调功能

| 任务 | 工时 | 负责人 | 状态 |
|------|------|--------|------|
| 项目结构搭建 | 4h | - | ⬜ |
| 音频上传功能 | 8h | - | ⬜ |
| 升降调核心算法 | 12h | - | ⬜ |
| 文件下载功能 | 4h | - | ⬜ |
| 基础 Web 界面 | 12h | - | ⬜ |
| 测试与优化 | 8h | - | ⬜ |
| **合计** | **48h** | | |

**MVP 功能清单**：
- [x] 上传 MP3/WAV 文件
- [x] 滑块选择 -12 ~ +12 半音
- [x] 升降调处理
- [x] 在线播放
- [x] 下载结果

### 9.2 Phase 2 - 完善（3 周）

**目标**：提升用户体验和功能完整性

| 任务 | 工时 | 优先级 | 状态 |
|------|------|--------|------|
| 波形可视化 | 12h | P1 | ⬜ |
| 调性自动检测 | 16h | P1 | ⬜ |
| 预设调性模板 | 8h | P1 | ⬜ |
| 批量处理 | 16h | P2 | ⬜ |
| 音质增强 | 12h | P2 | ⬜ |
| 移动端适配 | 12h | P1 | ⬜ |
| **合计** | **76h** | | |

### 9.3 Phase 3 - 优化（2 周）

**目标**：性能优化和高级功能

| 任务 | 工时 | 优先级 | 状态 |
|------|------|--------|------|
| 异步任务队列 | 16h | P1 | ⬜ |
| 缓存优化 | 8h | P2 | ⬜ |
| 用户系统 | 24h | P3 | ⬜ |
| 错误监控 | 8h | P1 | ⬜ |
| 文档完善 | 8h | P2 | ⬜ |
| **合计** | **64h** | | |

### 9.4 里程碑

| 里程碑 | 时间 | 交付物 |
|--------|------|--------|
| M1 - MVP 完成 | 第 2 周 | 核心功能可用 |
| M2 - 功能完善 | 第 5 周 | 完整产品 |
| M3 - 优化发布 | 第 7 周 | 生产版本 |

---

## 10. 风险评估

### 10.1 技术风险

| 风险 | 影响 | 概率 | 缓解方案 |
|------|------|------|---------|
| 升降调音质不佳 | 高 | 中 | 使用高质量算法，提供质量选项 |
| 大文件处理慢 | 中 | 中 | 异步处理，进度提示 |
| 格式兼容问题 | 中 | 低 | Librosa 广泛支持主流格式 |
| 内存溢出 | 高 | 低 | 限制文件大小，流式处理 |
| 多用户并发冲突 | 高 | 中 | 会话隔离，并发控制 |
| 用户文件泄露 | 高 | 低 | 严格目录隔离，权限控制 |
| 配额绕过 | 中 | 中 | 服务端验证，Redis 存储 |

### 10.2 业务风险

| 风险 | 影响 | 概率 | 缓解方案 |
|------|------|------|---------|
| 用户需求不足 | 高 | 低 | 市场调研，MVP 验证 |
| 竞品压力 | 中 | 中 | 差异化定位（免费、中文） |
| 法律风险 | 低 | 低 | 免责声明，不存储用户文件 |
| 恶意滥用 | 中 | 中 | 频率限制，配额管理 |
| 服务器过载 | 高 | 中 | 并发控制，自动扩缩容 |

### 10.3 运维风险

| 风险 | 影响 | 概率 | 缓解方案 |
|------|------|------|---------|
| 服务器负载高 | 高 | 中 | 限流，自动扩缩容 |
| 磁盘空间不足 | 中 | 低 | 定期清理临时文件 |
| 数据丢失 | 高 | 低 | 自动备份，临时文件清理 |
| 多用户资源竞争 | 高 | 中 | 并发控制，任务队列 |
| 会话数据丢失 | 中 | 低 | Redis 持久化，定期备份 |

---

## 附录

### A. 术语表

| 术语 | 英文 | 说明 |
|------|------|------|
| 半音 | Semitone | 音乐中最小的音程单位 |
| 升调 | Pitch Up | 提高音高 |
| 降调 | Pitch Down | 降低音高 |
| 调性 | Key | 音乐的主音和调式（如 C 大调） |
| 采样率 | Sample Rate | 每秒采样次数（Hz） |
| 声道 | Channel | 音频通道数（单声道/立体声） |

### B. 参考资源

- [Librosa 官方文档](https://librosa.org/doc/main/)
- [FastAPI 官方文档](https://fastapi.tiangolo.com/)
- [音乐调性参考表](https://en.wikipedia.org/wiki/Key_(music))
- [PSOLA 算法详解](https://www.mega-nerd.com/SRC/)

### C. 盈利模式（Phase 2+）

**分级收费方案**：

```python
class PricingConfig:
    FREE_TIER = {
        "max_files_per_day": 5,
        "max_duration": 600,  # 10 分钟
        "supported_formats": ["mp3", "wav"],
        "quality": "standard"
    }
    
    PRO_TIER = {
        "max_files_per_day": 100,
        "max_duration": 600,  # 10 分钟
        "supported_formats": ["mp3", "wav", "flac", "aac"],
        "quality": "high",
        "batch_processing": True,
        "api_access": True
    }
```

**免费额度限制**：

```python
@app.post("/api/v1/process")
async def process_audio_tiered(user_id: str = None, file: UploadFile = File(...)):
    """分级处理"""
    # 检查用户等级
    tier = get_user_tier(user_id)  # free 或 pro
    
    if tier == "free":
        # 检查每日限额
        if get_daily_count(user_id) >= 5:
            return {
                "status": "error",
                "message": "今日免费次数已用完",
                "upgrade_url": "/upgrade"
            }
    
    # 处理逻辑...
```

**盈利模式建议**：
- **MVP 阶段**：完全免费，无限制
- **Phase 2**：提供基础免费版 + 高级付费版
- **Phase 3**：考虑 API 开放、企业版

### E. 多用户部署建议

**MVP 阶段（1-10 用户）**：

| 配置 | 说明 |
|------|------|
| CPU | 2-4 核 |
| 内存 | 4-8 GB |
| 存储 | 20 GB |
| 会话存储 | 内存（字典） |
| 并发任务 | 4 |

**标准阶段（10-50 用户）**：

| 配置 | 说明 |
|------|------|
| CPU | 4-8 核 |
| 内存 | 8-16 GB |
| 存储 | 50 GB |
| 会话存储 | Redis |
| 并发任务 | 8 |

**生产阶段（50-100 用户）**：

| 配置 | 说明 |
|------|------|
| CPU | 8-16 核 |
| 内存 | 16-32 GB |
| 存储 | 100 GB+ |
| 会话存储 | Redis Cluster |
| 并发任务 | 16-32 |

### F. 文档版本

| 版本 | 日期 | 修改内容 | 作者 |
|------|------|---------|------|
| v1.0 | 2026-09-02 | 初始版本 | - |
| v1.1 | 2026-09-02 | 更新技术选型、添加详细方案 | - |
| v1.2 | 2026-09-02 | 添加多用户支持方案 | - |

---

*文档最后更新：2026-09-02*