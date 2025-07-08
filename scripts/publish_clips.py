import os, subprocess, whisper, yaml, traceback, time, threading
from moviepy.editor import VideoFileClip, AudioFileClip, TextClip, CompositeVideoClip
import moviepy.video.fx as vfx
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# === CONFIGURATION ===
SONGS_DIR = 'songs'
OUTPUT_DIR = 'output'
BACKGROUND_VIDEO = 'blank_bg.mp4'
THUMBNAIL_IMG = 'thumbnail.jpg'  # optional
MODEL = whisper.load_model("base")

# === YOUTUBE SETUP ===
SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]
credentials = service_account.Credentials.from_service_account_info(
    yaml.safe_load(os.environ["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"]),
    scopes=SCOPES
)
youtube = build('youtube', 'v3', credentials=credentials)

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

def upload_to_youtube(video_file, title, description, tags):
    body = {
        'snippet': {
            'title': title,
            'description': description,
            'tags': tags,
            'categoryId': '10'
        },
        'status': {'privacyStatus': 'public'}
    }

    media = MediaFileUpload(video_file, resumable=True, mimetype='video/mp4')

    for attempt in range(3):
        try:
            req = youtube.videos().insert(part="snippet,status", body=body, media_body=media)
            resp = req.execute()
            print(f"✅ Uploaded: https://youtu.be/{resp['id']}")
            if os.path.exists(THUMBNAIL_IMG):
                youtube.thumbnails().set(videoId=resp["id"],
                                         media_body=MediaFileUpload(THUMBNAIL_IMG)).execute()
            return
        except Exception as e:
            print(f"⚠️ Upload failed ({attempt+1}/3): {e}")
            time.sleep(2)
    print("❌ Upload failed after 3 attempts")

def process_song(fname):
    if not fname.lower().endswith(('.mp3', '.wav')):
        return
    try:
        print(f"🎶 Processing {fname}...")
        path = os.path.join(SONGS_DIR, fname)
        out_mp4 = os.path.join(OUTPUT_DIR, fname.rsplit('.', 1)[0] + '_clip.mp4')
        start, end, full_text = transcribe_with_timestamps(path)
        make_video_segment(path, start, end, full_text, out_mp4)
        upload_to_youtube(out_mp4, f"Medusa Clip – {fname}", "Auto‐created by Medusa Bot",
                          ["MedusaRecords", "MusicClip"])
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
