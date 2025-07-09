import os, subprocess, whisper, traceback
from moviepy.editor import VideoFileClip, AudioFileClip, TextClip, CompositeVideoClip
from moviepy.video.fx.all import loop

# === CONFIGURATION ===
SONGS_DIR = 'songs'
OUTPUT_DIR = 'output'
BACKGROUND_VIDEO = 'blank_bg.mp4'
MODEL = whisper.load_model("base")

# === TRANSCRIBE WITH FALLBACK ===
def transcribe_with_timestamps(audio_path):
    result = MODEL.transcribe(audio_path, word_timestamps=True)
    segments = result["segments"]
    segments.sort(key=lambda s: s["end"] - s["start"], reverse=True)
    text = result["text"].strip()
    return segments[0]['start'], segments[0]['end'], text

# === VIDEO SEGMENT CREATION ===
def make_video_segment(audio_path, start, end, text, out_path):
    duration = end - start
    tmp_audio = out_path.replace('.mp4', '.wav')

    subprocess.run([
        'ffmpeg', '-y', '-i', audio_path,
        '-ss', str(start), '-t', str(duration),
        tmp_audio
    ], check=True)

    clip = VideoFileClip(BACKGROUND_VIDEO)
    if clip.duration < duration:
        clip = loop(clip, duration=duration)
    else:
        clip = clip.subclip(0, duration)
    audio = AudioFileClip(tmp_audio)

    display_text = text[:200] + ('…' if len(text) > 200 else '')
    try:
        txt = TextClip(display_text, fontsize=40, method='caption', color='white',
                       size=(int(clip.w * 0.8), None))
    except Exception as e:
        print(f"⚠️ Text overlay failed (ImageMagick issue?), using no text. Error: {e}")
        txt = None

    if txt:
        txt = txt.set_position(('center', 'bottom')).set_duration(duration).fadein(0.5).fadeout(0.5)
        video = CompositeVideoClip([clip, txt]).set_audio(audio)
    else:
        video = clip.set_audio(audio)

    video.write_videofile(out_path, fps=24, codec='libx264', audio_codec='aac')

    if os.path.exists(tmp_audio):
        os.remove(tmp_audio)

# === MAIN PROCESS ===
def process_song(fname):
    if not fname.lower().endswith(('.mp3', '.wav')):
        return
    original_path = os.path.join(SONGS_DIR, fname)
    out_mp4 = os.path.join(OUTPUT_DIR, fname.rsplit('.', 1)[0] + '_clip.mp4')

    try:
        print(f"🎶 Processing {fname}...")
        try:
            start, end, full_text = transcribe_with_timestamps(original_path)
        except Exception as e:
            print(f"⚠️ Transcription failed ({fname}): {e}\n🔄 Retrying with 16kHz mono WAV...")
            tmp_wav = out_mp4.replace('_clip.mp4', '_fallback.wav')
            subprocess.run([
                'ffmpeg', '-y', '-i', original_path, '-ar', '16000', '-ac', '1', tmp_wav
            ], check=True)
            start, end, full_text = transcribe_with_timestamps(tmp_wav)
            os.remove(tmp_wav)

        make_video_segment(original_path, start, end, full_text, out_mp4)
        print(f"✅ Video rendered: {out_mp4}")

    except Exception as final_error:
        print(f"❌ Completely failed to process {fname}: {final_error}")
        traceback.print_exc()

def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    for fname in os.listdir(SONGS_DIR):
        process_song(fname)

if __name__ == "__main__":
    main()
