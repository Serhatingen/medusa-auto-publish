import os
import subprocess

# Kütüphane Linkleri
# ffmpeg: https://ffmpeg.org/

SONGS_DIR = 'songs'
OUTPUT_DIR = 'output'
BACKGROUND_VIDEO = 'blank_bg.mp4'

def process_song(fname):
    """Ses dosyasını FFmpeg ile basit bir video klibine dönüştürür."""
    if not fname.lower().endswith(('.mp3', '.wav')):
        print(f"⚠️ {fname} desteklenmeyen dosya formatı, atlanıyor.")
        return

    original_path = os.path.join(SONGS_DIR, fname)
    out_mp4 = os.path.join(OUTPUT_DIR, fname.rsplit('.', 1)[0] + '_clip.mp4')

    if not os.path.exists(original_path):
        print(f"❌ Dosya bulunamadı: {original_path}")
        return

    try:
        print(f"🎶 {fname} işleniyor...")
        subprocess.run([
            'ffmpeg', '-y', '-i', BACKGROUND_VIDEO, '-i', original_path,
            '-c:v', 'copy', '-c:a', 'aac', '-shortest', out_mp4
        ], check=True, capture_output=True, text=True)
        print(f"✅ Video oluşturuldu: {out_mp4}")
    except subprocess.CalledProcessError as e:
        print(f"❌ FFmpeg hatası: {e.stderr}")

def main():
    """Ana işlev: songs dizinindeki dosyaları işler."""
    print(f"📁 Çalışma dizini: {os.getcwd()}")
    print(f"📂 songs dizini içeriği: {os.listdir(SONGS_DIR) if os.path.exists(SONGS_DIR) else 'Dizin bulunamadı'}")
    
    if not os.path.exists(SONGS_DIR):
        print(f"❌ {SONGS_DIR} dizini bulunamadı.")
        return
    if not os.path.exists(BACKGROUND_VIDEO):
        print(f"❌ Arka plan videosu bulunamadı: {BACKGROUND_VIDEO}")
        return

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    for fname in os.listdir(SONGS_DIR):
        process_song(fname)

if __name__ == "__main__":
    main()