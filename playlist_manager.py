import json
import os
import random
import subprocess
import csv
import re
from datetime import datetime

class PlaylistManager:
    def __init__(self, playlist_file="playlist.json"):
        self.playlist_file = playlist_file
        self.songs = []
        self.shuffle_mode = False
        self.shuffle_history = []
        self.shuffle_index = 0
        
        # Load playlist on initialization
        self.songs = self.load_playlist()
    
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
    
    def validate_song_data(self, title, artist, url, duration):
        """Validasi data lagu"""
        errors = []
        
        if not title or not isinstance(title, str):
            errors.append("Judul lagu tidak valid")
        
        if not url or not isinstance(url, str):
            errors.append("URL lagu tidak valid")
        elif not (url.startswith("http://") or url.startswith("https://")):
            errors.append("URL harus dimulai dengan http:// atau https://")
            
        # Validate duration format if provided
        if duration and duration != "Unknown":
            if not re.match(r'^\d{1,2}:\d{2}$', duration):
                errors.append("Format durasi harus MM:SS")
        
        return errors
    
    def fetch_duration(self, url):
        """Mengambil durasi lagu dari URL menggunakan yt-dlp"""
        try:
            result = subprocess.run(
                ["yt-dlp", "--dump-json", "--no-warnings", url],
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                text=True,
                timeout=10  # Add timeout to prevent hanging
            )
            
            if result.returncode != 0:
                return "Unknown"
                
            info = json.loads(result.stdout)
            duration_seconds = int(info.get("duration", 0))
            
            # Handle very long durations (like livestreams)
            if duration_seconds > 24*60*60:  # If longer than 24 hours
                return "Live"
                
            hours = duration_seconds // 3600
            minutes = (duration_seconds % 3600) // 60
            seconds = duration_seconds % 60
            
            # Format based on length
            if hours > 0:
                return f"{hours:01d}:{minutes:02d}:{seconds:02d}"
            else:
                return f"{minutes:02d}:{seconds:02d}"
                
        except (subprocess.TimeoutExpired, json.JSONDecodeError, Exception) as e:
            print(f"Error fetching duration: {e}")
            return "Unknown"
    
    def save_playlist(self):
        """Menyimpan playlist ke file JSON"""
        try:
            # Create backup of existing playlist
            if os.path.exists(self.playlist_file):
                backup_file = f"{os.path.splitext(self.playlist_file)[0]}_backup_{datetime.now().strftime('%Y%m%d%H%M%S')}.json"
                try:
                    with open(self.playlist_file, 'r', encoding='utf-8') as src:
                        with open(backup_file, 'w', encoding='utf-8') as dst:
                            dst.write(src.read())
                except Exception as e:
                    print(f"Warning: Could not create playlist backup: {e}")
            
            # Save current playlist
            with open(self.playlist_file, 'w', encoding='utf-8') as file:
                json.dump(self.songs, file, indent=4, ensure_ascii=False)
            return True, "Playlist berhasil disimpan!"
        except Exception as e:
            return False, f"Gagal menyimpan playlist: {e}"
    
    def add_song(self, title, artist, url, duration="Unknown"):
        """Menambahkan lagu baru ke playlist dengan validasi"""
        # Validate song data
        errors = self.validate_song_data(title, artist, url, duration)
        if errors:
            return -1, f"Error: {'; '.join(errors)}"
        
        # Auto fetch duration if not provided or unknown
        if duration == "Unknown":
            duration = self.fetch_duration(url)
        
        new_song = {
            "title": title,
            "artist": artist or "Unknown Artist",
            "url": url,
            "duration": duration,
            "added_date": datetime.now().strftime("%Y-%m-%d")
        }
        
        self.songs.append(new_song)
        self.save_playlist()  # Auto-save after adding
        return len(self.songs) - 1, f"Lagu '{title}' berhasil ditambahkan"  # Return index of new song
    
    def update_song(self, index, title=None, artist=None, url=None, duration=None):
        """Memperbarui data lagu yang ada dengan validasi"""
        if 0 <= index < len(self.songs):
            # If we're updating URL and duration is not specified, we should refetch
            refetch_duration = url is not None and duration is None
            
            current_song = self.songs[index]
            
            # Prepare new data, keeping existing values where not specified
            new_title = title if title is not None else current_song["title"]
            new_artist = artist if artist is not None else current_song["artist"]
            new_url = url if url is not None else current_song["url"]
            new_duration = duration if duration is not None else current_song["duration"]
            
            # Validate the new data
            errors = self.validate_song_data(new_title, new_artist, new_url, new_duration)
            if errors:
                return False, f"Error: {'; '.join(errors)}"
            
            # Refetch duration if URL changed
            if refetch_duration:
                new_duration = self.fetch_duration(new_url)
            
            # Update the song
            self.songs[index]["title"] = new_title
            self.songs[index]["artist"] = new_artist
            self.songs[index]["url"] = new_url
            self.songs[index]["duration"] = new_duration
            self.songs[index]["updated_date"] = datetime.now().strftime("%Y-%m-%d")
            
            # Auto-save after updating
            self.save_playlist()
            return True, "Lagu berhasil diperbarui"
        return False, "Indeks lagu tidak valid"
    
    def delete_song(self, index):
        """Menghapus lagu dari playlist"""
        if 0 <= index < len(self.songs):
            deleted = self.songs.pop(index)
            # Auto-save after deletion
            self.save_playlist()
            return True, f"Lagu '{deleted['title']}' berhasil dihapus"
        return False, "Indeks lagu tidak valid"
    
    def export_playlist(self, filename, format="json"):
        """Export playlist to different formats"""
        try:
            if format.lower() == "json":
                with open(filename, 'w', encoding='utf-8') as file:
                    json.dump(self.songs, file, indent=4, ensure_ascii=False)
                    
            elif format.lower() == "m3u":
                with open(filename, 'w', encoding='utf-8') as file:
                    file.write("#EXTM3U\n")
                    for song in self.songs:
                        duration_secs = self._duration_to_seconds(song.get("duration", "Unknown"))
                        file.write(f"#EXTINF:{duration_secs},{song.get('artist', 'Unknown Artist')} - {song['title']}\n")
                        file.write(f"{song['url']}\n")
                        
            elif format.lower() == "csv":
                with open(filename, 'w', encoding='utf-8', newline='') as file:
                    writer = csv.writer(file)
                    # Write header
                    writer.writerow(["Title", "Artist", "URL", "Duration", "Added Date"])
                    # Write songs
                    for song in self.songs:
                        writer.writerow([
                            song["title"],
                            song.get("artist", "Unknown Artist"),
                            song["url"],
                            song.get("duration", "Unknown"),
                            song.get("added_date", "")
                        ])
            else:
                return False, f"Format '{format}' tidak didukung"
                
            return True, f"Playlist berhasil diekspor ke {filename}"
        except Exception as e:
            return False, f"Gagal mengekspor playlist: {e}"
    
    def import_playlist(self, filename, format="json", append=False):
        """Import playlist from different formats"""
        try:
            imported_songs = []
            
            if format.lower() == "json":
                with open(filename, 'r', encoding='utf-8') as file:
                    imported_songs = json.load(file)
                    
            elif format.lower() == "m3u":
                with open(filename, 'r', encoding='utf-8') as file:
                    lines = file.readlines()
                    i = 0
                    while i < len(lines):
                        line = lines[i].strip()
                        if line.startswith("#EXTINF:"):
                            # Parse EXTINF line
                            info_parts = line[8:].split(',', 1)
                            if len(info_parts) > 1:
                                title_artist = info_parts[1]
                                if " - " in title_artist:
                                    artist, title = title_artist.split(" - ", 1)
                                else:
                                    artist = "Unknown Artist"
                                    title = title_artist
                                
                                # Get URL from next line
                                if i + 1 < len(lines):
                                    url = lines[i + 1].strip()
                                    duration = "Unknown"  # M3U doesn't have reliable duration info
                                    
                                    imported_songs.append({
                                        "title": title,
                                        "artist": artist,
                                        "url": url,
                                        "duration": duration,
                                        "added_date": datetime.now().strftime("%Y-%m-%d")
                                    })
                                    i += 1  # Skip the URL line
                        i += 1
                        
            elif format.lower() == "csv":
                with open(filename, 'r', encoding='utf-8', newline='') as file:
                    reader = csv.reader(file)
                    header = next(reader, None)  # Skip header
                    
                    for row in reader:
                        if len(row) >= 3:  # At least title, artist, url
                            title = row[0]
                            artist = row[1]
                            url = row[2]
                            duration = row[3] if len(row) > 3 else "Unknown"
                            
                            imported_songs.append({
                                "title": title,
                                "artist": artist,
                                "url": url,
                                "duration": duration,
                                "added_date": datetime.now().strftime("%Y-%m-%d")
                            })
            else:
                return False, f"Format '{format}' tidak didukung"
            
            # Update playlist
            if not append:
                self.songs = imported_songs
            else:
                self.songs.extend(imported_songs)
                
            # Save the updated playlist
            self.save_playlist()
            
            return True, f"Berhasil mengimpor {len(imported_songs)} lagu"
        except Exception as e:
            return False, f"Gagal mengimpor playlist: {e}"
    
    def search_songs(self, query, fields=None):
        """Search songs by query in specified fields"""
        if fields is None:
            fields = ["title", "artist"]
            
        results = []
        query = query.lower()
        
        for i, song in enumerate(self.songs):
            for field in fields:
                if field in song and query in str(song[field]).lower():
                    results.append((i, song))
                    break  # Don't add the same song twice
                    
        return results
    
    def _duration_to_seconds(self, duration):
        """Convert duration string to seconds"""
        if duration == "Unknown" or duration == "Live":
            return -1
            
        parts = duration.split(":")
        if len(parts) == 2:  # MM:SS
            return int(parts[0]) * 60 + int(parts[1])
        elif len(parts) == 3:  # HH:MM:SS
            return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
        return -1
    
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
        
    def update_all_durations(self, callback=None):
        """Update durasi untuk semua lagu dengan durasi yang tidak diketahui"""
        updated_count = 0
        
        for i, song in enumerate(self.songs):
            if callback:
                callback(i, len(self.songs), song["title"])
                
            if song.get("duration") == "Unknown":
                new_duration = self.fetch_duration(song["url"])
                if new_duration != "Unknown":
                    self.songs[i]["duration"] = new_duration
                    updated_count += 1
        
        if updated_count > 0:
            self.save_playlist()
            
        return updated_count
