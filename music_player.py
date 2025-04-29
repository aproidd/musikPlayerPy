import os
import subprocess
import json

def clear():
    # Perintah clear untuk Windows atau Unix/Linux/Mac
    os.system('cls' if os.name == 'nt' else 'clear')

def load_playlist():
    # Coba memuat playlist dari file JSON
    try:
        with open('playlist.json', 'r', encoding='utf-8') as file:
            return json.load(file)
    except FileNotFoundError:
        print("File playlist.json tidak ditemukan. Menggunakan playlist default.")
        return [
            {
                "title": "Indonesian Folk Music Medley 2024 Ver. - hololive ID [Cover]",
                "artist": "hololive ID",
                "url": "https://youtu.be/rjhIMMSolmc?feature=shared"
            },
        ]
    except json.JSONDecodeError:
        print("Format file playlist.json tidak valid. Menggunakan playlist default.")
        return [
            {
                "title": "Indonesian Folk Music Medley 2024 Ver. - hololive ID [Cover]",
                "artist": "hololive ID",
                "url": "https://youtu.be/rjhIMMSolmc?feature=shared"
            },
        ]

def save_playlist(songs):
    # Simpan playlist ke file JSON
    try:
        with open('playlist.json', 'w', encoding='utf-8') as file:
            json.dump(songs, file, indent=4, ensure_ascii=False)
        print("Playlist berhasil disimpan!")
    except Exception as e:
        print(f"Gagal menyimpan playlist: {e}")

def print_menu(current_index, songs):
    clear()
    print("🎧 Terminal Music Player - hololive ID Edition 🎧\n")
    for i, song in enumerate(songs):
        prefix = ">>" if i == current_index else "  "
        artist = song.get("artist", "Unknown Artist")
        print(f"{prefix} {i+1}. {song['title']} - {artist}")
    print("\n[Enter] Play | [n] Next | [p] Prev | [s] Save Playlist | [q] Quit")

def get_duration_from_url(url):
    try:
        result = subprocess.run(
            ["yt-dlp", "--dump-json", "--no-warnings", url],
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True
        )
        info = json.loads(result.stdout)
        duration = int(info.get("duration", 0))
        minutes = duration // 60
        seconds = duration % 60
        return f"{minutes:02}:{seconds:02}"
    except Exception:
        return "Unknown"

def play_song(url):
    try:
        subprocess.run([
            "mpv",
            "--no-video",
            "--audio-display=no",      # Jangan tampilkan info audio
            "--sub-auto=no",           # Jangan load subtitle otomatis
            url
        ])
    except FileNotFoundError:
        print("Error: Program MPV tidak ditemukan. Pastikan MPV terinstal di sistem Anda.")
        input("Tekan Enter untuk kembali ke menu...")


def main():
    songs = load_playlist()
    current = 0
    
    while True:
        print_menu(current, songs)
        command = input("Command: ").strip().lower()
        if command == 'n':
            current = (current + 1) % len(songs)
        elif command == 'p':
            current = (current - 1) % len(songs)
        elif command == 's':
            save_playlist(songs)
            input("Tekan Enter untuk melanjutkan...")
        elif command == 'q':
            break
        else:
            print(f"🎵 Playing: {songs[current]['title']} - {songs[current].get('artist', 'Unknown Artist')}")
            play_song(songs[current]["url"])
            
def _monitor_playback(self):
    """Memantau status pemutaran untuk mengetahui kapan lagu selesai dan update waktu"""
    while self.is_running and self.process and self.process.poll() is None:
        try:
            # Baca output untuk mendapatkan waktu
            line = self.process.stdout.readline()
            if "AV:" in line or "A:" in line:  # Format output mpv untuk waktu pemutaran
                # Parse waktu pemutaran dengan lebih baik
                time_match = re.search(r'A:\s*(\d+):(\d+):(\d+)|\s*A:\s*(\d+):(\d+)', line)
                if time_match:
                    if time_match.group(1) is not None:
                        # Format HH:MM:SS
                        h, m, s = int(time_match.group(1)), int(time_match.group(2)), int(time_match.group(3))
                        self.current_time = f"{h*60+m:02d}:{s:02d}"
                    else:
                        # Format MM:SS
                        m, s = int(time_match.group(4)), int(time_match.group(5))
                        self.current_time = f"{m:02d}:{s:02d}"
        except Exception:
            pass
            
        # Beri waktu untuk mengurangi penggunaan CPU, tetapi cukup cepat untuk update
        time.sleep(1)  # Lebih cepat untuk update lebih responsif
        
if __name__ == "__main__":
    main()
