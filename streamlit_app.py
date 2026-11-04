import streamlit as st
import streamlit.components.v1 as components
import os
import json
import asyncio
import subprocess
import tempfile
import edge_tts
from groq import Groq
from google import genai

st.set_page_config(page_title="Studio99 - Video Dub", layout="centered")

# --- Studio99 Dark UI Styling ---
st.markdown("""
<style>
    .stApp { background-color: #0e121a; color: #ffffff; }
    .card {
        background-color: #171c26;
        padding: 16px;
        border-radius: 14px;
        border: 1px solid #262d3d;
        margin-bottom: 15px;
    }
    .stButton>button {
        width: 100%;
        background-color: #00e5ff;
        color: #000000;
        font-weight: bold;
        border-radius: 10px;
        height: 48px;
        border: none;
    }
</style>
""", unsafe_allow_html=True)

st.markdown("<h3 style='text-align: center; color: #fff;'>Studio99</h3>", unsafe_allow_html=True)

# --- API Keys Setup ---
with st.expander("🔑 API Keys & Voice Settings"):
    groq_key = st.text_input("Groq API Key (Whisper)", type="password")
    gemini_key = st.text_input("Gemini API Key", type="password")
    
    col_v1, col_v2 = st.columns(2)
    with col_v1:
        voice_opt = st.selectbox("Voice", ["my-MM-ThihaNeural", "my-MM-NilarNeural"])
    with col_v2:
        enable_sub = st.checkbox("မြန်မာစာတန်းထိုး ထည့်မည်", value=True)
        
    speed = st.slider("TTS Speed (%)", -30, 50, 10, step=5)
    pitch = st.slider("TTS Pitch (Hz)", -30, 30, 0, step=5)

# --- 1. Upload Video from Gallery ---
uploaded_file = st.file_uploader("▶️ Gallery မှ ဗီဒီယို ရွေးမည်", type=["mp4", "mov", "mkv"])

# --- 2. Interactive Touch Preview & Draggable Blur Boxes ---
st.markdown("""
<div class="card">
    <p style="margin:0 0 8px 0; font-weight:bold; color:#00e5ff;">🖐️ Interactive Preview & Touch Blur</p>
    <p style="font-size:12px; color:#9ba3b0; margin-bottom:10px;">
        အောက်ပါ "📱 Preview အတွက် ဗီဒီယိုရွေးပါ" ကိုနှိပ်ပါက ဗီဒီယို ချက်ချင်းပေါ်လာပြီး Blur Box များကို လက်ဖြင့် ဖိဆွဲနိုင်ပါသည်။
    </p>
</div>
""", unsafe_allow_html=True)

touch_canvas_html = """
<!DOCTYPE html>
<html>
<head>
<style>
  body { margin: 0; background: #0e121a; color: #fff; font-family: sans-serif; user-select: none; }
  .upload-btn {
    display: block; width: 95%; margin: 0 auto 10px auto; padding: 12px;
    background: #171c26; border: 1.5px solid #00e5ff; color: #fff;
    text-align: center; border-radius: 10px; font-weight: bold; cursor: pointer;
  }
  #player-box {
    position: relative; width: 100%; max-width: 360px; height: 260px;
    margin: 0 auto; background: #1c222e; border-radius: 12px; overflow: hidden;
    display: flex; align-items: center; justify-content: center; border: 1px solid #2b3344;
  }
  video { width: 100%; height: 100%; object-fit: fill; display: none; }
  #placeholder { color: #6c7585; font-size: 14px; text-align: center; }
  .blur-rect {
    position: absolute; backdrop-filter: blur(8px);
    background: rgba(255,255,255,0.18); touch-action: none;
    display: none; align-items: center; justify-content: center;
    font-size: 12px; font-weight: bold; border-radius: 4px;
  }
  #b1 { border: 2px dashed #00e5ff; color: #00e5ff; width: 70%; height: 16%; top: 75%; left: 15%; }
  #b2 { border: 2px dashed #d500f9; color: #d500f9; width: 35%; height: 14%; top: 8%; left: 8%; }
  .resizer {
    width: 16px; height: 16px; position: absolute; right: 0; bottom: 0;
    background: currentColor; cursor: se-resize; border-top-left-radius: 4px;
  }
  .controls {
    background: #171c26; padding: 12px; border-radius: 12px; margin-top: 12px; border: 1px solid #262d3d;
  }
  .row { display: flex; justify-content: space-between; align-items: center; padding: 6px 0; }
  .coord-badge {
    margin-top: 8px; padding: 8px; background: #0b0e14; border-radius: 6px;
    font-family: monospace; font-size: 11px; color: #00e5ff; text-align: center;
  }
</style>
</head>
<body>

<label class="upload-btn">
  📱 Preview ချက်ချင်းကြည့်ရန် ဗီဒီယိုရွေးပါ
  <input type="file" id="instant-vid" accept="video/*" style="display:none">
</label>

<div id="player-box">
  <div id="placeholder">▶️<br>Preview မြင်ရရန် ဗီဒီယိုရွေးပါ</div>
  <video id="vid" controls playsinline></video>
  <div id="b1" class="blur-rect">Blur 1<div class="resizer" id="r1"></div></div>
  <div id="b2" class="blur-rect">Blur 2<div class="resizer" id="r2"></div></div>
</div>

<div class="controls">
  <div class="row">
    <span style="color:#00e5ff; font-weight:bold;">Blur 1 (စာတန်းဖျောက်ရန်)</span>
    <input type="checkbox" id="t1" style="transform: scale(1.4);">
  </div>
  <div class="row">
    <span style="color:#d500f9; font-weight:bold;">Blur 2 (Logo ဖျောက်ရန်)</span>
    <input type="checkbox" id="t2" style="transform: scale(1.4);">
  </div>
  <div class="coord-badge" id="coord-out">
    {"b1": {"on": false, "x": 15, "y": 75, "w": 70, "h": 16}, "b2": {"on": false, "x": 8, "y": 8, "w": 35, "h": 14}}
  </div>
</div>

<script>
const vidInput = document.getElementById('instant-vid');
const vid = document.getElementById('vid');
const holder = document.getElementById('placeholder');
const box = document.getElementById('player-box');
const b1 = document.getElementById('b1');
const b2 = document.getElementById('b2');
const t1 = document.getElementById('t1');
const t2 = document.getElementById('t2');
const out = document.getElementById('coord-out');

vidInput.onchange = (e) => {
  const file = e.target.files[0];
  if (file) {
    vid.src = URL.createObjectURL(file);
    vid.style.display = 'block';
    holder.style.display = 'none';
  }
};

t1.onchange = () => { b1.style.display = t1.checked ? 'flex' : 'none'; updateCoords(); };
t2.onchange = () => { b2.style.display = t2.checked ? 'flex' : 'none'; updateCoords(); };

function makeInteractive(el, resizer) {
  let startX, startY, startLeft, startTop, startW, startH, mode = null;

  el.addEventListener('pointerdown', (e) => {
    mode = (e.target === resizer) ? 'resize' : 'drag';
    startX = e.clientX; startY = e.clientY;
    startLeft = el.offsetLeft; startTop = el.offsetTop;
    startW = el.offsetWidth; startH = el.offsetHeight;
    el.setPointerCapture(e.pointerId);
  });

  el.addEventListener('pointermove', (e) => {
    if (!mode) return;
    const dx = e.clientX - startX;
    const dy = e.clientY - startY;
    if (mode === 'drag') {
      let newL = Math.max(0, Math.min(box.clientWidth - el.offsetWidth, startLeft + dx));
      let newT = Math.max(0, Math.min(box.clientHeight - el.offsetHeight, startTop + dy));
      el.style.left = (newL / box.clientWidth * 100) + '%';
      el.style.top = (newT / box.clientHeight * 100) + '%';
    } else if (mode === 'resize') {
      let newW = Math.max(30, Math.min(box.clientWidth - startLeft, startW + dx));
      let newH = Math.max(20, Math.min(box.clientHeight - startTop, startH + dy));
      el.style.width = (newW / box.clientWidth * 100) + '%';
      el.style.height = (newH / box.clientHeight * 100) + '%';
    }
    updateCoords();
  });

  el.addEventListener('pointerup', (e) => { mode = null; el.releasePointerCapture(e.pointerId); });
}

function getPct(el, on) {
  return {
    on: on,
    x: Math.round( parseFloat(el.style.left || 15) ),
    y: Math.round( parseFloat(el.style.top || 75) ),
    w: Math.round( parseFloat(el.style.width || 70) ),
    h: Math.round( parseFloat(el.style.height || 16) )
  };
}

function updateCoords() {
  const data = { b1: getPct(b1, t1.checked), b2: getPct(b2, t2.checked) };
  out.innerText = JSON.stringify(data);
}

makeInteractive(b1, document.getElementById('r1'));
makeInteractive(b2, document.getElementById('r2'));
</script>
</body>
</html>
"""

components.html(touch_canvas_html, height=470)

blur_json_str = st.text_input(
    "📌 အပေါ်တွင် လက်ဖြင့်ဆွဲထားသော Blur အချိုးအစား (ပြင်ရန်မလိုပါ၊ လိုအပ်ပါက Copy ကူးထည့်နိုင်သည်)",
    value='{"b1": {"on": true, "x": 15, "y": 75, "w": 70, "h": 16}, "b2": {"on": false, "x": 8, "y": 8, "w": 35, "h": 14}}'
)

# --- 3. Video Ratio Section ---
st.markdown('<div class="card"><b>📐 Video Ratio</b></div>', unsafe_allow_html=True)
ratio = st.radio("Select Ratio", ["Original", "9:16", "16:9", "1:1", "4:3"], horizontal=True)

# --- Helper Functions for Audio/Video Sync ---
def get_duration(file_path):
    cmd = ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", file_path]
    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    try:
        return float(res.stdout.strip())
    except:
        return 1.0

def get_video_dimensions(file_path):
    cmd = ["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height", "-of", "csv=s=x:p=0", file_path]
    res = subprocess.run(cmd, stdout=subprocess.PIPE, text=True)
    try:
        w, h = map(int, res.stdout.strip().split('x'))
        return w, h
    except:
        return 720, 1280

def format_srt_time(seconds):
    hrs = int(seconds // 3600)
    mins = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds - int(seconds)) * 1000)
    return f"{hrs:02d}:{mins:02d}:{secs:02d},{millis:03d}"

async def make_synced_tts(segments, voice, rate_str, pitch_str, temp_dir):
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
        
        # မြန်မာအသံက မူရင်းစကားပြောချိန်ထက် ရှည်နေပါက ရုပ်နဲ့အသံကိုက်အောင် အသံနှုန်းကို အလိုအလျောက် ညှိပေးခြင်း
        if tts_dur > slot_dur:
            speed_factor = min(1.85, tts_dur / slot_dur)
            subprocess.run(["ffmpeg", "-y", "-i", raw_tts, "-filter:a", f"atempo={speed_factor}", sync_tts], check=True)
            synced_files.append((sync_tts, seg["start"]))
        else:
            synced_files.append((raw_tts, seg["start"]))
            
    return synced_files

# --- 4. Main Processing Pipeline ---
if st.button("🚀 Start Auto Dubbing & Sync"):
    if not uploaded_file:
        st.warning("ကျေးဇူးပြု၍ အပေါ်ဆုံးရှိ 'Gallery မှ ဗီဒီယို ရွေးမည်' တွင် ဗီဒီယိုဖိုင် ထည့်ပေးပါ။")
        st.stop()
    if not groq_key or not gemini_key:
        st.error("API Keys များ ထည့်သွင်းပေးပါ။")
        st.stop()

    with tempfile.TemporaryDirectory() as temp_dir:
        in_vid = os.path.join(temp_dir, "input.mp4")
        in_aud = os.path.join(temp_dir, "audio.mp3")
        srt_file = os.path.join(temp_dir, "sub.srt")
        out_vid = os.path.join(temp_dir, "studio99_output.mp4")

        with open(in_vid, "wb") as f:
            f.write(uploaded_file.read())

        vid_w, vid_h = get_video_dimensions(in_vid)

        st.info("၁။ ဗီဒီယိုထဲမှ အသံကို Whisper ဖြင့် နားထောင်နေပါသည်...")
        subprocess.run(["ffmpeg", "-y", "-i", in_vid, "-vn", "-acodec", "libmp3lame", "-q:a", "5", in_aud], check=True)

        groq_client = Groq(api_key=groq_key)
        with open(in_aud, "rb") as af:
            trans = groq_client.audio.transcriptions.create(
                file=("audio.mp3", af.read()),
                model="whisper-large-v3-turbo",
                response_format="verbose_json"
            )
        
        segments = [{"id": i, "start": s["start"], "end": s["end"], "text": s["text"]} for i, s in enumerate(trans.segments)]

        st.info("၂။ Gemini ဖြင့် အချိန်ကိုက် မြန်မာဘာသာပြန်နေပါသည်...")
        gem_client = genai.Client(api_key=gemini_key)
        prompt = f"""
        Translate these video segments into concise, natural spoken Burmese for video dubbing.
        Keep each line brief so it fits the exact start and end time.
        Return ONLY valid JSON array with keys: "id", "start", "end", "mm_text".
        Segments: {json.dumps(segments, ensure_ascii=False)}
        """
        resp = gem_client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config={"response_mime_type": "application/json"}
        )
        mm_segments = json.loads(resp.text)

        with open(srt_file, "w", encoding="utf-8") as sf:
            for idx, seg in enumerate(mm_segments, 1):
                sf.write(f"{idx}\n{format_srt_time(seg['start'])} --> {format_srt_time(seg['end'])}\n{seg['mm_text']}\n\n")

        st.info("၃။ Edge-TTS အသံထုတ်ပြီး ရုပ်နှင့်အသံ အချိန်ကိုက်ညှိနေပါသည်...")
        rate_str = f"{speed:+d}%"
        pitch_str = f"{pitch:+d}Hz"
        tts_list = asyncio.run(make_synced_tts(mm_segments, voice_opt, rate_str, pitch_str, temp_dir))

        st.info("၄။ Blur၊ စာတန်းထိုး နှင့် အသံများကို ပေါင်းစပ်နေပါသည်...")
        v_filters = []
        blur_cfg = json.loads(blur_json_str)

        for key in ["b1", "b2"]:
            b = blur_cfg.get(key, {})
            if b.get("on"):
                bx = int((b["x"] / 100.0) * vid_w)
                by = int((b["y"] / 100.0) * vid_h)
                bw = int((b["w"] / 100.0) * vid_w)
                bh = int((b["h"] / 100.0) * vid_h)
                v_filters.append(f"delogo=x={bx}:y={by}:w={bw}:h={bh}:show=0")

        if enable_sub:
            esc_srt = srt_file.replace("\\", "/").replace(":", "\\:")
            v_filters.append(f"subtitles='{esc_srt}':force_style='FontName=Noto Sans Myanmar,FontSize=16,PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,BorderStyle=1,Outline=2'")

        vf_chain = ",".join(v_filters) if v_filters else "null"

        cmd = ["ffmpeg", "-y", "-i", in_vid]
        for f_path, _ in tts_list:
            cmd.extend(["-i", f_path])

        fc = ["[0:a]volume=0.08[bg];"]
        mix_str = "[bg]"
        for i, (_, st_sec) in enumerate(tts_list, 1):
            d_ms = int(st_sec * 1000)
            fc.append(f"[{i}:a]adelay={d_ms}|{d_ms}[a{i}];")
            mix_str += f"[a{i}]"

        fc.append(f"{mix_str}amix=inputs={len(tts_list)+1}:dropout_transition=0:normalize=0[outa]")

        cmd.extend([
            "-filter_complex", "".join(fc),
            "-vf", vf_chain,
            "-map", "0:v", "-map", "[outa]",
            "-c:v", "libx264", "-preset", "ultrafast", "-c:a", "aac",
            out_vid
        ])
        subprocess.run(cmd, check=True)

        st.success("✅ ရုပ်နှင့်အသံ အချိန်ကိုက် ဗီဒီယို ရရှိပါပြီ!")
        st.video(out_vid)
        with open(out_vid, "rb") as f:
            st.download_button("⬇️ Download Video", f, file_name="studio99_dubbed.mp4", mime="video/mp4")
