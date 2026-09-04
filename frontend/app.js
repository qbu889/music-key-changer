/* ============================================================
   Music Key Changer — client-side app
   Audio decoding, phase-vocoder pitch shift, waveform, transport
   ============================================================ */
(() => {
  'use strict';

  /* ---------- DOM ---------- */
  const $ = (id) => document.getElementById(id);
  const el = {
    nav: $('globalNav'),
    dropzone: $('dropzone'),
    fileInput: $('fileInput'),
    fileInfo: $('fileInfo'),
    fileName: $('fileName'),
    fileDetail: $('fileDetail'),
    fileRemove: $('fileRemove'),
    semRange: $('semRange'),
    pitchValue: $('pitchValue'),
    pitchDir: $('pitchDir'),
    pitchKey: $('pitchKey'),
    presetChips: $('presetChips'),
    processBtn: $('processBtn'),
    progressWrap: $('progressWrap'),
    progressBar: $('progressBar'),
    progressText: $('progressText'),
    waveCanvas: $('waveCanvas'),
    wavePlaceholder: $('wavePlaceholder'),
    transport: $('transport'),
    playBtn: $('playBtn'),
    seek: $('seek'),
    curTime: $('curTime'),
    durTime: $('durTime'),
    downloadBtn: $('downloadBtn'),
  };

  /* ---------- State ---------- */
  const state = {
    audioCtx: null,
    originalBuffer: null,   // decoded source
    originalFile: null,     // raw File for backend processing
    processedBuffer: null,  // after pitch shift
    fileName: '',
    semitones: 0,
    processing: false,
    playing: false,
    sourceNode: null,
    startTime: 0,           // audioCtx.currentTime when play began
    offset: 0,              // playback offset
    seekOffset: null,       // when user seeks
    rafId: null,
    downloadUrl: null,
    backendAvailable: null, // cached /api/health result
  };

  const NOTE_NAMES = ['C','C♯','D','D♯','E','F','F♯','G','G♯','A','A♯','B'];
  const MIN_FILE = 0, MAX_FILE = 50 * 1024 * 1024;
  const MAX_DURATION = 600;

  /* ---------- Utils ---------- */
  function fmtTime(s) {
    if (!isFinite(s) || s < 0) s = 0;
    const m = Math.floor(s / 60);
    const sec = Math.floor(s % 60);
    return `${m}:${sec.toString().padStart(2, '0')}`;
  }
  function fmtSize(b) {
    if (b < 1024) return b + ' B';
    if (b < 1024 * 1024) return (b / 1024).toFixed(1) + ' KB';
    return (b / 1024 / 1024).toFixed(1) + ' MB';
  }
  function toast(msg, isError = false) {
    let t = document.querySelector('.toast');
    if (!t) {
      t = document.createElement('div');
      t.className = 'toast';
      document.body.appendChild(t);
    }
    t.textContent = msg;
    t.classList.toggle('is-error', isError);
    requestAnimationFrame(() => t.classList.add('show'));
    clearTimeout(t._timer);
    t._timer = setTimeout(() => t.classList.remove('show'), 2600);
  }

  /* ---------- Audio context (lazy, user gesture) ---------- */
  function ensureCtx() {
    if (!state.audioCtx) {
      state.audioCtx = new (window.AudioContext || window.webkitAudioContext)();
    }
    if (state.audioCtx.state === 'suspended') state.audioCtx.resume();
    return state.audioCtx;
  }

  /* ---------- Waveform rendering ---------- */
  function drawWaveform(buffer) {
    const canvas = el.waveCanvas;
    const dpr = window.devicePixelRatio || 1;
    const rect = canvas.getBoundingClientRect();
    canvas.width = rect.width * dpr;
    canvas.height = rect.height * dpr;
    const ctx = canvas.getContext('2d');
    ctx.scale(dpr, dpr);
    const W = rect.width, H = rect.height;
    ctx.clearRect(0, 0, W, H);

    const data = buffer.getChannelData(0);
    const step = Math.max(1, Math.floor(data.length / W));
    const mid = H / 2;

    const grad = ctx.createLinearGradient(0, 0, W, 0);
    grad.addColorStop(0, '#2997ff');
    grad.addColorStop(1, '#b16ce8');
    ctx.strokeStyle = grad;
    ctx.lineWidth = 1.4;
    ctx.globalAlpha = 0.9;
    ctx.beginPath();
    for (let x = 0; x < W; x++) {
      let min = 1, max = -1;
      const start = x * step;
      for (let j = 0; j < step; j++) {
        const v = data[start + j] || 0;
        if (v < min) min = v;
        if (v > max) max = v;
      }
      ctx.moveTo(x, mid + min * mid * 0.9);
      ctx.lineTo(x, mid + max * mid * 0.9);
    }
    ctx.stroke();
  }

  /* ---------- Play / pause ---------- */
  function stopSource() {
    if (state.sourceNode) {
      try { state.sourceNode.disconnect(); } catch (_) {}
      state.sourceNode = null;
    }
    cancelAnimationFrame(state.rafId);
    state.rafId = null;
  }

  function playFrom(offset = state.seekOffset != null ? state.seekOffset : state.offset) {
    const buffer = state.processedBuffer || state.originalBuffer;
    if (!buffer) return;
    ensureCtx();
    stopSource();

    state.sourceNode = state.audioCtx.createBufferSource();
    state.sourceNode.buffer = buffer;
    state.sourceNode.connect(state.audioCtx.destination);
    state.offset = offset;
    // 用可靠的单调墙钟 performance.now() 记录播放起点，避免 audioCtx.currentTime
    // 在某些浏览器/headless 环境下推进速率不可靠导致进度条漂移。
    state.startTime = performance.now();
    state.sourceNode.start(0, offset);
    state.sourceNode.onended = () => {
      // natural end
      if (state.playing && Math.abs((performance.now() - state.startTime) / 1000 - buffer.duration) < 0.3) {
        state.playing = false;
        state.offset = 0;
        state.seekOffset = null;
        el.playBtn.classList.remove('playing');
        el.seek.value = 0;
        el.curTime.textContent = '0:00';
      }
    };
    state.playing = true;
    el.playBtn.classList.add('playing');
    tick();
  }

  function pause() {
    if (!state.playing) return;
    state.offset += (performance.now() - state.startTime) / 1000;
    stopSource();
    state.playing = false;
    el.playBtn.classList.remove('playing');
  }

  function togglePlay() {
    if (!state.processedBuffer && !state.originalBuffer) return;
    if (state.playing) pause();
    else playFrom();
  }

  function tick() {
    if (!state.playing) return;
    const buffer = state.processedBuffer || state.originalBuffer;
    // state.offset 是播放(重)开始时的固定起点；这里只按墙钟流逝计算当前 pos 用于显示。
    // 绝不能把 pos 写回 state.offset——否则每帧都会把"总流逝时间"重复加到已累积的 offset 上，
    // 导致进度二次增长(复利)而瞬间跑满。pause() 会一次性把流逝时间累加到 offset。
    const pos = state.offset + (performance.now() - state.startTime) / 1000;
    if (pos >= buffer.duration) {
      el.seek.value = 1000;
      el.curTime.textContent = fmtTime(buffer.duration);
      return;
    }
    el.seek.value = (pos / buffer.duration) * 1000;
    el.curTime.textContent = fmtTime(pos);
    state.rafId = requestAnimationFrame(tick);
  }

  /* ---------- Pitch shift (phase vocoder) ---------- */
  function hann(n) {
    const w = new Float32Array(n);
    for (let i = 0; i < n; i++) w[i] = 0.5 * (1 - Math.cos((2 * Math.PI * i) / (n - 1)));
    return w;
  }

  function pitchShift(input, sr, semitones, frameSize = 2048) {
    const ratio = Math.pow(2, semitones / 12);
    const hopIn = Math.round(frameSize / 4);
    const hopOut = hopIn / ratio;
    const win = hann(frameSize);
    const winSum = new Float32Array(frameSize);
    for (let i = 0; i < frameSize; i++) winSum[i] = win[i] * win[i];

    // FFT via FFTPack-free DFT is too slow; use a simple radix-2 FFT (iterative)
    const N = frameSize;
    const log2N = Math.log2(N) | 0;
    const re = new Float32Array(N);
    const im = new Float32Array(N);
    const reOut = new Float32Array(N);
    const imOut = new Float32Array(N);

    // output buffer with overlap-add
    const outLen = Math.floor(input.length / ratio) + frameSize;
    const out = new Float32Array(outLen);
    const outWinSum = new Float32Array(outLen);

    // Expected phase advance per bin: 2π·k·hopIn/N
    const phShift = (2 * Math.PI * hopIn) / frameSize;
    let phPrev = new Float32Array(N / 2 + 1);
    let phAcc = new Float32Array(N / 2 + 1);

    const nFrames = Math.floor((input.length - frameSize) / hopIn) + 1;

    for (let frame = 0; frame < nFrames; frame++) {
      const start = frame * hopIn;
      // analyze window
      for (let i = 0; i < N; i++) {
        re[i] = (start + i < input.length) ? input[start + i] * win[i] : 0;
        im[i] = 0;
      }
      fft(re, im, log2N, false);

      // phase difference (de-wrap) + accumulate for synthesis
      for (let k = 0; k <= N / 2; k++) {
        const mag = Math.hypot(re[k], im[k]);
        const curPhase = Math.atan2(im[k], re[k]);
        let diff = curPhase - phPrev[k] - phShift * k;
        // unwrap residual phase to [-π, π]
        diff = Math.atan2(Math.sin(diff), Math.cos(diff));
        phAcc[k] += phShift * k + diff;
        phPrev[k] = curPhase;
        reOut[k] = mag * Math.cos(phAcc[k]);
        imOut[k] = mag * Math.sin(phAcc[k]);
      }

      // inverse FFT
      fft(reOut, imOut, log2N, true);

      // overlap-add with synthesis hop
      const outPos = Math.round(frame * hopOut);
      for (let i = 0; i < N; i++) {
        const idx = outPos + i;
        if (idx < outLen) {
          out[idx] += reOut[i] * win[i];
          outWinSum[idx] += winSum[i];
        }
      }
    }

    // normalize by window sum
    for (let i = 0; i < outLen; i++) {
      const w = outWinSum[i];
      out[i] = w > 1e-4 ? out[i] / w : 0;
    }

    // trim to near original length (scaled)
    const targetLen = Math.floor(input.length / ratio);
    const result = out.slice(0, targetLen);
    // soft fade in/out to avoid clicks
    const fade = Math.min(512, result.length / 200);
    for (let i = 0; i < fade; i++) {
      result[i] *= i / fade;
      result[result.length - 1 - i] *= i / fade;
    }
    return result;
  }

  /* Iterative radix-2 Cooley-Tukey FFT (in-place). log2N assumed valid. */
  function fft(re, im, log2N, invert) {
    const n = re.length;
    // bit reversal
    for (let i = 1, j = 0; i < n; i++) {
      let bit = n >> 1;
      for (; j & bit; bit >>= 1) j ^= bit;
      j ^= bit;
      if (i < j) {
        [re[i], re[j]] = [re[j], re[i]];
        [im[i], im[j]] = [im[j], im[i]];
      }
    }
    for (let len = 2; len <= n; len <<= 1) {
      const ang = (2 * Math.PI / len) * (invert ? 1 : -1);
      const wpr = Math.cos(ang), wpi = Math.sin(ang);
      let wr = 1, wi = 0;
      for (let i = 0; i < n; i += len) {
        for (let k = 0; k < len / 2; k++) {
          const tRe = wr * re[i + k + len / 2] - wi * im[i + k + len / 2];
          const tIm = wr * im[i + k + len / 2] + wi * re[i + k + len / 2];
          re[i + k + len / 2] = re[i + k] - tRe;
          im[i + k + len / 2] = im[i + k] - tIm;
          re[i + k] += tRe;
          im[i + k] += tIm;
          const nwr = wr * wpr - wi * wpi;
          wi = wr * wpi + wi * wpr;
          wr = nwr;
        }
      }
    }
    if (invert) {
      const inv = 1 / n;
      for (let i = 0; i < n; i++) { re[i] *= inv; im[i] *= inv; }
    }
  }

  /* ---------- Encode WAV (16-bit PCM) for download ---------- */
  function encodeWAV(buffer) {
    const numCh = buffer.numberOfChannels;
    const len = buffer.length;
    const sr = buffer.sampleRate;
    const inter = numCh === 1 ? [buffer.getChannelData(0)] : [];
    for (let c = 0; c < numCh; c++) inter.push(buffer.getChannelData(c));
    const bytes = new ArrayBuffer(44 + len * numCh * 2);
    const dv = new DataView(bytes);
    const wr = (o, s) => { for (let i = 0; i < s.length; i++) dv.setUint8(o + i, s.charCodeAt(i)); };
    wr(0, 'RIFF'); dv.setUint32(4, 36 + len * numCh * 2, true); wr(8, 'WAVE');
    wr(12, 'fmt '); dv.setUint32(16, 16, true); dv.setUint16(20, 1, true);
    dv.setUint16(22, numCh, true); dv.setUint32(24, sr, true);
    dv.setUint32(28, sr * numCh * 2, true); dv.setUint16(32, numCh * 2, true);
    dv.setUint16(34, 16, true); wr(36, 'data'); dv.setUint32(40, len * numCh * 2, true);
    let off = 44;
    for (let i = 0; i < len; i++) {
      for (let c = 0; c < numCh; c++) {
        let s = Math.max(-1, Math.min(1, inter[c][i]));
        dv.setInt16(off, s < 0 ? s * 0x8000 : s * 0x7fff, true);
        off += 2;
      }
    }
    return new Blob([bytes], { type: 'audio/wav' });
  }

  /* ---------- Processing engine selection ---------- */
  async function detectBackend() {
    if (state.backendAvailable !== null) return state.backendAvailable;
    try {
      const res = await fetch('/api/health', { method: 'GET' });
      state.backendAvailable = res.ok;
    } catch (_) {
      state.backendAvailable = false; // e.g. opened via file://
    }
    return state.backendAvailable;
  }

  // Server path: upload to FastAPI, decode the returned WAV for playback.
  async function processViaBackend() {
    setProgress(10, '正在上传…');
    const fd = new FormData();
    fd.append('file', state.originalFile);
    fd.append('semitones', String(state.semitones));
    el.progressText.textContent = '服务端处理中…';

    const res = await fetch('/api/v1/process', { method: 'POST', body: fd });
    const payload = await res.json().catch(() => ({}));
    if (!res.ok || payload.status !== 'success') {
      throw new Error(payload.message || `请求失败 (${res.status})`);
    }

    setProgress(85, '正在加载结果…');
    const blob = await fetch(payload.output_url).then((r) => r.blob());
    const arrayBuf = await blob.arrayBuffer();
    const ctx = ensureCtx();
    const processed = await ctx.decodeAudioData(arrayBuf);
    state.processedBuffer = processed;

    // Download points straight at the server; no local object URL needed.
    if (state.downloadUrl) URL.revokeObjectURL(state.downloadUrl);
    state.downloadUrl = payload.output_url;
    el.downloadBtn.href = payload.output_url;
    const base = state.fileName.replace(/\.[^.]+$/, '');
    el.downloadBtn.setAttribute('download', `${base}_shifted.wav`);
  }

  // Offline fallback: in-browser phase-vocoder (unchanged core DSP).
  async function processClientSide() {
    const { audioCtx, originalBuffer } = state;
    const sr = originalBuffer.sampleRate;
    const sem = state.semitones;

    // Work on a mono mix to keep DSP fast & consistent
    const mono = toMono(originalBuffer);
    const input = mono.getChannelData(0);

    await sleep(30);
    setProgress(20, '正在计算相位声码器…');
    await sleep(20);

    const frameSize = 2048;
    let output;
    try {
      output = pitchShift(input, sr, sem, frameSize);
    } catch (e) {
      console.error(e);
      throw new Error('本地处理失败');
    }

    setProgress(75, '正在合成输出…');
    await sleep(20);

    // Build stereo output buffer (duplicate mono -> stereo)
    const outputBuf = audioCtx.createBuffer(2, output.length, sr);
    outputBuf.getChannelData(0).set(output);
    outputBuf.getChannelData(1).set(output);
    state.processedBuffer = outputBuf;

    // Build download blob
    const wav = encodeWAV(outputBuf);
    if (state.downloadUrl) URL.revokeObjectURL(state.downloadUrl);
    state.downloadUrl = URL.createObjectURL(wav);
    el.downloadBtn.href = state.downloadUrl;
    const base = state.fileName.replace(/\.[^.]+$/, '');
    el.downloadBtn.setAttribute('download', `${base}_shifted.wav`);
  }

  async function processAudio() {
    if (!state.originalBuffer || state.processing) return;
    state.processing = true;
    if (state.playing) pause();
    el.processBtn.disabled = true;
    el.progressWrap.hidden = false;
    el.downloadBtn.hidden = true;
    setProgress(0, '准备中…');

    const backend = await detectBackend();
    setProgress(5, backend ? '服务端处理中…' : '本地引擎处理中…');

    try {
      if (backend) await processViaBackend();
      else await processClientSide();
    } catch (e) {
      console.error(e);
      toast('处理失败：' + e.message, true);
      finishProcessing(false);
      return;
    }

    setProgress(100, '完成');
    await sleep(200);
    finishProcessing(true);
  }

  function finishProcessing(success) {
    state.processing = false;
    el.processBtn.disabled = false;
    el.processBtn.querySelector('.btn-label').textContent = success ? '重新处理' : '处理';
    if (success) {
      el.wavePlaceholder.classList.add('hidden');
      el.transport.hidden = false;
      el.seek.disabled = false;
      drawWaveform(state.processedBuffer);
      el.durTime.textContent = fmtTime(state.processedBuffer.duration);
      el.downloadBtn.hidden = false;
      toast('处理完成，可以试听或下载');
    } else {
      setTimeout(() => { el.progressWrap.hidden = true; }, 400);
    }
  }

  function toMono(buf) {
    if (buf.numberOfChannels === 1) return buf;
    const mono = buf.audioCtx.createBuffer(1, buf.length, buf.sampleRate);
    let sum = new Float32Array(buf.length);
    for (let c = 0; c < buf.numberOfChannels; c++) {
      const ch = buf.getChannelData(c);
      for (let i = 0; i < buf.length; i++) sum[i] += ch[i];
    }
    const md = mono.getChannelData(0);
    for (let i = 0; i < buf.length; i++) md[i] = sum[i] / buf.numberOfChannels;
    return mono;
  }

  function setProgress(pct, text) {
    el.progressBar.style.width = pct + '%';
    if (text) el.progressText.textContent = text;
  }

  function sleep(ms) { return new Promise((r) => setTimeout(r, ms)); }

  /* ---------- File handling ---------- */
  async function handleFile(file) {
    if (!file) return;
    const ext = (file.name.split('.').pop() || '').toLowerCase();
    const okExt = ['mp3', 'wav', 'flac', 'aac', 'ogg', 'm4a', 'mp4'];
    if (!okExt.includes(ext)) {
      toast('不支持的格式，请选择 MP3 / WAV / FLAC / AAC / OGG', true);
      return;
    }
    if (file.size > MAX_FILE) {
      toast(`文件过大（${fmtSize(file.size)}），请上传小于 50MB 的文件`, true);
      return;
    }

    // decode
    setProgress && setProgress(0, '正在解码…');
    el.progressWrap.hidden = false;
    el.progressText.textContent = '正在解码音频…';
    el.progressBar.style.width = '0%';
    let decoded = null;
    try {
      const arrayBuf = await file.arrayBuffer();
      const ctx = ensureCtx();
      decoded = await ctx.decodeAudioData(arrayBuf);
      if (decoded.duration > MAX_DURATION) {
        toast(`时长超过限制（${fmtTime(decoded.duration)}），请上传小于 10 分钟的音频`, true);
        el.progressWrap.hidden = true;
        return;
      }
      state.originalBuffer = decoded;
      state.originalFile = file;
      state.fileName = file.name;
    } catch (e) {
      console.error(e);
      toast('无法读取该音频文件，格式可能损坏', true);
      el.progressWrap.hidden = true;
      return;
    }
    el.progressWrap.hidden = true;

    // UI
    el.fileName.textContent = file.name;
    el.fileDetail.textContent = `${fmtSize(file.size)} · ${fmtTime(decoded.duration)} · ${decoded.sampleRate} Hz`;
    el.fileInfo.hidden = false;
    el.dropzone.hidden = true;
    el.fileInput.value = '';

    // enable controls
    el.semRange.disabled = false;
    el.processBtn.disabled = false;
    toast('上传成功，选择升降调后处理');
  }

  function resetAll() {
    if (state.playing) pause();
    state.originalBuffer = null;
    state.processedBuffer = null;
    state.fileName = '';
    if (state.downloadUrl) { URL.revokeObjectURL(state.downloadUrl); state.downloadUrl = null; }
    el.fileInfo.hidden = true;
    el.dropzone.hidden = false;
    el.semRange.disabled = true;
    el.processBtn.disabled = true;
    el.downloadBtn.hidden = true;
    el.transport.hidden = true;
    el.seek.disabled = true;
    el.progressWrap.hidden = true;
    el.progressBar.style.width = '0%';
    el.wavePlaceholder.classList.remove('hidden');
    const ctx = el.waveCanvas.getContext('2d');
    ctx.clearRect(0, 0, el.waveCanvas.width, el.waveCanvas.height);
    setSemitone(0);
  }

  /* ---------- Semitone / UI sync ---------- */
  function setSemitone(val) {
    state.semitones = val;
    el.semRange.value = val;
    el.pitchValue.textContent = (val > 0 ? '+' : '') + val;
    el.pitchValue.classList.toggle('pos', val > 0);
    el.pitchValue.classList.toggle('neg', val < 0);
    el.pitchDir.textContent = val === 0 ? '原调' : val > 0 ? '升调' : '降调';
    // estimate resulting key label
    el.pitchKey.textContent = describeKey(val);
    // update active chip
    document.querySelectorAll('.chip').forEach((c) => {
      c.classList.toggle('is-active', parseInt(c.dataset.val, 10) === val);
    });
  }

  // Simple key estimate: assume C major input, shift by semitones
  function describeKey(sem) {
    const idx = ((sem % 12) + 12) % 12;
    const name = NOTE_NAMES[idx];
    return sem === 0 ? 'C 大调' : `${name} 大调`;
  }

  /* ---------- Events ---------- */
  el.dropzone.addEventListener('click', () => el.fileInput.click());
  el.dropzone.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); el.fileInput.click(); }
  });
  el.fileInput.addEventListener('change', (e) => { if (e.target.files[0]) handleFile(e.target.files[0]); });

  ['dragenter', 'dragover'].forEach((ev) =>
    el.dropzone.addEventListener(ev, (e) => { e.preventDefault(); el.dropzone.classList.add('drag'); })
  );
  ['dragleave', 'drop'].forEach((ev) =>
    el.dropzone.addEventListener(ev, (e) => { e.preventDefault(); el.dropzone.classList.remove('drag'); })
  );
  el.dropzone.addEventListener('drop', (e) => {
    const f = e.dataTransfer.files[0];
    if (f) handleFile(f);
  });

  el.fileRemove.addEventListener('click', resetAll);

  el.semRange.addEventListener('input', (e) => setSemitone(parseInt(e.target.value, 10)));

  el.presetChips.addEventListener('click', (e) => {
    const chip = e.target.closest('.chip');
    if (!chip) return;
    setSemitone(parseInt(chip.dataset.val, 10));
  });

  el.processBtn.addEventListener('click', processAudio);
  el.playBtn.addEventListener('click', togglePlay);

  let seeking = false;
  el.seek.addEventListener('input', () => {
    seeking = true;
    const buffer = state.processedBuffer || state.originalBuffer;
    if (!buffer) return;
    const t = (el.seek.value / 1000) * buffer.duration;
    state.seekOffset = t;
    el.curTime.textContent = fmtTime(t);
  });
  el.seek.addEventListener('change', () => {
    seeking = false;
    if (state.playing) playFrom(state.seekOffset != null ? state.seekOffset : state.offset);
  });

  // Nav scroll style
  const onScroll = () => el.nav.classList.toggle('scrolled', window.scrollY > 8);
  window.addEventListener('scroll', onScroll, { passive: true });
  onScroll();

  // Reveal on scroll
  const io = new IntersectionObserver((entries) => {
    entries.forEach((en) => { if (en.isIntersecting) en.target.classList.add('in'); io.unobserve(en.target); });
  }, { threshold: 0.12 });
  document.querySelectorAll('[data-reveal]').forEach((n) => io.observe(n));

  // Keyboard: space toggles play when not typing
  document.addEventListener('keydown', (e) => {
    if (e.code === 'Space' && e.target.tagName !== 'INPUT' && e.target.tagName !== 'BUTTON') {
      if (el.downloadBtn.hidden === false || state.processedBuffer) { e.preventDefault(); togglePlay(); }
    }
  });

  // Init
  setSemitone(0);
})();
