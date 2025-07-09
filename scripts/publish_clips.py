import os, subprocess, whisper, yaml, traceback, time, threading
from moviepy.editor import VideoFileClip, AudioFileClip, TextClip, CompositeVideoClip
import moviepy.video.fx as vfx

# === CONFIGURATION ===
SONGS_DIR = 'songs'
OUTPUT_DIR = 'output'
BACKGROUND_VIDEO = 'blank_bg.mp4'
MODEL = whisper.load_model("base")

# === CORE FUNCTIONS ===

def transcribe_with_timestamps(audio_path):
    result = MODEL.transcribe(audio_path, word_timestamps=True)
    segments = result["segments"]
    segments.sort(key=lambda s: s["end"] - s["start"], reverse=True)
    return segments[0]['start'], segments[0]['end'], result["text"]

def make_video_segment(audio_path, start, end, text, out_path):
    duration = end - start
    tmp_audio = out_path.replace('.mp4', '.wav')

    subprocess.run([
        'ffmpeg', '-y', '-i', audio_path,
        '-ss', str(start), '-t', str(duration),
        tmp_audio
    ], check=True)

    # Background loop
    clip = VideoFileClip(BACKGROUND_VIDEO)
    if clip.duration < duration:
        clip = vfx.loop(clip, duration=duration)
    clip = clip.subclip(0, duration)
    audio = AudioFileClip(tmp_audio)

    # Truncate text for legibility
    display_text = text[:200] + ('…' if len(text) > 200 else '')
    txt = TextClip(display_text, fontsize=40, method='caption', color='white',
                   size=(int(clip.w * 0.8), None))
    txt = txt.set_position(('center', 'bottom')).set_duration(duration).fadein(0.5).fadeout(0.5)

    video = CompositeVideoClip([clip, txt]).set_audio(audio)
    video.write_videofile(out_path, fps=24, codec='libx264')

    if os.path.exists(tmp_audio):
        os.remove(tmp_audio)

def process_song(fname):
    if not fname.lower().endswith(('.mp3', '.wav')):
        return
    try:
        print(f"🎶 Processing {fname}...")
        path = os.path.join(SONGS_DIR, fname)
        out_mp4 = os.path.join(OUTPUT_DIR, fname.rsplit('.', 1)[0] + '_clip.mp4')
        start, end, full_text = transcribe_with_timestamps(path)
        make_video_segment(path, start, end, full_text, out_mp4)
        print(f"✅ Video rendered and saved at: {out_mp4}")
    except Exception as e:
        print(f"❌ Error processing {fname}: {e}")
        traceback.print_exc()

def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    threads = []
    for fname in os.listdir(SONGS_DIR):
        t = threading.Thread(target=process_song, args=(fname,))
        t.start()
        threads.append(t)
    for t in threads:
        t.join()

if __name__ == "__main__":
    main()
