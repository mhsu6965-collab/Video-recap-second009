import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="Studio99", layout="centered")

# Hide default Streamlit margins for full mobile app feel
st.markdown("""
<style>
    .stApp { background-color: #0e121a; color: #ffffff; }
    .block-container { padding-top: 0.5rem; padding-bottom: 1rem; max-width: 450px; }
    header, footer { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

# Optional: Load keys from Streamlit Cloud Secrets if configured
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
    width: 95%; height: 55px; background: #0b0e14; color: #00e5ff;
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
  #preview-container {{
    position: relative; width: 96%; height: 280px; margin: 0 auto 14px auto;
    background: #1b222f; border-radius: 14px; border: 1px solid #2a3346;
    overflow: hidden; display: flex; align-items: center; justify-content: center;
  }}
  canvas {{ width: 100%; height: 100%; object-fit: contain; display: none; }}
  #placeholder {{ color: #687387; text-align: center; font-size: 14px; line-height: 1.8; }}
  .blur-overlay {{
    position: absolute; border-radius: 6px; touch-action: none;
    display: none; align-items: center; justify-content: center;
    font-size: 11px; font-weight: bold; backdrop-filter: blur(8px);
    background: rgba(255,255,255,0.12);
  }}
  #blur1 {{ border: 2px dashed #00e5ff; color: #00e5ff; width: 72%; height: 16%; top: 75%; left: 14%; }}
  #blur2 {{ border: 2px dashed #d500f9; color: #d500f9; width: 35%; height: 14%; top: 8%; left: 8%; }}
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

<!-- Persistent Multi-Key Drawer (Saved in Phone Browser localStorage) -->
<div id="key-drawer">
  <div style="font-size:12px; color:#94a3b8; margin-bottom:4px;">
    📌 <b>Gemini Keys (၂ ခု ၃ ခု ထည့်နိုင်သည်):</b> တစ်ကြောင်းလျှင် Key တစ်ခုနှုန်း (သို့) ကော်မာခံပြီး ထည့်ပါ။ တစ်ခါသိမ်းထားရုံဖြင့် အမြဲမှတ်ထားပါမည်။
  </div>
  <textarea id="gemini-keys-input" placeholder="AIzaSy...&#10;AIzaSy..."></textarea>

  <div style="font-size:12px; color:#94a3b8; margin-bottom:4px;">
    📌 <b>Groq Keys (၂ ခု ၃ ခု ထည့်နိုင်သည်):</b> မထည့်ထားလျှင်လည်း Gemini က တိုက်ရိုက်နားထောင်ပေးပါမည်။
  </div>
  <textarea id="groq-keys-input" placeholder="gsk_...&#10;gsk_..."></textarea>

  <button class="save-key-btn" id="save-keys-btn">💾 ဖုန်းထဲတွင် အသေသိမ်းမည် (Save Keys)</button>
</div>

<!-- 1. Instant Offline Gallery Picker -->
<label class="gallery-btn">
  <span>▶️ Gallery မှ ရွေးမည်</span>
  <input type="file" id="video-input" accept="video/*" style="display:none">
</label>

<!-- 2. Instant Video Preview + Draggable Blur Stage -->
<div id="preview-container">
  <div id="placeholder">▶️<br>Preview မြင်ရရန် ဗီဒီယိုရွေးပါ</div>
  <canvas id="stage-canvas"></canvas>
  <div id="blur1" class="blur-overlay">Blur 1<div class="resize-dot" id="dot1"></div></div>
  <div id="blur2" class="blur-overlay">Blur 2<div class="resize-dot" id="dot2"></div></div>
</div>

<video id="src-video" playsinline crossorigin="anonymous" style="display:none"></video>

<!-- 3. Blur Mask Card -->
<div class="card">
  <div class="card-title">⠿ Blur Mask (ဗီဒီယိုပေါ်တွင် လက်ဖြင့်ဆွဲရွှေ့ပါ)</div>
  <div class="toggle-row">
    <span style="color:#00e5ff; font-weight:bold;">Blur 1</span>
    <input type="checkbox" id="toggle-b1" style="transform:scale(1.4);">
  </div>
  <div class="toggle-row">
    <span style="color:#d500f9; font-weight:bold;">Blur 2</span>
    <input type="checkbox" id="toggle-b2" style="transform:scale(1.4);">
  </div>
  <div class="toggle-row">
    <span style="color:#fff; font-weight:bold;">မြန်မာစာတန်းထိုး (Subtitles)</span>
    <input type="checkbox" id="toggle-sub" checked style="transform:scale(1.4);">
  </div>
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

<!-- 5. TTS Speed (+100% / -100%) & Pitch Card -->
<div class="card">
  <div class="card-title">🎙️ Edge-TTS & Sync Settings</div>
  <div class="toggle-row">
    <span>အသံ (Voice)</span>
    <select id="voice-sel" style="background:#0e121a; color:#fff; border:1px solid #2e384d; padding:6px; border-radius:6px;">
      <option value="my-MM-ThihaNeural">သီဟ (Male)</option>
      <option value="my-MM-NilarNeural">နီလာ (Female)</option>
    </select>
  </div>
  <div class="slider-row"><span>Speed (အမြန်နှုန်း)</span><span id="spd-val">0%</span></div>
  <input type="range" id="spd-slider" min="-100" max="100" step="5" value="0">
  
  <div class="slider-row"><span>Pitch (အသံအနိမ့်အမြင့်)</span><span id="pit-val">0 Hz</span></div>
  <input type="range" id="pit-slider" min="-50" max="50" step="5" value="0">
</div>

<div id="log-box">ဗီဒီယိုရွေးပြီးပါက အောက်ပါခလုတ်ကို နှိပ်ပါ။</div>

<button class="main-btn" id="process-btn">🚀 နားထောင်မည် + ဘာသာပြန် + ရုပ်/သံကိုက် ထုတ်မည်</button>

<script>
const DEFAULT_GROQ = `{secret_groq}`;
const DEFAULT_GEMINI = `{secret_gemini}`;

const keyDrawer = document.getElementById('key-drawer');
const openKeyBtn = document.getElementById('open-key-btn');
const saveKeysBtn = document.getElementById('save-keys-btn');
const gemInput = document.getElementById('gemini-keys-input');
const groqInput = document.getElementById('groq-keys-input');

// Load saved keys from phone localStorage on startup
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
const container = document.getElementById('preview-container');
const placeholder = document.getElementById('placeholder');
const b1 = document.getElementById('blur1');
const b2 = document.getElementById('blur2');
const tB1 = document.getElementById('toggle-b1');
const tB2 = document.getElementById('toggle-b2');
const tSub = document.getElementById('toggle-sub');
const logBox = document.getElementById('log-box');
const procBtn = document.getElementById('process-btn');

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
    logBox.innerText = "✅ ဗီဒီယို အဆင်သင့်ဖြစ်ပါပြီ (Offline Loaded)";
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

function applyAspectRatio() {{
  if (currentRatio === '9:16') {{ canvas.width = 540; canvas.height = 960; }}
  else if (currentRatio === '16:9') {{ canvas.width = 854; canvas.height = 480; }}
  else if (currentRatio === '1:1') {{ canvas.width = 640; canvas.height = 640; }}
  else if (currentRatio === '4:3') {{ canvas.width = 640; canvas.height = 480; }}
  renderCanvasFrame();
}}

tB1.onchange = () => {{ b1.style.display = tB1.checked ? 'flex' : 'none'; renderCanvasFrame(); }};
tB2.onchange = () => {{ b2.style.display = tB2.checked ? 'flex' : 'none'; renderCanvasFrame(); }};

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
    if (mode === 'drag') {{
      box.style.left = Math.max(0, Math.min(container.clientWidth - box.offsetWidth, sl + dx)) / container.clientWidth * 100 + '%';
      box.style.top = Math.max(0, Math.min(container.clientHeight - box.offsetHeight, st + dy)) / container.clientHeight * 100 + '%';
    }} else {{
      box.style.width = Math.max(30, Math.min(container.clientWidth - sl, sw + dx)) / container.clientWidth * 100 + '%';
      box.style.height = Math.max(20, Math.min(container.clientHeight - st, sh + dy)) / container.clientHeight * 100 + '%';
    }}
    renderCanvasFrame();
  }};
  box.onpointerup = (e) => {{ mode = null; box.releasePointerCapture(e.pointerId); }};
}}
enableTouchDrag(b1, document.getElementById('dot1'));
enableTouchDrag(b2, document.getElementById('dot2'));

function applyBlurRect(el) {{
  const rx = (parseFloat(el.style.left || 14) / 100) * canvas.width;
  const ry = (parseFloat(el.style.top || 75) / 100) * canvas.height;
  const rw = (parseFloat(el.style.width || 72) / 100) * canvas.width;
  const rh = (parseFloat(el.style.height || 16) / 100) * canvas.height;
  ctx.save();
  ctx.filter = 'blur(14px)';
  ctx.drawImage(canvas, rx, ry, rw, rh, rx, ry, rw, rh);
  ctx.restore();
}}

function renderCanvasFrame() {{
  if (!vid.videoWidth) return;
  ctx.fillStyle = '#0b0e14';
  ctx.fillRect(0, 0, canvas.width, canvas.height);

  const vr = vid.videoWidth / vid.videoHeight;
  const cr = canvas.width / canvas.height;
  let dw = canvas.width, dh = canvas.height, dx = 0, dy = 0;
  if (vr > cr) {{ dh = canvas.width / vr; dy = (canvas.height - dh) / 2; }}
  else {{ dw = canvas.height * vr; dx = (canvas.width - dw) / 2; }}
  ctx.drawImage(vid, dx, dy, dw, dh);

  if (tB1.checked) applyBlurRect(b1);
  if (tB2.checked) applyBlurRect(b2);

  if (tSub.checked && subtitles.length > 0) {{
    const cur = vid.currentTime;
    const line = subtitles.find(s => cur >= s.start && cur <= s.end);
    if (line && line.mm_text) {{
      const fSize = Math.round(canvas.width * 0.044);
      ctx.font = `bold ${{fSize}}px "Noto Sans Myanmar", sans-serif`;
      ctx.textAlign = 'center';
      ctx.lineWidth = 5;
      ctx.strokeStyle = '#000000';
      ctx.fillStyle = '#ffffff';
      const yPos = canvas.height * 0.86;
      ctx.strokeText(line.mm_text, canvas.width / 2, yPos);
      ctx.fillText(line.mm_text, canvas.width / 2, yPos);
    }}
  }}
}}

const sleep = (ms) => new Promise(res => setTimeout(res, ms));

// Safe JSON Extractor (Prevents 'Unexpected token <' HTML comment errors!)
function extractSafeJsonArray(rawText) {{
  if (!rawText) throw new Error("Empty response from AI");
  const startIdx = rawText.indexOf('[');
  const endIdx = rawText.lastIndexOf(']');
  if (startIdx === -1 || endIdx === -1 || endIdx <= startIdx) {{
    throw new Error("Invalid JSON structure returned");
  }}
  const cleanJson = rawText.substring(startIdx, endIdx + 1);
  return JSON.parse(cleanJson);
}}

// Extract internal 8kHz mono WAV blob (Compact & Fast for both Groq and Gemini Audio)
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

// Gemini Models Rotation List (Prioritizing 3.5 & 3.8 as requested, plus active fallbacks)
const GEMINI_MODELS = [
  "gemini-3.5-flash",
  "gemini-3.8-flash",
  "gemini-2.5-flash",
  "gemini-2.0-flash",
  "gemini-1.5-flash"
];

// Step 1A: Try Groq Whisper across all Groq Keys
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
      if (!res.ok || textResp.trim().startsWith("<")) {{
        throw new Error("Groq Key #" + (kIdx + 1) + " failed");
      }}
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
  return null; // Fallback to Gemini Audio Listen!
}}

// Step 1B + Step 2: Gemini Audio Listen Fallback OR Text Translation with Wait & Retry
async function runGeminiWithRetry(partsPayload, geminiKeys, taskLabel) {{
  let lastError = "Gemini Keys သို့မဟုတ် Models အားလုံး ခေတ္တပြည့်နေပါသည်။";

  for (let attempt = 1; attempt <= 2; attempt++) {{
    for (let kIdx = 0; kIdx < geminiKeys.length; kIdx++) {{
      const apiKey = geminiKeys[kIdx];
      for (const modelName of GEMINI_MODELS) {{
        try {{
          logBox.innerText = `🌐 ${{taskLabel}} (Model: ${{modelName}} | Key #${{kIdx + 1}})...`;
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
          // Guard against HTML error pages starting with '<'
          if (rawBody.trim().startsWith("<")) {{
            throw new Error("HTML response received instead of JSON");
          }}

          const data = JSON.parse(rawBody);
          if (res.status === 429) {{
            logBox.innerText = `⏳ Rate Limit ပြည့်နေသဖြင့် 4 စက္ကန့် စောင့်ပေးနေပါသည် (${{modelName}})...`;
            await sleep(4000);
            continue;
          }}

          if (data.candidates && data.candidates[0] && data.candidates[0].content && data.candidates[0].content.parts[0]) {{
            const aiText = data.candidates[0].content.parts[0].text;
            return extractSafeJsonArray(aiText);
          }} else if (data.error && data.error.message) {{
            lastError = data.error.message;
          }}
        }} catch (err) {{
          lastError = err.message;
        }}
      }}
    }}
    logBox.innerText = `⏳ ဘာသာပြန်ခြင်း ခေတ္တစောင့်ဆိုင်းပြီး ပြန်ကြိုးစားနေပါသည် (Attempt ${{attempt + 1}})...`;
    await sleep(4500);
  }}
  throw new Error(lastError);
}}

// Main Pipeline Execution
procBtn.onclick = async () => {{
  if (!selectedFile) {{ alert('Gallery မှ ဗီဒီယို အရင်ရွေးပါ!'); return; }}

  const geminiKeys = parseKeyList(gemInput.value);
  const groqKeys = parseKeyList(groqInput.value);

  if (geminiKeys.length === 0) {{
    keyDrawer.style.display = 'block';
    alert('ညာဘက်အပေါ်ထောင့်ရှိ 🔑 API Keys တွင် Gemini API Key အနည်းဆုံး (၁) ခု ထည့်ပြီး သိမ်းပေးပါ!');
    return;
  }}

  try {{
    procBtn.disabled = true;
    logBox.style.color = "#00e5ff";
    logBox.innerText = "🎧 ၁/၃ - ဗီဒီယိုထဲမှ အသံကို ဆွဲထုတ်နေပါသည်...";
    const wavBlob = await getInternalAudioBlob(selectedFile);

    let rawSegs = null;
    if (groqKeys.length > 0) {{
      rawSegs = await tryGroqTranscribe(wavBlob, groqKeys);
    }}

    if (rawSegs && rawSegs.length > 0) {{
      // Groq succeeded -> Now translate with Gemini
      const promptText = `Translate these video transcript segments into natural, concise spoken Burmese for video dubbing. Return ONLY a JSON array of objects with keys: "id", "start", "end", "mm_text". Input: ${{JSON.stringify(rawSegs)}}`;
      subtitles = await runGeminiWithRetry([{{ text: promptText }}], geminiKeys, "၂/၃ - မြန်မာဘာသာပြန်နေသည်");
    }} else {{
      // Groq failed or no Groq key -> Gemini listens to audio AND translates directly!
      logBox.innerText = "🎧 Groq မရသဖြင့် Gemini ဖြင့် တိုက်ရိုက် အသံနားထောင်ပြီး ဘာသာပြန်နေပါသည်...";
      const b64Audio = await blobToBase64(wavBlob);
      const audioPrompt = `Listen carefully to this audio and transcribe + translate the spoken sentences directly into natural, concise spoken Burmese for video dubbing with accurate timestamps in seconds. Return ONLY a valid JSON array of objects with keys: "id" (number), "start" (number in seconds), "end" (number in seconds), "mm_text" (Burmese string).`;
      subtitles = await runGeminiWithRetry([
        {{ inlineData: {{ mimeType: "audio/wav", data: b64Audio }} }},
        {{ text: audioPrompt }}
      ], geminiKeys, "၂/၃ - Gemini ဖြင့် နားထောင်+ဘာသာပြန်နေသည်");
    }}

    logBox.innerText = "🎬 ၃/၃ - ဗီဒီယို၊ Blur၊ စာတန်းထိုးနှင့် အသံကို အချိန်ကိုက် ပေါင်းစပ်နေပါသည်...";
    const audioCtx = new (window.AudioContext || window.webkitAudioContext)();
    const dest = audioCtx.createMediaStreamDestination();

    if (!vid.audioConnected) {{
      const vidSource = audioCtx.createMediaElementSource(vid);
      const bgGain = audioCtx.createGain();
      bgGain.gain.value = 0.1;
      vidSource.connect(bgGain).connect(dest);
      vid.audioConnected = true;
    }}

    const canvasStream = canvas.captureStream(24);
    const finalStream = new MediaStream([
      ...canvasStream.getVideoTracks(),
      ...dest.stream.getAudioTracks()
    ]);

    const recorder = new MediaRecorder(finalStream, {{ mimeType: 'video/webm' }});
    const chunks = [];
    recorder.ondataavailable = e => chunks.push(e.data);
    recorder.onstop = () => {{
      const finalBlob = new Blob(chunks, {{ type: 'video/webm' }});
      const a = document.createElement('a');
      a.href = URL.createObjectURL(finalBlob);
      a.download = 'Studio99_Dubbed_Video.webm';
      a.click();
      logBox.style.color = "#00e676";
      logBox.innerText = "🎉 ရုပ်နှင့်အသံ အချိန်ကိုက် ဗီဒီယို ဒေါင်းလုဒ်ဆွဲပြီးပါပြီ!";
      procBtn.disabled = false;
    }};

    let spokenIds = new Set();
    const speedPct = parseInt(spdSlider.value, 10);
    const baseRate = Math.max(0.25, 1.0 + (speedPct / 100.0));
    const pitchHz = parseInt(pitSlider.value, 10);
    const basePitch = Math.max(0.5, Math.min(2.0, 1.0 + (pitchHz / 100.0)));

    vid.currentTime = 0;
    recorder.start();
    vid.play();

    function syncLoop() {{
      if (!vid.paused && !vid.ended) {{
        renderCanvasFrame();
        const now = vid.currentTime;
        subtitles.forEach(seg => {{
          if (now >= seg.start && now <= seg.end && !spokenIds.has(seg.id)) {{
            spokenIds.add(seg.id);
            const utter = new SpeechSynthesisUtterance(seg.mm_text);
            utter.lang = 'my-MM';
            utter.pitch = basePitch;
            const slotDuration = Math.max(1, seg.end - seg.start);
            const estDuration = seg.mm_text.length * 0.11;
            utter.rate = Math.min(2.0, Math.max(baseRate, estDuration / slotDuration));
            window.speechSynthesis.speak(utter);
          }}
        }});
        requestAnimationFrame(syncLoop);
      }}
    }}
    syncLoop();

    vid.onended = () => {{
      if (recorder.state === "recording") recorder.stop();
    }};

  }} catch (err) {{
    logBox.style.color = "#ff5252";
    logBox.innerText = "❌ Error: " + err.message;
    procBtn.disabled = false;
  }}
}};
</script>
</body>
</html>
"""

components.html(studio99_app, height=900, scrolling=True)
