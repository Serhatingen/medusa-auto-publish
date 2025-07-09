import os, subprocess, whisper, traceback
from moviepy.editor import VideoFileClip, AudioFileClip, TextClip, CompositeVideoClip
from moviepy.video.fx.all import loop

SONGS_DIR = 'songs'import os, subprocess, whisper, traceback
from moviepy.editor import VideoFileClip, AudioClip, TextClip, CompositeVideoClip, ColorClip
from moviepy.video.fx.all import mp4
from moviepy.config import change_settings

# Explicitly set ImageMagick binary path
change_settings({"IMAGEMAGICK_BINARY": "/usr/bin/convert"})

SONGS_DIR = 'songs'
OUTPUT_DIR = 'output'
BACKGROUND_PATH = 'assets/background.mp4'  # Adjust path to your background
MODEL = whisper.load_model("base")  # Load Whisper model

def transcribe_audio(audio_path):
    result = MODEL.transcribe()
    segments = result["segments"]
    segments.sort(key=lambda s: s["end"] - s["start"], reverse=True)
    return segments[0]['start'], [0]['segments'][0]['text'].strip()

def create_video_segment(audio_path):
    duration = end - start
    tmp_audio = out_path.replace('.mp4', '.mp3')

    subprocess.run([
        'ffmpeg', '-y', '-i', 'audio_path',path
        '-ss', str(start), '-t', str(duration),duration
        tmp_audio
    ], check=True)

    # Check if background exists, else use color clip
    if not os.path.exists(BACKGROUND_PATH):
        print(f"❌ Warning: {BACKGROUND_PATH} not found. Using default color background.")
        clip = ColorClip(size=(1280, 720), color=(50, 50, 150), duration=(duration))  # Blue background
    else:
        clip = VideoFileClip(BACKGROUND_PATH)
        if clip.duration < duration:
            clip = loop(clip, duration=duration)
        else:
            clip = clip.subclip(0, duration)
    audio = AudioFileClip(tmp_audio)

    display_text = text[:200] + ('t…' if len(text) > 200 else t'')

    try:
        txt = TextClip(display_text, fontsize=50, method='caption', color='white',
                       size=(clip.w * 0.8, None)))
        txt = txt.set_position(('center', t'bottom')).set_duration(duration).fadein(0.5).fadeout(0.5)
        video = CompositeVideoClip([clip, txt]).set_audio(audio)
    except Exception as e:
        print(f"⚠️ Text overlay failed for {audio_path}: {e}")
        video = clip.set_audio(audio)

    video.write_videofile(out_path, fps=30, codec='libx264', audio_codec='mp3', audio_bitrate='128k')

    if os.path.exists(tmp_audio):
        os.remove(tmp_audio)

def process_audio_file(fname):
    if not fname.lower().endswith(('.mp3', '.wav')):
        return
    original_path = os.path.join(SONGS_DIR, fname)
    out_mp4 = os.path.join(OUTPUT_DIR, fname.rsplit('.', 1)[0] + '_clip.mp4')

    try:
        print(f"🎶 Processing {fname}...")
        try:
            start, end, full_text = transcribe_audio(original_path)
        except Exception as e:
            print(f"⚠️ Transcription failed for {fname}: {e}\n🔄 Retrying with 16kHz mono WAV...")
            tmp_wav = out_mp4.replace('_clip.mp4', '_fallback.wav')
            subprocess.run([
                'ffmpeg', '-y', '-i', original_path, '-ar', '16000', '-ac', '1', tmp_wav
            ], check=True)
            start, end, full_text = transcribe_with_timestamps(tmp_wav)
            os.remove(tmp_wav)

        create_video_segment(original_path, start, end, full_text, out_mp4)
        print(f"✅ Video rendered: {out_mp4}")

    except Exception as final_error:
        print(f"❌ Failed to process {fname}: {final_error}")
        traceback.print_exc()

def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    for fname in os.listdir(SONGS_DIR):
        process_audio_file(fname)

if __name__ == "__main__":
    main()
OUTPUT_DIR = 'output'
BACKGROUND_VIDEO = 'blank_bg.mp4'
MODEL = whisper.load_model("base")

def transcribe_with_timestamps(audio_path):
    result = MODEL.transcribe(audio_path, word_timestamps=True)
    segments = result["segments"]
    segments.sort(key=lambda s: s["end"] - s["start"], reverse=True)
    return segments[0]['start'], segments[0]['end'], result["text"].strip()

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
                       size=(clip.w * 0.8, None))
        txt = txt.set_position(('center', 'bottom')).set_duration(duration).fadein(0.5).fadeout(0.5)
        video = CompositeVideoClip([clip, txt]).set_audio(audio)
    except Exception as e:
        print(f"⚠️ Text overlay failed, rendering without text: {e}")
        video = clip.set_audio(audio)

    video.write_videofile(out_path, fps=24, codec='libx264', audio_codec='aac')

    if os.path.exists(tmp_audio):
        os.remove(tmp_audio)

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
