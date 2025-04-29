import os

class UI:
    def __init__(self):
        pass
    
    def clear_screen(self):
        """Membersihkan layar terminal"""
        os.system('cls' if os.name == 'nt' else 'clear')
    
    def print_header(self):
        """Menampilkan header aplikasi"""
        print("🎧 Terminal Music Player - hololive ID Edition 🎧")
        print("=" * 50)
        
    def print_progress_bar(self, current_time, duration):
        """Menampilkan progress bar pemutaran lagu"""
        try:
            # Konversi waktu ke detik
            def time_to_seconds(time_str):
                m, s = map(int, time_str.split(':'))
                return m * 60 + s
        
            current_sec = time_to_seconds(current_time)
            total_sec = time_to_seconds(duration)
            progress = min(current_sec / total_sec, 1.0) if total_sec > 0 else 0
        
            # Buat progress bar
            bar_length = 30
            filled_length = int(bar_length * progress)
            bar = '█' * filled_length + '-' * (bar_length - filled_length)
        
            print(f"[{bar}] {current_time} / {duration}")
        except:
            print(f"Time: {current_time} / {duration}")
        
    def print_playlist(self, songs, current_index, shuffle_mode=False):
        """Menampilkan daftar lagu"""
        print("\nPLAYLIST:" + (" [SHUFFLE]" if shuffle_mode else " [URUT]"))
        if not songs:
            print("  (Playlist kosong)")
            return
            
        for i, song in enumerate(songs):
            prefix = ">>" if i == current_index else "  "
            artist = song.get("artist", "Unknown Artist")
            duration = song.get("duration", "??:??")
            print(f"{prefix} {i+1}. {song['title']} - {artist} [{duration}]")
            
        print("\nKetik nomor lagu untuk memilih secara langsung (misalnya: 3)")
    
    def print_controls(self):
        """Menampilkan kontrol yang tersedia"""
        print("\nKONTROL:")
        print("  [p] Play | [s] Stop | [n] Next | [prev] Previous | [r] Shuffle On/Off")
        print("  [a] Add song | [e] Edit song | [d] Delete song | [i] Get song info")
        print("  [dl] Download song | [dla] Download all | [auto] Toggle auto-download")
        print("  [save] Save playlist | [q] Quit")
    
    def print_download_status(self, auto_download, downloaded_count, total_count):
        """Menampilkan status download"""
        print(f"\nAuto-download: {'AKTIF' if auto_download else 'NONAKTIF'} | "
              f"Lagu terdownload: {downloaded_count}/{total_count}")
    
    def print_now_playing(self, song, current_time="00:00"):
        """Menampilkan informasi lagu yang sedang diputar"""
        artist = song.get("artist", "Unknown Artist")
        duration = song.get("duration", "??:??")
        print(f"\nNOW PLAYING: {song['title']} - {artist}")
        self.print_progress_bar(current_time, duration)
    
    def print_message(self, message):
        """Menampilkan pesan ke pengguna"""
        print(f"\n>> {message}")
    
    def get_command(self):
        """Mendapatkan perintah dari pengguna"""
        return input("Command: ").strip().lower()
    
    def add_song_form(self):
        """Form untuk menambahkan lagu baru"""
        self.clear_screen()
        self.print_header()
        print("\nTAMBAH LAGU BARU:")
        
        title = input("Judul lagu: ")
        artist = input("Artis: ")
        url = input("URL (YouTube): ")
        duration = input("Durasi (MM:SS) [optional]: ")
        
        # Validasi input
        if not title or not url:
            return None, None, None, None
        
        # Gunakan durasi default jika tidak diisi
        if not duration:
            duration = "Unknown"
        
        return title, artist, url, duration
    
    def edit_song_form(self, song):
        """Form untuk mengubah lagu"""
        self.clear_screen()
        self.print_header()
        print("\nEDIT LAGU:")
        print(f"Lagu: {song['title']} - {song.get('artist', 'Unknown Artist')}")
        
        print("\nKosongkan input untuk mempertahankan nilai sebelumnya")
        title = input(f"Judul lagu [{song['title']}]: ")
        artist = input(f"Artis [{song.get('artist', 'Unknown Artist')}]: ")
        url = input(f"URL [{song['url']}]: ")
        duration = input(f"Durasi [{song.get('duration', 'Unknown')}]: ")
        
        # Gunakan nilai sebelumnya jika input kosong
        title = title if title else None
        artist = artist if artist else None
        url = url if url else None
        duration = duration if duration else None
        
        return title, artist, url, duration
    
    def confirm_delete(self, song):
        """Konfirmasi penghapusan lagu"""
        response = input(f"Hapus lagu '{song['title']}' dari playlist? (y/n): ")
        return response.lower() == 'y'
