import json
import os
import random

class PlaylistManager:
    def __init__(self, playlist_file="playlist.json"):
        self.playlist_file = playlist_file
        self.songs = self.load_playlist()
        self.shuffle_mode = False
        self.shuffle_history = []
        self.shuffle_index = 0
    
        # Fetch missing durations for all songs
        for song in self.songs:
            if "duration" not in song or song["duration"] == "Unknown":
                # We'll implement this in the main.py
                pass
    
    def load_playlist(self):
        """Memuat playlist dari file JSON"""
        try:
            if os.path.exists(self.playlist_file):
                with open(self.playlist_file, 'r', encoding='utf-8') as file:
                    return json.load(file)
            else:
                print("File playlist.json tidak ditemukan. Menggunakan playlist default.")
                return self.get_default_playlist()
        except json.JSONDecodeError:
            print("Format file playlist.json tidak valid. Menggunakan playlist default.")
            return self.get_default_playlist()
        except Exception as e:
            print(f"Error saat memuat playlist: {e}")
            return self.get_default_playlist()
    
    def get_default_playlist(self):
        """Mengembalikan playlist default"""
        return [
            {
                "title": "Indonesian Folk Music Medley 2024 Ver. - hololive ID [Cover]",
                "artist": "hololive ID",
                "url": "https://youtu.be/rjhIMMSolmc?feature=shared",
                "duration": "10:56"
            },
            {
                "title": "Terhebat - hololive ID [Cover]",
                "artist": "hololive ID",
                "url": "https://youtu.be/PaOMF-g1ZWU?feature=shared",
                "duration": "03:12"
            },
            {
                "title": "Bebas - hololive ID [Cover]",
                "artist": "hololive ID",
                "url": "https://youtu.be/wlyRGXUwjVA?feature=shared",
                "duration": "04:04"
            }
        ]
    
    def save_playlist(self):
        """Menyimpan playlist ke file JSON"""
        try:
            with open(self.playlist_file, 'w', encoding='utf-8') as file:
                json.dump(self.songs, file, indent=4, ensure_ascii=False)
            return True, "Playlist berhasil disimpan!"
        except Exception as e:
            return False, f"Gagal menyimpan playlist: {e}"
    
    def add_song(self, title, artist, url, duration="Unknown"):
        """Menambahkan lagu baru ke playlist"""
        new_song = {
            "title": title,
            "artist": artist,
            "url": url,
            "duration": duration
        }
        self.songs.append(new_song)
        return len(self.songs) - 1  # Return index of new song
    
    def update_song(self, index, title=None, artist=None, url=None, duration=None):
        """Memperbarui data lagu yang ada"""
        if 0 <= index < len(self.songs):
            if title:
                self.songs[index]["title"] = title
            if artist:
                self.songs[index]["artist"] = artist
            if url:
                self.songs[index]["url"] = url
            if duration:
                self.songs[index]["duration"] = duration
            return True, "Lagu berhasil diperbarui"
        return False, "Indeks lagu tidak valid"
    
    def delete_song(self, index):
        """Menghapus lagu dari playlist"""
        if 0 <= index < len(self.songs):
            deleted = self.songs.pop(index)
            return True, f"Lagu '{deleted['title']}' berhasil dihapus"
        return False, "Indeks lagu tidak valid"
    
    def get_songs(self):
        """Mendapatkan daftar semua lagu"""
        return self.songs
    
    def get_song(self, index):
        """Mendapatkan lagu berdasarkan indeks"""
        if 0 <= index < len(self.songs):
            return self.songs[index]
        return None
    
    def toggle_shuffle(self):
        """Mengaktifkan/menonaktifkan mode shuffle"""
        self.shuffle_mode = not self.shuffle_mode
        if self.shuffle_mode:
            # Buat daftar acak baru
            self.shuffle_history = list(range(len(self.songs)))
            random.shuffle(self.shuffle_history)
            self.shuffle_index = 0
        return self.shuffle_mode
    
    def get_next_song_index(self, current_index):
        """Mendapatkan indeks lagu berikutnya berdasarkan mode"""
        if not self.songs:
            return 0
        
        if self.shuffle_mode:
            # Jika shuffle mode aktif, ambil dari shuffle history
            self.shuffle_index = (self.shuffle_index + 1) % len(self.shuffle_history)
            return self.shuffle_history[self.shuffle_index]
        else:
            # Jika tidak, lanjut ke lagu berikutnya secara berurutan
            return (current_index + 1) % len(self.songs)
    
    def get_prev_song_index(self, current_index):
        """Mendapatkan indeks lagu sebelumnya berdasarkan mode"""
        if not self.songs:
            return 0
        
        if self.shuffle_mode:
            # Jika shuffle mode aktif, mundur di shuffle history
            self.shuffle_index = (self.shuffle_index - 1) % len(self.shuffle_history)
            return self.shuffle_history[self.shuffle_index]
        else:
            # Jika tidak, kembali ke lagu sebelumnya secara berurutan
            return (current_index - 1) % len(self.songs)
    
    def is_shuffle_mode(self):
        """Cek apakah mode shuffle aktif"""
        return self.shuffle_mode
