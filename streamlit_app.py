import streamlit as st
import os
import json
import asyncio
import subprocess
import tempfile
import edge_tts
from groq import Groq
from google import genai

st.set_page_config(page_title="Myanmar Video Dub & Sync", layout="wide")
st.title("🎬 Auto Video Dubbing & Sync (Myanmar)")

# --- Sidebar: API Keys & TTS Settings ---
with st.sidebar:
    st.header("🔑 API Keys")
    groq_key = st.text_input("Groq API Key (Whisper)", type="password")
    gemini_key = st.text_input("Gemini API Key", type="password")
    
    st.header("🎙️ Edge-TTS Settings")
    voice_option = st.selectbox(
        "အသံရွေးချယ်ရန်",
        ["my-MM-ThihaNeural (Male)", "my-MM-NilarNeural (Female)"]
    )
    voice = voice_option.split(" ")[0]
    speed = st.slider("Speed (အမြန်နှုန်း %)", -50, 100, 10, step=5)
    pitch = st.slider("Pitch (အသံအနိမ့်အမြင့် Hz)", -50, 50, 0, step=5)

    st.header("📝 Subtitle Settings")
    enable_sub = st.checkbox("မြန်မာစာတန်းထိုး ထည့်မည်", value=True)
    sub_size = st.slider("စာလုံးအရွယ်အစား", 10, 36, 18)

# --- Blur Settings ---
st.subheader("🔲 Blur Box Settings (မူရင်းစာတန်း သို့မဟုတ် Logo ဖျောက်ရန်)")
col1, col2 = st.columns(2)

with col1:
    blur1_on = st.checkbox("Enable Blur Box 1 (ဥပမာ - အောက်ခြေစာတန်း)", value=True)
    if blur1_on:
        b1_x = st.number_input("Box 1: X (ဘယ်မှညာ)", value=50, min_value=0)
        b1_y = st.number_input("Box 1: Y (အပေါ်မှအောက်)", value=550, min_value=0)
        b1_w = st.number_input("Box 1: Width (အကျယ်)", value=600, min_value=10)
        b1_h = st.number_input("Box 1: Height (အမြင့်)", value=100, min_value=10)

with col2:
    blur2_on = st.checkbox("Enable Blur Box 2 (ဥပမာ - အပေါ်ထောင့် Logo)", value=False)
    if blur2_on:
        b2_x = st.number_input("Box 2: X (ဘယ်မှညာ)", value=20, min_value=0)
        b2_y = st.number_input("Box 2: Y (အပေါ်မှအောက်)", value=20, min_value=0)
        b2_w = st.number_input("Box 2: Width (အကျယ်)", value=150, min_value=10)
        b2_h = st.number_input("Box 2: Height (အမြင့်)", value=60, min_value=10)

# --- Helper Functions ---
def format_srt_time(seconds):
    hrs = int(seconds // 3600)
    mins = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds - int(seconds)) * 1000)
    return f"{hrs:02d}:{mins:02d}:{secs:02d},{millis:03d}"

async def generate_tts_segments(segments, voice, rate_str, pitch_str, temp_dir):
    audio_files = []
    for i, seg in enumerate(segments):
        out_file = os.path.join(temp_dir, f"tts_{i}.mp3")
        text = seg.get("mm_text", "").strip()
        if text:
            communicate = edge_tts.Communicate(text, voice, rate=rate_str, pitch=pitch_str)
            await communicate.save(out_file)
            audio_files.append((out_file, seg["start"]))
    return audio_files

# --- Video Upload & Processing ---
uploaded_file = st.file_uploader("📱 Gallery မှ ဗီဒီယိုဖိုင် ရွေးပါ", type=["mp4", "mov", "mkv"])

if uploaded_file:
    st.video(uploaded_file)
    
    if st.button("🚀 Start Dubbing & Sync Process"):
        if not groq_key or not gemini_key:
            st.error("ကျေးဇူးပြု၍ Sidebar တွင် Groq နှင့် Gemini API Key များ ထည့်သွင်းပါ။")
            st.stop()

        with tempfile.TemporaryDirectory() as temp_dir:
            input_video = os.path.join(temp_dir, "input.mp4")
            extracted_audio = os.path.join(temp_dir, "audio.mp3")
            srt_path = os.path.join(temp_dir, "subs.srt")
            output_video = os.path.join(temp_dir, "final_output.mp4")

            with open(input_video, "wb") as f:
                f.write(uploaded_file.read())

            # Step 1: Extract Audio for Whisper
            st.info("၁။ ဗီဒီယိုမှ အသံကို ခွဲထုတ်နေပါသည်...")
            subprocess.run(["ffmpeg", "-y", "-i", input_video, "-vn", "-acodec", "libmp3lame", "-q:a", "4", extracted_audio], check=True)

            # Step 2: Whisper Transcription (Groq)
            st.info("၂။ Whisper ဖြင့် အသံနားထောင်ပြီး အချိန်မှတ်တမ်း (Timestamps) ယူနေပါသည်...")
            groq_client = Groq(api_key=groq_key)
            with open(extracted_audio, "rb") as audio_file:
                transcription = groq_client.audio.transcriptions.create(
                    file=("audio.mp3", audio_file.read()),
                    model="whisper-large-v3-turbo",
                    response_format="verbose_json"
                )
            
            raw_segments = [
                {"id": i, "start": s["start"], "end": s["end"], "text": s["text"]}
                for i, s in enumerate(transcription.segments)
            ]

            # Step 3: Gemini Translation
            st.info("၃။ Gemini ဖြင့် မြန်မာဘာသာသို့ သဘာဝကျကျ ပြန်ဆိုနေပါသည်...")
            gemini_client = genai.Client(api_key=gemini_key)
            prompt = f"""
            Translate the following video transcript segments into natural spoken Burmese suitable for voiceover dubbing.
            Keep the translation concise so it matches the original speaking duration.
            Return ONLY a valid JSON array of objects with keys: "id", "start", "end", and "mm_text".
            
            Input JSON:
            {json.dumps(raw_segments, ensure_ascii=False)}
            """
            
            response = gemini_client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
                config={"response_mime_type": "application/json"}
            )
            translated_segments = json.loads(response.text)

            # Step 4: Generate SRT File
            with open(srt_path, "w", encoding="utf-8") as srt_file:
                for idx, seg in enumerate(translated_segments, 1):
                    start_t = format_srt_time(seg["start"])
                    end_t = format_srt_time(seg["end"])
                    srt_file.write(f"{idx}\n{start_t} --> {end_t}\n{seg['mm_text']}\n\n")

            # Step 5: Generate Edge-TTS Audio per Segment
            st.info("၄။ Edge-TTS ဖြင့် မြန်မာအသံဖိုင်များ ထုတ်လုပ်နေပါသည်...")
            rate_str = f"{speed:+d}%"
            pitch_str = f"{pitch:+d}Hz"
            tts_files = asyncio.run(generate_tts_segments(translated_segments, voice, rate_str, pitch_str, temp_dir))

            # Step 6: FFmpeg Combine (Blur + Subtitle + Audio Sync)
            st.info("၅။ ဗီဒီယို၊ Blur Box၊ စာတန်းထိုး နှင့် အသံများကို အချိန်ကိုက် ပေါင်းစပ်နေပါသည်...")
            
            v_filters = []
            if blur1_on:
                v_filters.append(f"delogo=x={b1_x}:y={b1_y}:w={b1_w}:h={b1_h}:show=0")
            if blur2_on:
                v_filters.append(f"delogo=x={b2_x}:y={b2_y}:w={b2_w}:h={b2_h}:show=0")
            if enable_sub:
                # Escape path for FFmpeg filter
                escaped_srt = srt_path.replace("\\", "/").replace(":", "\\:")
                v_filters.append(f"subtitles='{escaped_srt}':force_style='FontName=Noto Sans Myanmar,FontSize={sub_size},PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,BorderStyle=1,Outline=2'")

            vf_string = ",".join(v_filters) if v_filters else "null"

            # Build Complex Audio Filter to Sync TTS segments
            ffmpeg_cmd = ["ffmpeg", "-y", "-i", input_video]
            for f_path, _ in tts_files:
                ffmpeg_cmd.extend(["-i", f_path])

            filter_complex = []
            # Lower original video volume slightly or mute it (0.1 = 10% background sound)
            filter_complex.append("[0:a]volume=0.08[bg_audio];")
            
            mix_inputs = "[bg_audio]"
            for i, (_, start_sec) in enumerate(tts_files, start=1):
                delay_ms = int(start_sec * 1000)
                filter_complex.append(f"[{i}:a]adelay={delay_ms}|{delay_ms}[a{i}];")
                mix_inputs += f"[a{i}]"

            total_audio_streams = len(tts_files) + 1
            filter_complex.append(f"{mix_inputs}amix=inputs={total_audio_streams}:dropout_transition=0:normalize=0[outa]")

            ffmpeg_cmd.extend([
                "-filter_complex", "".join(filter_complex),
                "-vf", vf_string,
                "-map", "0:v",
                "-map", "[outa]",
                "-c:v", "libx264",
                "-preset", "ultrafast",
                "-c:a", "aac",
                output_video
            ])

            subprocess.run(ffmpeg_cmd, check=True)

            st.success("✅ ဗီဒီယို ထုတ်လုပ်မှု အောင်မြင်ပါသည်။")
            st.video(output_video)

            with open(output_video, "rb") as final_f:
                st.download_button(
                    label="⬇️ Download Dubbed Video",
                    data=final_f,
                    file_name="myanmar_dubbed_video.mp4",
                    mime="video/mp4"
                )
