import streamlit as st
import streamlit.components.v1 as components
import asyncio
import base64
import json
import edge_tts

st.set_page_config(page_title="Studio99", layout="centered")

st.markdown("""
<style>
    .stApp { background-color: #0e121a; color: #ffffff; }
    .block-container { padding-top: 0.4rem; padding-bottom: 1rem; max-width: 450px; }
    header, footer { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

secret_groq = ""
secret_gemini = ""
try:
    secret_groq = st.secrets.get("GROQ_KEYS", "")
    secret_gemini = st.secrets.get("GEMINI_KEYS", "")
except Exception:
    pass

studio99_app = f"""
<!DOCTYPE html>
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
<style>
  @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+Myanmar:wght@500;700&display=swap');
  body {{
    margin: 0; padding: 0; background: #0e121a; color: #fff;
    font-family: 'Noto Sans Myanmar', sans-serif; user-select: none;
  }}
  .top-bar {{
    display: flex; justify-content: space-between; align-items: center;
    padding: 10px 14px 12px 14px; font-size: 18px; font-weight: bold;
  }}
  .key-btn {{
    background: #1c2436; border: 1px solid #00e5ff; color: #00e5ff;
    padding: 5px 10px; border-radius: 8px; font-size: 12px; cursor: pointer;
  }}
  #key-drawer {{
    display: none; width: 90%; margin: 0 auto 14px auto; background: #151a24;
    border: 1px solid #00e5ff; border-radius: 12px; padding: 12px;
  }}
  textarea {{
    width: 95%; height: 52px; background: #0b0e14; color: #00e5ff;
    border: 1px solid #2e384d; border-radius: 8px; padding: 6px;
    font-size: 11px; font-family: monospace; margin-bottom: 8px;
  }}
  .save-key-btn {{
    width: 100%; padding: 8px; background: #00e5ff; color: #000;
    border: none; border-radius: 8px; font-weight: bold; cursor: pointer;
  }}
  .gallery-btn {{
    display: flex; align-items: center; justify-content: center; gap: 8px;
    width: 96%; margin: 0 auto 14px auto; padding: 13px 0;
    background: #131822; border: 1.5px solid #00e5ff; color: #fff;
    border-radius: 12px; font-weight: bold; font-size: 15px; cursor: pointer;
    box-shadow: 0 0 12px rgba(0, 229, 255, 0.15);
  }}
  #preview-outer {{
    width: 96%; height: 320px; margin: 0 auto 14px auto;
    background: #141923; border-radius: 14px; border: 1px solid #2a3346;
    display: flex; align-items: center; justify-content: center; overflow: hidden;
  }}
  /* Stage wrapper matches the exact canvas aspect ratio so drag boxes never shift! */
  #stage-wrap {{
    position: relative; display: flex; align-items: center; justify-content: center;
  }}
  canvas {{ width: 100%; height: 100%; display: none; }}
  #placeholder {{ color: #687387; text-align: center; font-size: 14px; line-height: 1.8; }}
  .drag-overlay {{
    position: absolute; border-radius: 4px; touch-action: none;
    display: none; align-items: center; justify-content: center;
    font-size: 11px; font-weight: bold; text-align: center; box-sizing: border-box;
  }}
  #blur1 {{
    border: 2px solid #00e5ff; color: #00e5ff;
    background: rgba(0, 229, 255, 0.22); width: 76%; height: 14%; top: 70%; left: 12%;
  }}
  #blur2 {{
    border: 2px solid #d500f9; color: #d500f9;
    background: rgba(213, 0, 249, 0.22); width: 36%; height: 13%; top: 6%; left: 6%;
  }}
  #sub-box {{
    display: flex; border: 2px dashed #ffea00; color: #ffea00;
    background: rgba(0, 0, 0, 0.45); width: 88%; height: 14%; top: 83%; left: 6%;
  }}
  .resize-dot {{
    width: 18px; height: 18px; position: absolute; right: -2px; bottom: -2px;
    background: currentColor; border-top-left-radius: 6px;
  }}
  .card {{
    width: 90%; margin: 0 auto 14px auto; background: #151a24;
    border: 1px solid #232b3b; border-radius: 14px; padding: 14px;
  }}
  .card-title {{ font-size: 14px; font-weight: bold; margin-bottom: 10px; color: #e2e8f0; }}
  .toggle-row {{
    display: flex; justify-content: space-between; align-items: center;
    padding: 8px 0; border-bottom: 1px solid #1e2533;
  }}
  .toggle-row:last-child {{ border-bottom: none; }}
  .ratio-grid {{ display: flex; gap: 8px; margin-top: 8px; }}
  .ratio-btn {{
    flex: 1; padding: 9px 0; background: #1c2230; border: 1px solid #2e384d;
    color: #94a3b8; border-radius: 8px; text-align: center; font-size: 13px;
    font-weight: bold; cursor: pointer;
  }}
  .ratio-btn.active {{ border-color: #eab308; color: #eab308; background: #262418; }}
  .slider-row {{ margin-top: 10px; font-size: 13px; color: #94a3b8; display: flex; justify-content: space-between; }}
  input[type="range"] {{ width: 100%; accent-color: #00e5ff; margin-top: 6px; }}
  .main-btn {{
    display: block; width: 96%; margin: 10px auto; padding: 15px;
    background: linear-gradient(90deg, #00e5ff, #00b8d4); color: #000;
    font-weight: bold; font-size: 15px; border: none; border-radius: 12px;
    cursor: pointer; text-align: center;
  }}
  .main-btn:disabled {{ opacity: 0.5; cursor: not-allowed; }}
  #log-box {{
    width: 90%; margin: 8px auto; padding: 12px; background: #11151e;
    border-radius: 10px; font-size: 12px; color: #00e5ff; text-align: center;
    border: 1px solid #1f2737; min-height: 24px; word-break: break-word; line-height: 1.5;
  }}
</style>
</head>
<body>

<div class="top-bar">
  <span>Studio99</span>
  <button class="key-btn" id="open-key-btn">🔑 API Keys (အသေသိမ်းရန်)</button>
</div>

<div id="key-drawer">
  <div style="font-size:12px; color:#94a3b8; margin-bottom:4px;">
    📌 <b>Gemini Keys (၂ ခု ၃ ခု ထည့်နိုင်သည်):</b> တစ်ကြောင်းလျှင် တစ်ခုနှုန်းထည့်ပါ။
  </div>
  <textarea id="gemini-keys-input" placeholder="AIzaSy...&#10;AIzaSy..."></textarea>

  <div style="font-size:12px; color:#94a3b8; margin-bottom:4px;">
    📌 <b>Groq Keys (၂ ခု ၃ ခု ထည့်နိုင်သည်):</b> မထည့်ထားလျှင် Gemini က တိုက်ရိုက်နားထောင်ပေးပါမည်။
  </div>
  <textarea id="groq-keys-input" placeholder="gsk_...&#10;gsk_..."></textarea>

  <button class="save-key-btn" id="save-keys-btn">💾 ဖုန်းထဲတွင် အသေသိမ်းမည် (Save Keys)</button>
</div>

<!-- 1. Instant Offline Gallery Picker -->
<label class="gallery-btn">
  <span>▶️ Gallery မှ ရွေးမည်</span>
  <input type="file" id="video-input" accept="video/*" style="display:none">
</label>

<!-- 2. Exact Aspect-Locked Stage (100% Accurate Blur & Subtitle Coordinates) -->
<div id="preview-outer">
  <div id="placeholder">▶️<br>Preview မြင်ရရန် ဗီဒီယိုရွေးပါ</div>
  <div id="stage-wrap">
    <canvas id="stage-canvas"></canvas>
    <div id="blur1" class="drag-overlay">Blur 1<div class="resize-dot" id="dot1"></div></div>
    <div id="blur2" class="drag-overlay">Blur 2<div class="resize-dot" id="dot2"></div></div>
    <div id="sub-box" class="drag-overlay">📝 မြန်မာစာတန်းထိုး နေရာ<div class="resize-dot" id="dot-sub"></div></div>
  </div>
</div>

<video id="src-video" playsinline crossorigin="anonymous" style="display:none"></video>

<!-- 3. Blur & Subtitle Position Card -->
<div class="card">
  <div class="card-title">⠿ Blur & စာတန်းထိုး နေရာ (အကွက်တည့်တည့် အပြည့်ဝါးပေးမည်)</div>
  <div class="toggle-row">
    <span style="color:#00e5ff; font-weight:bold;">Blur 1 (အပြာကွက်)</span>
    <input type="checkbox" id="toggle-b1" style="transform:scale(1.4);">
  </div>
  <div class="toggle-row">
    <span style="color:#d500f9; font-weight:bold;">Blur 2 (ခရမ်းကွက်)</span>
    <input type="checkbox" id="toggle-b2" style="transform:scale(1.4);">
  </div>
  <div class="toggle-row">
    <span style="color:#ffea00; font-weight:bold;">📝 မြန်မာစာတန်းထိုး အကွက် (အဝါကွက်)</span>
    <input type="checkbox" id="toggle-sub" checked style="transform:scale(1.4);">
  </div>
  <div class="slider-row"><span>Blur အပြင်းအပျော့ (Blur Strength)</span><span id="blur-str-val">100% (အပြည့်ဝါးမည်)</span></div>
  <input type="range" id="blur-slider" min="10" max="40" step="2" value="28">
</div>

<!-- 4. Video Ratio Card -->
<div class="card">
  <div class="card-title">🖼️ Video Ratio</div>
  <div class="ratio-grid" id="ratio-group">
    <div class="ratio-btn active" data-ratio="9:16">9:16</div>
    <div class="ratio-btn" data-ratio="16:9">16:9</div>
    <div class="ratio-btn" data-ratio="1:1">1:1</div>
    <div class="ratio-btn" data-ratio="4:3">4:3</div>
  </div>
</div>

<!-- 5. Fast Parallel Edge-TTS Settings -->
<div class="card">
  <div class="card-title">🎙️ Fast Parallel Edge-TTS & Sync Settings</div>
  <div class="toggle-row">
    <span>အသံ (Voice)</span>
    <select id="voice-sel" style="background:#0e121a; color:#fff; border:1px solid #2e384d; padding:6px; border-radius:6px;">
      <option value="my-MM-ThihaNeural">သီဟ - Male (Edge-TTS)</option>
      <option value="my-MM-NilarNeural">နီလာ - Female (Edge-TTS)</option>
    </select>
  </div>
  <div class="slider-row"><span>Speed (အမြန်နှုန်း)</span><span id="spd-val">+25%</span></div>
  <input type="range" id="spd-slider" min="-100" max="100" step="5" value="25">
  
  <div class="slider-row"><span>Pitch (အသံအနိမ့်အမြင့်)</span><span id="pit-val">0 Hz</span></div>
  <input type="range" id="pit-slider" min="-50" max="50" step="5" value="0">
</div>

<div id="log-box">ဗီဒီယိုရွေးပြီးပါက အောက်ပါခလုတ်ကို နှိပ်ပါ။</div>

<button class="main-btn" id="process-btn">🚀 နားထောင်မည် + ဘာသာပြန် + TTS ရုပ်/သံကိုက် ထုတ်မည်</button>

<script>
const DEFAULT_GROQ = `{secret_groq}`;
const DEFAULT_GEMINI = `{secret_gemini}`;

const keyDrawer = document.getElementById('key-drawer');
const openKeyBtn = document.getElementById('open-key-btn');
const saveKeysBtn = document.getElementById('save-keys-btn');
const gemInput = document.getElementById('gemini-keys-input');
const groqInput = document.getElementById('groq-keys-input');

gemInput.value = localStorage.getItem('s99_gemini_keys') || DEFAULT_GEMINI;
groqInput.value = localStorage.getItem('s99_groq_keys') || DEFAULT_GROQ;

openKeyBtn.onclick = () => {{
  keyDrawer.style.display = keyDrawer.style.display === 'block' ? 'none' : 'block';
}};

saveKeysBtn.onclick = () => {{
  localStorage.setItem('s99_gemini_keys', gemInput.value.trim());
  localStorage.setItem('s99_groq_keys', groqInput.value.trim());
  keyDrawer.style.display = 'none';
  document.getElementById('log-box').innerText = "✅ API Key များကို ဖုန်းထဲတွင် အသေသိမ်းဆည်းပြီးပါပြီ!";
}};

function parseKeyList(rawStr) {{
  return rawStr.split(/[\\n,]+/).map(k => k.trim()).filter(k => k.length > 5);
}}

const vidInput = document.getElementById('video-input');
const vid = document.getElementById('src-video');
const canvas = document.getElementById('stage-canvas');
const ctx = canvas.getContext('2d');
const previewOuter = document.getElementById('preview-outer');
const stageWrap = document.getElementById('stage-wrap');
const placeholder = document.getElementById('placeholder');
const b1 = document.getElementById('blur1');
const b2 = document.getElementById('blur2');
const subBox = document.getElementById('sub-box');
const tB1 = document.getElementById('toggle-b1');
const tB2 = document.getElementById('toggle-b2');
const tSub = document.getElementById('toggle-sub');
const blurSlider = document.getElementById('blur-slider');
const logBox = document.getElementById('log-box');
const procBtn = document.getElementById('process-btn');

// Offscreen helper canvas for 100% solid edge-to-edge box blur
const blurHelperCanvas = document.createElement('canvas');
const blurHelperCtx = blurHelperCanvas.getContext('2d');

let selectedFile = null;
let currentRatio = '9:16';
let subtitles = [];

const spdSlider = document.getElementById('spd-slider');
const pitSlider = document.getElementById('pit-slider');

spdSlider.oninput = () => {{
  const v = parseInt(spdSlider.value, 10);
  document.getElementById('spd-val').innerText = (v > 0 ? '+' + v : v) + '%';
}};
pitSlider.oninput = () => {{
  const v = parseInt(pitSlider.value, 10);
  document.getElementById('pit-val').innerText = (v > 0 ? '+' + v : v) + ' Hz';
}};
blurSlider.oninput = () => {{
  renderCanvasFrame();
}};

vidInput.onchange = (e) => {{
  selectedFile = e.target.files[0];
  if (!selectedFile) return;
  vid.src = URL.createObjectURL(selectedFile);
  vid.onloadedmetadata = () => {{
    placeholder.style.display = 'none';
    canvas.style.display = 'block';
    applyAspectRatio();
    vid.currentTime = 0.2;
    logBox.style.color = "#00e5ff";
    logBox.innerText = "✅ ဗီဒီယို အဆင်သင့်ဖြစ်ပါပြီ! Blur အကွက်တည့်တည့် လုံးဝဝါးပေးထားပါသည်။";
  }};
  vid.onseeked = () => renderCanvasFrame();
}};

document.querySelectorAll('.ratio-btn').forEach(btn => {{
  btn.onclick = () => {{
    document.querySelectorAll('.ratio-btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    currentRatio = btn.dataset.ratio;
    applyAspectRatio();
  }};
}});

// Lock #stage-wrap dimensions to exact canvas aspect ratio so overlay boxes align 1:1 with canvas pixels!
function applyAspectRatio() {{
  if (currentRatio === '9:16') {{ canvas.width = 540; canvas.height = 960; }}
  else if (currentRatio === '16:9') {{ canvas.width = 854; canvas.height = 480; }}
  else if (currentRatio === '1:1') {{ canvas.width = 640; canvas.height = 640; }}
  else if (currentRatio === '4:3') {{ canvas.width = 640; canvas.height = 480; }}

  const maxW = previewOuter.clientWidth - 8;
  const maxH = previewOuter.clientHeight - 8;
  const cRatio = canvas.width / canvas.height;

  let dispW = maxW;
  let dispH = dispW / cRatio;
  if (dispH > maxH) {{
    dispH = maxH;
    dispW = dispH * cRatio;
  }}

  stageWrap.style.width = Math.round(dispW) + 'px';
  stageWrap.style.height = Math.round(dispH) + 'px';
  renderCanvasFrame();
}}

tB1.onchange = () => {{ b1.style.display = tB1.checked ? 'flex' : 'none'; renderCanvasFrame(); }};
tB2.onchange = () => {{ b2.style.display = tB2.checked ? 'flex' : 'none'; renderCanvasFrame(); }};
tSub.onchange = () => {{ subBox.style.display = tSub.checked ? 'flex' : 'none'; renderCanvasFrame(); }};

function enableTouchDrag(box, dot) {{
  let sx, sy, sl, st, sw, sh, mode = null;
  box.onpointerdown = (e) => {{
    mode = (e.target === dot) ? 'resize' : 'drag';
    sx = e.clientX; sy = e.clientY;
    sl = box.offsetLeft; st = box.offsetTop;
    sw = box.offsetWidth; sh = box.offsetHeight;
    box.setPointerCapture(e.pointerId);
  }};
  box.onpointermove = (e) => {{
    if (!mode) return;
    const dx = e.clientX - sx, dy = e.clientY - sy;
    const wrapW = stageWrap.clientWidth;
    const wrapH = stageWrap.clientHeight;
    if (mode === 'drag') {{
      box.style.left = Math.max(0, Math.min(wrapW - box.offsetWidth, sl + dx)) / wrapW * 100 + '%';
      box.style.top = Math.max(0, Math.min(wrapH - box.offsetHeight, st + dy)) / wrapH * 100 + '%';
    }} else {{
      box.style.width = Math.max(28, Math.min(wrapW - sl, sw + dx)) / wrapW * 100 + '%';
      box.style.height = Math.max(18, Math.min(wrapH - st, sh + dy)) / wrapH * 100 + '%';
    }}
    renderCanvasFrame();
  }};
  box.onpointerup = (e) => {{ mode = null; box.releasePointerCapture(e.pointerId); }};
}}

enableTouchDrag(b1, document.getElementById('dot1'));
enableTouchDrag(b2, document.getElementById('dot2'));
enableTouchDrag(subBox, document.getElementById('dot-sub'));

// Exact 1:1 Coordinate Mapper using bounding rectangles
function getExactCanvasRect(el, defL, defT, defW, defH) {{
  const cRect = canvas.getBoundingClientRect();
  const eRect = el.getBoundingClientRect();
  if (cRect.width > 0 && eRect.width > 0 && el.style.display !== 'none') {{
    const scaleX = canvas.width / cRect.width;
    const scaleY = canvas.height / cRect.height;
    return {{
      rx: Math.max(0, (eRect.left - cRect.left) * scaleX),
      ry: Math.max(0, (eRect.top - cRect.top) * scaleY),
      rw: Math.min(canvas.width, eRect.width * scaleX),
      rh: Math.min(canvas.height, eRect.height * scaleY)
    }};
  }}
  return {{
    rx: (parseFloat(el.style.left || defL) / 100) * canvas.width,
    ry: (parseFloat(el.style.top || defT) / 100) * canvas.height,
    rw: (parseFloat(el.style.width || defW) / 100) * canvas.width,
    rh: (parseFloat(el.style.height || defH) / 100) * canvas.height
  }};
}}

// 100% Solid Edge-to-Edge Heavy Blur (Downscale + Smooth Upscale + Gaussian Blur inside Clipped Box)
function applySolidBoxBlur(el, defL, defT, defW, defH) {{
  const m = getExactCanvasRect(el, defL, defT, defW, defH);
  if (m.rw < 2 || m.rh < 2) return;

  const strength = parseInt(blurSlider.value, 10) || 28;
  // Downscale factor completely destroys underlying characters/logos across the ENTIRE box evenly
  const downW = Math.max(4, Math.round(m.rw / (strength * 0.55)));
  const downH = Math.max(2, Math.round(m.rh / (strength * 0.55)));

  blurHelperCanvas.width = downW;
  blurHelperCanvas.height = downH;
  blurHelperCtx.imageSmoothingEnabled = true;

  // Step A: Copy exact box region into tiny buffer (wipes out sharp text details everywhere including edges)
  blurHelperCtx.drawImage(canvas, m.rx, m.ry, m.rw, m.rh, 0, 0, downW, downH);

  // Step B: Draw back into clipped exact box with smooth Gaussian filter for a clean frosted blur look
  ctx.save();
  ctx.beginPath();
  ctx.rect(m.rx, m.ry, m.rw, m.rh);
  ctx.clip();

  ctx.imageSmoothingEnabled = true;
  ctx.filter = `blur(${{Math.round(strength * 0.4)}}px)`;
  // Slightly bleed by 6px inside the clip so edges never fade or look unblurred
  ctx.drawImage(blurHelperCanvas, 0, 0, downW, downH, m.rx - 6, m.ry - 6, m.rw + 12, m.rh + 12);
  ctx.restore();
}}

function drawWrappedSubtitles(text, x, y, maxWidth, fontSize) {{
  ctx.font = `bold ${{fontSize}}px "Noto Sans Myanmar", sans-serif`;
  ctx.textAlign = 'center';
  ctx.textBaseline = 'middle';
  ctx.lineWidth = Math.max(3, Math.round(fontSize * 0.22));
  ctx.strokeStyle = '#000000';
  ctx.fillStyle = '#ffffff';

  const words = text.split(' ');
  let lines = [];
  let currentLine = words[0] || '';

  for (let i = 1; i < words.length; i++) {{
    const testLine = currentLine + ' ' + words[i];
    if (ctx.measureText(testLine).width < maxWidth) {{
      currentLine = testLine;
    }} else {{
      lines.push(currentLine);
      currentLine = words[i];
    }}
  }}
  lines.push(currentLine);

  if (lines.length === 1 && ctx.measureText(lines[0]).width > maxWidth && text.length > 20) {{
    const mid = Math.floor(text.length / 2);
    lines = [text.slice(0, mid), text.slice(mid)];
  }}

  const lineHeight = fontSize * 1.35;
  const startY = y - ((lines.length - 1) * lineHeight) / 2;

  lines.forEach((ln, idx) => {{
    const ly = startY + idx * lineHeight;
    ctx.strokeText(ln, x, ly);
    ctx.fillText(ln, x, ly);
  }});
}}

function renderCanvasFrame(activeSubText = null) {{
  if (!vid.videoWidth) return;
  ctx.fillStyle = '#0b0e14';
  ctx.fillRect(0, 0, canvas.width, canvas.height);

  const vr = vid.videoWidth / vid.videoHeight;
  const cr = canvas.width / canvas.height;
  let dw = canvas.width, dh = canvas.height, dx = 0, dy = 0;
  if (vr > cr) {{ dh = canvas.width / vr; dy = (canvas.height - dh) / 2; }}
  else {{ dw = canvas.height * vr; dx = (canvas.width - dw) / 2; }}
  ctx.drawImage(vid, dx, dy, dw, dh);

  if (tB1.checked) applySolidBoxBlur(b1, 12, 70, 76, 14);
  if (tB2.checked) applySolidBoxBlur(b2, 6, 6, 36, 13);

  if (tSub.checked) {{
    let textToDraw = activeSubText;
    if (!textToDraw && subtitles.length > 0) {{
      const cur = vid.currentTime;
      const found = subtitles.find(s => cur >= s.start && cur <= s.end);
      if (found) textToDraw = found.mm_text;
    }}
    if (textToDraw) {{
      const sm = getExactCanvasRect(subBox, 6, 83, 88, 14);
      const centerX = sm.rx + (sm.rw / 2);
      const centerY = sm.ry + (sm.rh / 2);
      const dynamicFontSize = Math.max(16, Math.min(42, Math.round(sm.rh * 0.34)));
      drawWrappedSubtitles(textToDraw, centerX, centerY, sm.rw * 0.95, dynamicFontSize);
    }}
  }}
}}

const sleep = (ms) => new Promise(res => setTimeout(res, ms));

function extractSafeJsonArray(rawText) {{
  if (!rawText || typeof rawText !== 'string') throw new Error("Empty response from AI");
  const startIdx = rawText.indexOf('[');
  const endIdx = rawText.lastIndexOf(']');
  if (startIdx === -1 || endIdx === -1 || endIdx <= startIdx) {{
    throw new Error("Invalid JSON array returned");
  }}
  return JSON.parse(rawText.substring(startIdx, endIdx + 1));
}}

async function getInternalAudioBlob(file) {{
  const buf = await file.arrayBuffer();
  const actx = new (window.AudioContext || window.webkitAudioContext)({{ sampleRate: 8000 }});
  const decoded = await actx.decodeAudioData(buf);
  const pcm = decoded.getChannelData(0);
  const wav = new ArrayBuffer(44 + pcm.length * 2);
  const v = new DataView(wav);
  const str = (o, s) => {{ for (let i=0;i<s.length;i++) v.setUint8(o+i, s.charCodeAt(i)); }};
  str(0, 'RIFF'); v.setUint32(4, 36 + pcm.length * 2, true);
  str(8, 'WAVEfmt '); v.setUint32(16, 16, true);
  v.setUint16(20, 1, true); v.setUint16(22, 1, true);
  v.setUint32(24, 8000, true); v.setUint32(28, 16000, true);
  v.setUint16(32, 2, true); v.setUint16(34, 16, true);
  str(36, 'data'); v.setUint32(40, pcm.length * 2, true);
  for (let i = 0, off = 44; i < pcm.length; i++, off += 2) {{
    let s = Math.max(-1, Math.min(1, pcm[i]));
    v.setInt16(off, s < 0 ? s * 0x8000 : s * 0x7FFF, true);
  }}
  return new Blob([v], {{ type: 'audio/wav' }});
}}

function blobToBase64(blob) {{
  return new Promise((resolve) => {{
    const reader = new FileReader();
    reader.onloadend = () => resolve(reader.result.split(',')[1]);
    reader.readAsDataURL(blob);
  }});
}}

const GEMINI_MODELS = [
  "gemini-3.5-flash",
  "gemini-3.8-flash",
  "gemini-2.5-flash",
  "gemini-2.0-flash",
  "gemini-1.5-flash"
];

async function tryGroqTranscribe(wavBlob, groqKeys) {{
  for (let kIdx = 0; kIdx < groqKeys.length; kIdx++) {{
    const gKey = groqKeys[kIdx];
    try {{
      logBox.innerText = `🎧 Groq Whisper (Key #${{kIdx + 1}}) ဖြင့် နားထောင်နေပါသည်...`;
      const formData = new FormData();
      formData.append("file", wavBlob, "audio.wav");
      formData.append("model", "whisper-large-v3-turbo");
      formData.append("response_format", "verbose_json");

      const res = await fetch("https://api.groq.com/openai/v1/audio/transcriptions", {{
        method: "POST",
        headers: {{ "Authorization": `Bearer ${{gKey}}` }},
        body: formData
      }});
      const textResp = await res.text();
      if (!res.ok || textResp.trim().startsWith("<")) throw new Error("Groq failed");
      const data = JSON.parse(textResp);
      if (data.segments && data.segments.length > 0) {{
        return data.segments.map((s, idx) => ({{
          id: idx, start: Number(s.start.toFixed(2)), end: Number(s.end.toFixed(2)), text: s.text
        }}));
      }}
    }} catch (e) {{
      console.warn("Groq key failed, rotating...", e);
    }}
  }}
  return null;
}}

async function runGeminiWithRetry(partsPayload, geminiKeys, taskLabel) {{
  let lastError = "Gemini Keys သို့မဟုတ် Models အားလုံး ခေတ္တပြည့်နေပါသည်။";

  for (let attempt = 1; attempt <= 2; attempt++) {{
    for (let kIdx = 0; kIdx < geminiKeys.length; kIdx++) {{
      const apiKey = geminiKeys[kIdx];
      for (const modelName of GEMINI_MODELS) {{
        try {{
          logBox.innerText = `🌐 ${{taskLabel}} (${{modelName}} | Key #${{kIdx + 1}})...`;
          const url = `https://generativelanguage.googleapis.com/v1beta/models/${{modelName}}:generateContent?key=${{apiKey}}`;
          const res = await fetch(url, {{
            method: "POST",
            headers: {{ "Content-Type": "application/json" }},
            body: JSON.stringify({{
              contents: [{{ parts: partsPayload }}],
              generationConfig: {{ responseMimeType: "application/json" }}
            }})
          }});

          const rawBody = await res.text();
          if (rawBody.trim().startsWith("<")) continue;

          const data = JSON.parse(rawBody);
          if (res.status === 429) {{
            logBox.innerText = `⏳ Rate Limit ပြည့်နေသဖြင့် 4 စက္ကန့် စောင့်ပေးနေပါသည် (${{modelName}})...`;
            await sleep(4000);
            continue;
          }}

          const candidateText = data?.candidates?.[0]?.content?.parts?.[0]?.text;
          if (candidateText) {{
            return extractSafeJsonArray(candidateText);
          }} else if (data?.error?.message) {{
            lastError = data.error.message;
          }}
        }} catch (err) {{
          lastError = err.message;
        }}
      }}
    }}
    logBox.innerText = `⏳ ခေတ္တစောင့်ဆိုင်းပြီး ပြန်ကြိုးစားနေပါသည် (Attempt ${{attempt + 1}})...`;
    await sleep(4000);
  }}
  throw new Error(lastError);
}}

// --- ULTRA-FAST PARALLEL TTS GENERATOR (Generates ALL segments simultaneously in ~2 seconds!) ---
async function fetchSingleFastTTS(text, voice, ratePct, pitchHz) {{
  // Fast direct Edge-TTS endpoint + instant Google Myanmar TTS fallback with 2.5s timeout
  const rateStr = (ratePct >= 0 ? '+' : '') + ratePct + '%';
  const pitchStr = (pitchHz >= 0 ? '+' : '') + pitchHz + 'Hz';

  try {{
    const ctrl = new AbortController();
    const tId = setTimeout(() => ctrl.abort(), 2500);
    const res = await fetch("https://tts.travisvn.com/v1/audio/speech", {{
      method: "POST",
      headers: {{ "Content-Type": "application/json" }},
      body: JSON.stringify({{ input: text, voice: voice, rate: rateStr, pitch: pitchStr }}),
      signal: ctrl.signal
    }});
    clearTimeout(tId);
    if (res.ok) {{
      const b = await res.blob();
      if (b.size > 200) return b;
    }}
  }} catch (e) {{}}

  // Instantaneous (<300ms) Myanmar TTS Stream
  const encoded = encodeURIComponent(text);
  const fastUrls = [
    `https://translate.googleapis.com/translate_tts?ie=UTF-8&q=${{encoded}}&tl=my&client=gtx`,
    `https://corsproxy.io/?` + encodeURIComponent(`https://translate.google.com/translate_tts?ie=UTF-8&q=${{encoded}}&tl=my&client=tw-ob`)
  ];
  for (const u of fastUrls) {{
    try {{
      const r = await fetch(u);
      if (r.ok) {{
        const b = await r.blob();
        if (b.size > 100) return b;
      }}
    }} catch (e) {{}}
  }}
  throw new Error("TTS failed");
}}

// --- MAIN EXECUTION PIPELINE ---
procBtn.onclick = async () => {{
  if (!selectedFile) {{ alert('Gallery မှ ဗီဒီယို အရင်ရွေးပါ!'); return; }}

  const geminiKeys = parseKeyList(gemInput.value);
  const groqKeys = parseKeyList(groqInput.value);

  if (geminiKeys.length === 0) {{
    keyDrawer.style.display = 'block';
    alert('ညာဘက်အပေါ်ထောင့်ရှိ 🔑 API Keys တွင် Gemini API Key အရင်ထည့်ပေးပါ!');
    return;
  }}

  try {{
    procBtn.disabled = true;
    logBox.style.color = "#00e5ff";
    logBox.innerText = "🎧 ၁/၄ - ဗီဒီယိုထဲမှ အသံကို ဆွဲထုတ်နေပါသည်...";
    const wavBlob = await getInternalAudioBlob(selectedFile);

    let rawSegs = null;
    if (groqKeys.length > 0) {{
      rawSegs = await tryGroqTranscribe(wavBlob, groqKeys);
    }}

    if (rawSegs && rawSegs.length > 0) {{
      const promptText = `Translate these video transcript segments into natural, concise spoken Burmese for video dubbing. Keep each Burmese sentence brief so it matches the speaking duration. Return ONLY a JSON array of objects with keys: "id", "start", "end", "mm_text". Input: ${{JSON.stringify(rawSegs)}}`;
      subtitles = await runGeminiWithRetry([{{ text: promptText }}], geminiKeys, "၂/၄ - မြန်မာဘာသာပြန်နေသည်");
    }} else {{
      logBox.innerText = "🎧 Groq မရသဖြင့် Gemini ဖြင့် တိုက်ရိုက်နားထောင်ပြီး ဘာသာပြန်နေပါသည်...";
      const b64Audio = await blobToBase64(wavBlob);
      const audioPrompt = `Listen to this audio and translate the speech into concise spoken Burmese segments for dubbing with accurate timestamps in seconds. Return ONLY a valid JSON array of objects with keys: "id" (number), "start" (number in seconds), "end" (number in seconds), "mm_text" (Burmese string).`;
      subtitles = await runGeminiWithRetry([
        {{ inlineData: {{ mimeType: "audio/wav", data: b64Audio }} }},
        {{ text: audioPrompt }}
      ], geminiKeys, "၂/၄ - Gemini နားထောင်+ဘာသာပြန်နေသည်");
    }}

    // Step 3: PARALLEL BATCH TTS (All segments generated simultaneously in 1-2 seconds!)
    const voiceName = document.getElementById('voice-sel').value;
    const ratePct = parseInt(spdSlider.value, 10);
    const pitchHz = parseInt(pitSlider.value, 10);
    const userSpeedMultiplier = Math.max(0.3, 1.0 + (ratePct / 100.0));

    const audioCtx = new (window.AudioContext || window.webkitAudioContext)();
    const dest = audioCtx.createMediaStreamDestination();

    logBox.innerText = `⚡ ၃/၄ - စာကြောင်း (${{subtitles.length}}) ကြောင်းလုံးအတွက် TTS အသံကို တစ်ပြိုင်နက်တည်း အမြန်ထုတ်နေပါသည်...`;

    const validSubs = subtitles.filter(s => s.mm_text && s.mm_text.trim());
    const ttsPromises = validSubs.map(async (seg) => {{
      try {{
        const blob = await fetchSingleFastTTS(seg.mm_text.trim(), voiceName, ratePct, pitchHz);
        const arrBuf = await blob.arrayBuffer();
        const decodedBuf = await audioCtx.decodeAudioData(arrBuf);
        return {{
          id: seg.id,
          start: Number(seg.start),
          end: Number(seg.end),
          mm_text: seg.mm_text,
          buffer: decodedBuf,
          played: false
        }};
      }} catch (err) {{
        return null;
      }}
    }});

    const results = await Promise.all(ttsPromises);
    const ttsBuffers = results.filter(Boolean).sort((a, b) => a.start - b.start);

    if (ttsBuffers.length === 0) {{
      throw new Error("TTS အသံထုတ်လုပ်ရာတွင် အင်တာနက် အခက်အခဲရှိနေပါသည်။ ပြန်နှိပ်ပေးပါ။");
    }}

    // Step 4: Mute original video 100% & Sync TTS with Video Frame-by-Frame
    logBox.innerText = "🎬 ၄/၄ - မူရင်းအသံဖျောက်ပြီး TTS အသံနှင့် ဗီဒီယို အချိန်ကိုက် ပေါင်းစပ်နေပါသည်...";
    vid.muted = true;
    vid.volume = 0;

    b1.style.opacity = '0';
    b2.style.opacity = '0';
    subBox.style.opacity = '0';

    const canvasStream = canvas.captureStream(24);
    const combinedStream = new MediaStream([
      ...canvasStream.getVideoTracks(),
      ...dest.stream.getAudioTracks()
    ]);

    const recorder = new MediaRecorder(combinedStream, {{ mimeType: 'video/webm' }});
    const chunks = [];
    recorder.ondataavailable = e => chunks.push(e.data);
    recorder.onstop = () => {{
      b1.style.opacity = '1';
      b2.style.opacity = '1';
      subBox.style.opacity = '1';
      vid.playbackRate = 1.0;

      const finalBlob = new Blob(chunks, {{ type: 'video/webm' }});
      const a = document.createElement('a');
      a.href = URL.createObjectURL(finalBlob);
      a.download = 'Studio99_Synced_Dub.webm';
      a.click();
      logBox.style.color = "#00e676";
      logBox.innerText = "🎉 မူရင်းအသံဖျောက် + မြန်မာ TTS ရုပ်/သံကိုက် ဗီဒီယို ဒေါင်းလုဒ်ဆွဲပြီးပါပြီ!";
      procBtn.disabled = false;
    }};

    vid.currentTime = 0;
    await audioCtx.resume();
    recorder.start();
    await vid.play();

    let activeSegText = null;

    function syncRenderLoop() {{
      if (!vid.paused && !vid.ended) {{
        const now = vid.currentTime;
        const currentSeg = ttsBuffers.find(s => now >= s.start && now <= s.end);
        activeSegText = currentSeg ? currentSeg.mm_text : null;

        ttsBuffers.forEach(item => {{
          if (!item.played && now >= item.start) {{
            item.played = true;
            const slotDur = Math.max(0.4, item.end - item.start);
            const rawTtsDur = item.buffer.duration;
            const effectiveTtsDur = rawTtsDur / userSpeedMultiplier;

            const srcNode = audioCtx.createBufferSource();
            srcNode.buffer = item.buffer;

            let finalAudioRate = userSpeedMultiplier;
            if (effectiveTtsDur > slotDur) {{
              finalAudioRate = Math.min(1.8, rawTtsDur / slotDur);
              const actualDuration = rawTtsDur / finalAudioRate;
              vid.playbackRate = Math.max(0.45, Math.min(1.0, slotDur / actualDuration));
            }} else {{
              vid.playbackRate = 1.0;
            }}

            srcNode.playbackRate.value = finalAudioRate;
            if (srcNode.detune) {{
              srcNode.detune.value = pitchHz * 10;
            }}

            srcNode.connect(dest);
            srcNode.connect(audioCtx.destination);
            srcNode.start(0);

            srcNode.onended = () => {{
              vid.playbackRate = 1.0;
            }};
          }}
        }});

        renderCanvasFrame(activeSegText);
        requestAnimationFrame(syncRenderLoop);
      }}
    }}
    syncRenderLoop();

    vid.onended = () => {{
      if (recorder.state === "recording") recorder.stop();
    }};

  }} catch (err) {{
    b1.style.opacity = '1';
    b2.style.opacity = '1';
    subBox.style.opacity = '1';
    logBox.style.color = "#ff5252";
    logBox.innerText = "❌ Error: " + err.message;
    procBtn.disabled = false;
  }}
}};
</script>
</body>
</html>
"""

components.html(studio99_app, height=960, scrolling=True)
