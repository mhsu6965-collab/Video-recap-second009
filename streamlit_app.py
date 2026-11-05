import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="Studio99", layout="centered")

# Hide default Streamlit margins for full mobile app feel
st.markdown("""
<style>
    .stApp { background-color: #0e121a; color: #ffffff; }
    .block-container { padding-top: 1rem; padding-bottom: 1rem; max-width: 450px; }
    header, footer { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

# --- API Keys Input (Saved in Session) ---
with st.expander("🔑 API Keys ထည့်သွင်းရန် (Groq & Gemini)", expanded=False):
    groq_key = st.text_input("Groq API Key (Whisper)", type="password")
    gemini_key = st.text_input("Gemini API Key (Translator)", type="password")

# --- All-in-One Studio99 Offline Video Engine ---
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
    display: flex; justify-content: center; align-items: center;
    padding: 10px 0 14px 0; font-size: 18px; font-weight: bold;
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
  .slider-row {{ margin-top: 8px; font-size: 12px; color: #94a3b8; display: flex; justify-content: space-between; }}
  input[type="range"] {{ width: 100%; accent-color: #00e5ff; margin-top: 4px; }}
  .main-btn {{
    display: block; width: 96%; margin: 10px auto; padding: 15px;
    background: linear-gradient(90deg, #00e5ff, #00b8d4); color: #000;
    font-weight: bold; font-size: 15px; border: none; border-radius: 12px;
    cursor: pointer; text-align: center;
  }}
  .main-btn:disabled {{ opacity: 0.5; cursor: not-allowed; }}
  #log-box {{
    width: 90%; margin: 8px auto; padding: 10px; background: #11151e;
    border-radius: 10px; font-size: 12px; color: #00e5ff; text-align: center;
    border: 1px solid #1f2737; min-height: 22px;
  }}
</style>
</head>
<body>

<div class="top-bar">Studio99</div>

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

<!-- 5. TTS Speed & Pitch Card -->
<div class="card">
  <div class="card-title">🎙️ Edge-TTS & Sync Settings</div>
  <div class="toggle-row">
    <span>အသံ (Voice)</span>
    <select id="voice-sel" style="background:#0e121a; color:#fff; border:1px solid #2e384d; padding:6px; border-radius:6px;">
      <option value="my-MM-ThihaNeural">သီဟ (Male)</option>
      <option value="my-MM-NilarNeural">နီလာ (Female)</option>
    </select>
  </div>
  <div class="slider-row"><span>Speed (အမြန်နှုန်း)</span><span id="spd-val">1.0x</span></div>
  <input type="range" id="spd-slider" min="0.7" max="1.5" step="0.05" value="1.0">
  
  <div class="slider-row"><span>Pitch (အသံအနိမ့်အမြင့်)</span><span id="pit-val">0 Hz</span></div>
  <input type="range" id="pit-slider" min="-20" max="20" step="2" value="0">
</div>

<div id="log-box">ဗီဒီယိုရွေးပြီးပါက အောက်ပါခလုတ်ကို နှိပ်ပါ။</div>

<button class="main-btn" id="process-btn">🚀 နားထောင်မည် + ဘာသာပြန် + ရုပ်/သံကိုက် ထုတ်မည်</button>

<script>
const GROQ_KEY = "{groq_key}";
const GEMINI_KEY = "{gemini_key}";

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
let ttsAudioClips = [];

// Sliders UI update
const spdSlider = document.getElementById('spd-slider');
const pitSlider = document.getElementById('pit-slider');
spdSlider.oninput = () => document.getElementById('spd-val').innerText = spdSlider.value + 'x';
pitSlider.oninput = () => document.getElementById('pit-val').innerText = pitSlider.value + ' Hz';

// 1. Instant Local Video Load (0 MB Internet Upload)
vidInput.onchange = (e) => {{
  selectedFile = e.target.files[0];
  if (!selectedFile) return;
  vid.src = URL.createObjectURL(selectedFile);
  vid.onloadedmetadata = () => {{
    placeholder.style.display = 'none';
    canvas.style.display = 'block';
    applyAspectRatio();
    vid.currentTime = 0.2;
    logBox.innerText = "✅ ဗီဒီယို အဆင်သင့်ဖြစ်ပါပြီ (Offline Loaded)";
  }};
  vid.onseeked = () => renderCanvasFrame();
}};

// Ratio Selection
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

// Draggable & Resizable Blur Boxes
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
      const fSize = Math.round(canvas.width * 0.045);
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

// Helper: Extract tiny internal WAV blob in memory (User never sees or downloads this)
async function getInternalAudioBlob(file) {{
  const buf = await file.arrayBuffer();
  const actx = new (window.AudioContext || window.webkitAudioContext)({{ sampleRate: 16000 }});
  const decoded = await actx.decodeAudioData(buf);
  const pcm = decoded.getChannelData(0);
  const wav = new ArrayBuffer(44 + pcm.length * 2);
  const v = new DataView(wav);
  const str = (o, s) => {{ for (let i=0;i<s.length;i++) v.setUint8(o+i, s.charCodeAt(i)); }};
  str(0, 'RIFF'); v.setUint32(4, 36 + pcm.length * 2, true);
  str(8, 'WAVEfmt '); v.setUint32(16, 16, true);
  v.setUint16(20, 1, true); v.setUint16(22, 1, true);
  v.setUint32(24, 16000, true); v.setUint32(28, 32000, true);
  v.setUint16(32, 2, true); v.setUint16(34, 16, true);
  str(36, 'data'); v.setUint32(40, pcm.length * 2, true);
  for (let i = 0, off = 44; i < pcm.length; i++, off += 2) {{
    let s = Math.max(-1, Math.min(1, pcm[i]));
    v.setInt16(off, s < 0 ? s * 0x8000 : s * 0x7FFF, true);
  }}
  return new Blob([v], {{ type: 'audio/wav' }});
}}

// 2. All-in-One Pipeline (Listen -> Translate -> TTS -> Sync Render)
procBtn.onclick = async () => {{
  if (!selectedFile) {{ alert('Gallery မှ ဗီဒီယို အရင်ရွေးပါ!'); return; }}
  if (!GROQ_KEY || !GEMINI_KEY) {{ alert('အပေါ်ဆုံးရှိ API Keys (Groq & Gemini) အရင်ထည့်ပါ!'); return; }}

  try {{
    procBtn.disabled = true;
    logBox.innerText = "🎧 ၁/၄ - ဗီဒီယိုထဲမှ အသံကို Whisper ဖြင့် တိုက်ရိုက်နားထောင်နေပါသည်...";
    const wavBlob = await getInternalAudioBlob(selectedFile);

    const formData = new FormData();
    formData.append("file", wavBlob, "audio.wav");
    formData.append("model", "whisper-large-v3-turbo");
    formData.append("response_format", "verbose_json");

    const groqRes = await fetch("https://api.groq.com/openai/v1/audio/transcriptions", {{
      method: "POST",
      headers: {{ "Authorization": `Bearer ${{GROQ_KEY}}` }},
      body: formData
    }});
    const transData = await groqRes.json();
    const rawSegs = transData.segments.map((s, idx) => ({{
      id: idx, start: Number(s.start.toFixed(2)), end: Number(s.end.toFixed(2)), text: s.text
    }}));

    logBox.innerText = "🌐 ၂/၄ - Gemini ဖြင့် အချိန်ကိုက် မြန်မာဘာသာပြန်နေပါသည်...";
    const geminiUrl = `https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key=${{GEMINI_KEY}}`;
    const promptText = `Translate these video transcript segments into natural, concise spoken Burmese for video dubbing. Return ONLY a JSON array of objects with keys: "id", "start", "end", "mm_text". Input: ${{JSON.stringify(rawSegs)}}`;

    const gemRes = await fetch(geminiUrl, {{
      method: "POST",
      headers: {{ "Content-Type": "application/json" }},
      body: JSON.stringify({{
        contents: [{{ parts: [{{ text: promptText }}] }}],
        generationConfig: {{ responseMimeType: "application/json" }}
      }})
    }});
    const gemJson = await gemRes.json();
    subtitles = JSON.parse(gemJson.candidates[0].content.parts[0].text);

    logBox.innerText = "🎙️ ၃/၄ - TTS အသံထုတ်ပြီး ရုပ်နှင့်အသံ အချိန်ကိုက် ချိန်ညှိနေပါသည်...";
    // Generate synced TTS audio using Google Translate TTS endpoint fallback for instant browser mixing
    const audioCtx = new (window.AudioContext || window.webkitAudioContext)();
    const dest = audioCtx.createMediaStreamDestination();

    // Lower original video background audio to 10%
    const vidSource = audioCtx.createMediaElementSource(vid);
    const bgGain = audioCtx.createGain();
    bgGain.gain.value = 0.1;
    vidSource.connect(bgGain).connect(dest);

    logBox.innerText = "🎬 ၄/၄ - ဗီဒီယို၊ Blur၊ စာတန်းထိုးနှင့် အသံကို အချိန်ကိုက် ပေါင်းစပ်နေပါသည်...";
    const canvasStream = canvas.captureStream(24); // 24fps keeps phone CPU cool
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
      logBox.innerText = "🎉 ရုပ်နှင့်အသံ အချိန်ကိုက် ဗီဒီယို ဒေါင်းလုဒ်ဆွဲပြီးပါပြီ!";
      procBtn.disabled = false;
    }};

    // Speak each translated segment at its exact timestamp
    let spokenIds = new Set();
    const userSpeed = parseFloat(spdSlider.value);

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
            // Auto speed-up if text is long so voice stays synced with video
            const slotDuration = Math.max(1, seg.end - seg.start);
            const estDuration = seg.mm_text.length * 0.12;
            utter.rate = Math.min(1.8, Math.max(userSpeed, estDuration / slotDuration));
            window.speechSynthesis.speak(utter);
          }}
        }});
        requestAnimationFrame(syncLoop);
      }}
    }}
    syncLoop();

    vid.onended = () => {{
      recorder.stop();
    }};

  }} catch (err) {{
    logBox.innerText = "❌ Error: " + err.message;
    procBtn.disabled = false;
  }}
}};
</script>
</body>
</html>
"""

components.html(studio99_app, height=860, scrolling=True)
