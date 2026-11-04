import streamlit as st
import streamlit.components.v1 as components
import os
import json
import base64
import asyncio
import subprocess
import tempfile
import edge_tts
from groq import Groq
from google import genai

st.set_page_config(page_title="Studio99 - Local Engine", layout="centered")

st.markdown("""
<style>
    .stApp { background-color: #0e121a; color: #ffffff; }
    .stButton>button {
        width: 100%; background-color: #00e5ff; color: #000;
        font-weight: bold; border-radius: 10px; height: 46px; border: none;
    }
    .step-box {
        background: #171c26; border: 1px solid #262d3d;
        padding: 14px; border-radius: 12px; margin-bottom: 12px;
    }
</style>
""", unsafe_allow_html=True)

st.markdown("<h3 style='text-align: center; color: #fff; margin-bottom: 5px;'>Studio99 (Offline Video Engine)</h3>", unsafe_allow_html=True)

# --- 1. API Keys & TTS Settings ---
with st.expander("🔑 API Keys & TTS အသံချိန်ညှိရန်", expanded=False):
    groq_key = st.text_input("Groq API Key (Whisper)", type="password")
    gemini_key = st.text_input("Gemini API Key", type="password")
    voice_opt = st.selectbox("Voice", ["my-MM-ThihaNeural", "my-MM-NilarNeural"])
    col1, col2 = st.columns(2)
    with col1:
        speed = st.slider("Speed (%)", -30, 50, 10, step=5)
    with col2:
        pitch = st.slider("Pitch (Hz)", -30, 30, 0, step=5)

# --- Helper Functions (Server processes ONLY lightweight Audio & Text) ---
def get_duration(file_path):
    cmd = ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", file_path]
    res = subprocess.run(cmd, stdout=subprocess.PIPE, text=True)
    try:
        return float(res.stdout.strip())
    except:
        return 1.0

async def build_master_tts(segments, voice, rate_str, pitch_str, temp_dir):
    synced_files = []
    for i, seg in enumerate(segments):
        raw_tts = os.path.join(temp_dir, f"raw_{i}.mp3")
        sync_tts = os.path.join(temp_dir, f"sync_{i}.mp3")
        text = seg.get("mm_text", "").strip()
        if not text:
            continue
        comm = edge_tts.Communicate(text, voice, rate=rate_str, pitch=pitch_str)
        await comm.save(raw_tts)
        
        tts_dur = get_duration(raw_tts)
        slot_dur = max(0.5, seg["end"] - seg["start"])
        
        if tts_dur > slot_dur:
            factor = min(1.85, tts_dur / slot_dur)
            subprocess.run(["ffmpeg", "-y", "-i", raw_tts, "-filter:a", f"atempo={factor}", sync_tts], check=True)
            synced_files.append((sync_tts, seg["start"]))
        else:
            synced_files.append((raw_tts, seg["start"]))

    master_mp3 = os.path.join(temp_dir, "master_tts.mp3")
    if not synced_files:
        return None

    cmd = ["ffmpeg", "-y"]
    for f_path, _ in synced_files:
        cmd.extend(["-i", f_path])

    fc = []
    mix_inputs = ""
    for i, (_, st_sec) in enumerate(synced_files):
        d_ms = int(st_sec * 1000)
        fc.append(f"[{i}:a]adelay={d_ms}|{d_ms}[a{i}];")
        mix_inputs += f"[a{i}]"

    fc.append(f"{mix_inputs}amix=inputs={len(synced_files)}:dropout_transition=0:normalize=0[outa]")
    cmd.extend(["-filter_complex", "".join(fc), "-map", "[outa]", "-c:a", "libmp3lame", "-q:a", "4", master_mp3])
    subprocess.run(cmd, check=True)
    return master_mp3

# --- Step 1: Upload ONLY tiny extracted audio (or small file) for AI ---
st.markdown("""
<div class="step-box">
    <b>အဆင့် (၁) - အသံနားထောင်ရန်နှင့် ဘာသာပြန်ရန်</b><br>
    <span style="font-size:12px; color:#9ba3b0;">
        အောက်ပါ Studio99 Player မှ "🎵 အသံသီးသန့်ထုတ်မည် (1MB)" ဖြင့် ထုတ်ထားသော အသံဖိုင်လေးကို ဒီမှာထည့်ပြီး AI ဖြင့် ဘာသာပြန်ပါ။ (ဗီဒီယိုဖိုင်အကြီးကြီး တင်ရန်မလိုပါ)
    </span>
</div>
""", unsafe_allow_html=True)

audio_upload = st.file_uploader("🎵 ခွဲထုတ်ထားသော အသံဖိုင် (.wav / .mp3) ထည့်ပါ", type=["wav", "mp3", "m4a", "mp4"])

if "ai_payload" not in st.session_state:
    st.session_state.ai_payload = "null"

if st.button("🧠 1. Whisper နားထောင်မည် + Gemini ဘာသာပြန် + TTS ထုတ်မည်"):
    if not audio_upload or not groq_key or not gemini_key:
        st.error("ကျေးဇူးပြု၍ API Key များနှင့် အသံဖိုင် ထည့်သွင်းပါ။")
    else:
        with tempfile.TemporaryDirectory() as temp_dir:
            in_aud = os.path.join(temp_dir, "input_audio.mp3")
            raw_in = os.path.join(temp_dir, audio_upload.name)
            with open(raw_in, "wb") as f:
                f.write(audio_upload.read())
            
            subprocess.run(["ffmpeg", "-y", "-i", raw_in, "-vn", "-acodec", "libmp3lame", "-ac", "1", "-ar", "16000", "-b:a", "32k", in_aud], check=True)

            st.info("🎧 Whisper ဖြင့် နားထောင်နေပါသည်...")
            groq_client = Groq(api_key=groq_key)
            with open(in_aud, "rb") as af:
                trans = groq_client.audio.transcriptions.create(
                    file=("audio.mp3", af.read()),
                    model="whisper-large-v3-turbo",
                    response_format="verbose_json"
                )
            segments = [{"id": i, "start": s["start"], "end": s["end"], "text": s["text"]} for i, s in enumerate(trans.segments)]

            st.info("🌐 Gemini ဖြင့် မြန်မာဘာသာပြန်နေပါသည်...")
            gem_client = genai.Client(api_key=gemini_key)
            prompt = f"""
            Translate these video segments into concise, natural spoken Burmese for voiceover dubbing.
            Return ONLY a JSON array with keys: "id", "start", "end", "mm_text".
            Segments: {json.dumps(segments, ensure_ascii=False)}
            """
            resp = gem_client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
                config={"response_mime_type": "application/json"}
            )
            mm_segments = json.loads(resp.text)

            st.info("🎙️ Edge-TTS အသံထုတ်ပြီး အချိန်ကိုက် ချိတ်ဆက်နေပါသည်...")
            rate_str = f"{speed:+d}%"
            pitch_str = f"{pitch:+d}Hz"
            master_mp3 = asyncio.run(build_master_tts(mm_segments, voice_opt, rate_str, pitch_str, temp_dir))

            if master_mp3 and os.path.exists(master_mp3):
                with open(master_mp3, "rb") as mf:
                    b64_audio = base64.b64encode(mf.read()).decode("utf-8")
                st.session_state.ai_payload = json.dumps({
                    "subs": mm_segments,
                    "audio_b64": f"data:audio/mp3;base64,{b64_audio}"
                }, ensure_ascii=False)
                st.success("✅ AI အသံနှင့် မြန်မာစာတန်းထိုး အဆင်သင့်ဖြစ်ပါပြီ! အောက်ပါ Player တွင် Offline ပေါင်းစပ်နိုင်ပါပြီ။")

# --- Step 2: Offline Local Video Studio (Zero Video Upload, Low CPU Canvas Render) ---
local_studio_html = f"""
<!DOCTYPE html>
<html>
<head>
<style>
  body {{ margin: 0; background: #0e121a; color: #fff; font-family: sans-serif; user-select: none; }}
  .btn-gallery {{
    display: block; width: 94%; margin: 6px auto 12px auto; padding: 13px;
    background: #171c26; border: 1.5px solid #00e5ff; color: #fff;
    text-align: center; border-radius: 12px; font-weight: bold; cursor: pointer;
  }}
  #stage {{
    position: relative; width: 100%; max-width: 350px; height: 260px;
    margin: 0 auto; background: #1c222e; border-radius: 14px; overflow: hidden;
    border: 1px solid #2b3344; display: flex; align-items: center; justify-content: center;
  }}
  canvas {{ width: 100%; height: 100%; object-fit: contain; display: none; }}
  #empty-msg {{ color: #6c7585; text-align: center; font-size: 14px; }}
  .blur-box {{
    position: absolute; border-radius: 4px; touch-action: none;
    display: none; align-items: center; justify-content: center;
    font-size: 11px; font-weight: bold; background: rgba(255,255,255,0.12);
  }}
  #b1 {{ border: 2px dashed #00e5ff; color: #00e5ff; width: 70%; height: 15%; top: 76%; left: 15%; }}
  #b2 {{ border: 2px dashed #d500f9; color: #d500f9; width: 32%; height: 14%; top: 8%; left: 8%; }}
  .handle {{
    width: 16px; height: 16px; position: absolute; right: 0; bottom: 0;
    background: currentColor; border-top-left-radius: 4px;
  }}
  .card {{
    background: #171c26; border: 1px solid #262d3d; border-radius: 12px;
    padding: 12px; margin-top: 12px;
  }}
  .row {{ display: flex; justify-content: space-between; align-items: center; padding: 6px 0; }}
  .action-btn {{
    width: 100%; padding: 12px; margin-top: 8px; border-radius: 10px;
    border: none; font-weight: bold; cursor: pointer; font-size: 14px;
  }}
  .btn-extract {{ background: #263147; color: #00e5ff; border: 1px solid #00e5ff; }}
  .btn-render {{ background: #00e5ff; color: #000; }}
  #status {{ font-size: 12px; color: #00e5ff; text-align: center; margin-top: 8px; }}
</style>
</head>
<body>

<label class="btn-gallery">
  ▶️ Gallery မှ ရွေးမည် (Offline တန်းပေါ်မည်)
  <input type="file" id="vid-file" accept="video/*" style="display:none">
</label>

<div id="stage">
  <div id="empty-msg">▶️<br>Preview မြင်ရရန် ဗီဒီယိုရွေးပါ</div>
  <canvas id="render-canvas"></canvas>
  <div id="b1" class="blur-box">Blur 1<div class="handle" id="h1"></div></div>
  <div id="b2" class="blur-box">Blur 2<div class="handle" id="h2"></div></div>
</div>

<video id="hidden-vid" playsinline crossorigin="anonymous" style="display:none"></video>
<audio id="tts-audio" crossorigin="anonymous" style="display:none"></audio>

<div class="card">
  <div class="row">
    <span style="color:#00e5ff; font-weight:bold;">Blur 1 (လက်ဖြင့် ဖိဆွဲရွှေ့ပါ)</span>
    <input type="checkbox" id="chk1" style="transform:scale(1.4);">
  </div>
  <div class="row">
    <span style="color:#d500f9; font-weight:bold;">Blur 2 (လက်ဖြင့် ဖိဆွဲရွှေ့ပါ)</span>
    <input type="checkbox" id="chk2" style="transform:scale(1.4);">
  </div>
  <div class="row">
    <span style="color:#fff; font-weight:bold;">မြန်မာစာတန်းထိုး (Subtitles)</span>
    <input type="checkbox" id="chk-sub" checked style="transform:scale(1.4);">
  </div>
  <div class="row">
    <span style="font-size:12px; color:#9ba3b0;">Video Ratio</span>
    <select id="ratio-sel" style="background:#0e121a; color:#fff; border:1px solid #2b3344; padding:5px; border-radius:6px;">
      <option value="orig">Original</option>
      <option value="9:16">9:16 (TikTok/Reels)</option>
      <option value="16:9">16:9 (YouTube)</option>
      <option value="1:1">1:1</option>
    </select>
  </div>

  <button class="action-btn btn-extract" id="extract-btn">🎵 ၁။ အသံသီးသန့်ထုတ်မည် (AI ပို့ရန် ~1MB)</button>
  <button class="action-btn btn-render" id="render-btn">🎬 ၂။ Offline Video + TTS Render ဆွဲမည်</button>
  <div id="status">အဆင်သင့်ဖြစ်ပါပြီ။</div>
</div>

<script>
const aiData = {st.session_state.ai_payload};
const vidFile = document.getElementById('vid-file');
const vid = document.getElementById('hidden-vid');
const ttsAudio = document.getElementById('tts-audio');
const canvas = document.getElementById('render-canvas');
const ctx = canvas.getContext('2d');
const stage = document.getElementById('stage');
const emptyMsg = document.getElementById('empty-msg');
const b1 = document.getElementById('b1');
const b2 = document.getElementById('b2');
const chk1 = document.getElementById('chk1');
const chk2 = document.getElementById('chk2');
const chkSub = document.getElementById('chk-sub');
const ratioSel = document.getElementById('ratio-sel');
const statusEl = document.getElementById('status');

let currentFile = null;

if (aiData && aiData.audio_b64) {{
  ttsAudio.src = aiData.audio_b64;
  statusEl.innerText = "✅ AI ဘာသာပြန်နှင့် TTS အသံ အသင့်ရှိနေပါပြီ!";
}}

vidFile.onchange = (e) => {{
  currentFile = e.target.files[0];
  if (!currentFile) return;
  vid.src = URL.createObjectURL(currentFile);
  vid.onloadedmetadata = () => {{
    setupCanvasSize();
    emptyMsg.style.display = 'none';
    canvas.style.display = 'block';
    vid.currentTime = 0.1;
  }};
  vid.onseeked = () => drawFrame();
}};

function setupCanvasSize() {{
  const r = ratioSel.value;
  if (r === '9:16') {{ canvas.width = 540; canvas.height = 960; }}
  else if (r === '16:9') {{ canvas.width = 854; canvas.height = 480; }}
  else if (r === '1:1') {{ canvas.width = 640; canvas.height = 640; }}
  else {{
    const scale = Math.min(1, 720 / Math.max(vid.videoWidth, vid.videoHeight));
    canvas.width = Math.round(vid.videoWidth * scale);
    canvas.height = Math.round(vid.videoHeight * scale);
  }}
  drawFrame();
}}

ratioSel.onchange = setupCanvasSize;
chk1.onchange = () => {{ b1.style.display = chk1.checked ? 'flex' : 'none'; drawFrame(); }};
chk2.onchange = () => {{ b2.style.display = chk2.checked ? 'flex' : 'none'; drawFrame(); }};

function makeTouchDrag(el, handle) {{
  let sx, sy, sl, st, sw, sh, mode = null;
  el.onpointerdown = (e) => {{
    mode = (e.target === handle) ? 'resize' : 'drag';
    sx = e.clientX; sy = e.clientY;
    sl = el.offsetLeft; st = el.offsetTop;
    sw = el.offsetWidth; sh = el.offsetHeight;
    el.setPointerCapture(e.pointerId);
  }};
  el.onpointermove = (e) => {{
    if (!mode) return;
    const dx = e.clientX - sx, dy = e.clientY - sy;
    if (mode === 'drag') {{
      el.style.left = Math.max(0, Math.min(stage.clientWidth - el.offsetWidth, sl + dx)) / stage.clientWidth * 100 + '%';
      el.style.top = Math.max(0, Math.min(stage.clientHeight - el.offsetHeight, st + dy)) / stage.clientHeight * 100 + '%';
    }} else {{
      el.style.width = Math.max(25, Math.min(stage.clientWidth - sl, sw + dx)) / stage.clientWidth * 100 + '%';
      el.style.height = Math.max(20, Math.min(stage.clientHeight - st, sh + dy)) / stage.clientHeight * 100 + '%';
    }}
    drawFrame();
  }};
  el.onpointerup = (e) => {{ mode = null; el.releasePointerCapture(e.pointerId); }};
}}
makeTouchDrag(b1, document.getElementById('h1'));
makeTouchDrag(b2, document.getElementById('h2'));

function drawBlurZone(el) {{
  const rx = (parseFloat(el.style.left || 15) / 100) * canvas.width;
  const ry = (parseFloat(el.style.top || 76) / 100) * canvas.height;
  const rw = (parseFloat(el.style.width || 70) / 100) * canvas.width;
  const rh = (parseFloat(el.style.height || 15) / 100) * canvas.height;
  ctx.save();
  ctx.filter = 'blur(12px)';
  ctx.drawImage(canvas, rx, ry, rw, rh, rx, ry, rw, rh);
  ctx.restore();
}}

function drawFrame() {{
  if (!vid.videoWidth) return;
  ctx.fillStyle = '#000';
  ctx.fillRect(0, 0, canvas.width, canvas.height);

  // Draw Video Fit
  const vr = vid.videoWidth / vid.videoHeight;
  const cr = canvas.width / canvas.height;
  let dw = canvas.width, dh = canvas.height, dx = 0, dy = 0;
  if (vr > cr) {{ dh = canvas.width / vr; dy = (canvas.height - dh) / 2; }}
  else {{ dw = canvas.height * vr; dx = (canvas.width - dw) / 2; }}
  ctx.drawImage(vid, dx, dy, dw, dh);

  if (chk1.checked) drawBlurZone(b1);
  if (chk2.checked) drawBlurZone(b2);

  // Draw Synced Subtitle
  if (chkSub.checked && aiData && aiData.subs) {{
    const t = vid.currentTime;
    const active = aiData.subs.find(s => t >= s.start && t <= s.end);
    if (active && active.mm_text) {{
      ctx.font = 'bold ' + Math.round(canvas.width * 0.042) + 'px sans-serif';
      ctx.textAlign = 'center';
      ctx.lineWidth = 4;
      ctx.strokeStyle = '#000000';
      ctx.fillStyle = '#ffffff';
      const subY = canvas.height * 0.88;
      ctx.strokeText(active.mm_text, canvas.width / 2, subY);
      ctx.fillText(active.mm_text, canvas.width / 2, subY);
    }}
  }}
}}

// 1. Extract lightweight WAV audio locally in browser (No video upload!)
document.getElementById('extract-btn').onclick = async () => {{
  if (!currentFile) {{ alert('Gallery မှ ဗီဒီယို အရင်ရွေးပါ!'); return; }}
  statusEl.innerText = "⏳ ဖုန်းထဲတွင် အသံသီးသန့် ခွဲထုတ်နေပါသည်...";
  const arrayBuf = await currentFile.arrayBuffer();
  const audioCtx = new (window.AudioContext || window.webkitAudioContext)({{ sampleRate: 16000 }});
  const decoded = await audioCtx.decodeAudioData(arrayBuf);
  const chan = decoded.getChannelData(0);

  // Encode lightweight 16kHz Mono WAV
  const wavBuf = new ArrayBuffer(44 + chan.length * 2);
  const view = new DataView(wavBuf);
  const writeStr = (off, s) => {{ for (let i=0;i<s.length;i++) view.setUint8(off+i, s.charCodeAt(i)); }};
  writeStr(0, 'RIFF'); view.setUint32(4, 36 + chan.length * 2, true);
  writeStr(8, 'WAVEfmt '); view.setUint32(16, 16, true);
  view.setUint16(20, 1, true); view.setUint16(22, 1, true);
  view.setUint32(24, 16000, true); view.setUint32(28, 32000, true);
  view.setUint16(32, 2, true); view.setUint16(34, 16, true);
  writeStr(36, 'data'); view.setUint32(40, chan.length * 2, true);
  let offset = 44;
  for (let i = 0; i < chan.length; i++, offset += 2) {{
    let s = Math.max(-1, Math.min(1, chan[i]));
    view.setInt16(offset, s < 0 ? s * 0x8000 : s * 0x7FFF, true);
  }}
  const blob = new Blob([view], {{ type: 'audio/wav' }});
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = 'extracted_audio.wav';
  a.click();
  statusEl.innerText = "✅ extracted_audio.wav ဒေါင်းပြီးပါပြီ! အပေါ်ဆုံးအဆင့် (၁) တွင် ထည့်ပေးပါ။";
}};

// 2. Hardware-Accelerated Local Video + TTS Render (Gentle on Phone CPU, 24 FPS)
document.getElementById('render-btn').onclick = async () => {{
  if (!currentFile) {{ alert('Gallery မှ ဗီဒီယို အရင်ရွေးပါ!'); return; }}
  if (!aiData || !aiData.audio_b64) {{ alert('အဆင့် (၁) တွင် AI အသံ အရင်ထုတ်ပေးပါ!'); return; }}

  statusEl.innerText = "🎬 Offline Render ဆွဲနေပါသည် (ဖုန်း CPU သက်သာစေရန် 24fps ဖြင့် ဖမ်းယူနေသည်)...";
  const stream = canvas.captureStream(24); // 24 FPS keeps mobile CPU cool

  const audioCtx = new (window.AudioContext || window.webkitAudioContext)();
  const dest = audioCtx.createMediaStreamDestination();

  const vidSrc = audioCtx.createMediaElementSource(vid);
  const bgGain = audioCtx.createGain();
  bgGain.gain.value = 0.08; // Lower original video sound to 8%
  vidSrc.connect(bgGain).connect(dest);

  const ttsSrc = audioCtx.createMediaElementSource(ttsAudio);
  ttsSrc.connect(dest);
  ttsSrc.connect(audioCtx.destination); // Let user hear progress

  const combined = new MediaStream([...stream.getVideoTracks(), ...dest.stream.getAudioTracks()]);
  const recorder = new MediaRecorder(combined, {{ mimeType: 'video/webm' }});
  const chunks = [];
  recorder.ondataavailable = e => chunks.push(e.data);
  recorder.onstop = () => {{
    const outBlob = new Blob(chunks, {{ type: 'video/webm' }});
    const a = document.createElement('a');
    a.href = URL.createObjectURL(outBlob);
    a.download = 'studio99_synced_video.webm';
    a.click();
    statusEl.innerText = "🎉 Render ပြီးပါပြီ! ဖုန်းထဲသို့ ဒေါင်းလုဒ်ဆွဲပြီးပါပြီ။";
  }};

  vid.currentTime = 0;
  ttsAudio.currentTime = 0;
  recorder.start();
  vid.play();
  ttsAudio.play();

  function step() {{
    if (!vid.paused && !vid.ended) {{
      drawFrame();
      requestAnimationFrame(step);
    }}
  }}
  step();

  vid.onended = () => {{
    recorder.stop();
    ttsAudio.pause();
  }};
}};
</script>
</body>
</html>
"""

components.html(local_studio_html, height=620)
