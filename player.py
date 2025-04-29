import subprocess
import json
import time
import threading
import re
import os

class MusicPlayer:
    def __init__(self):
        self.process = None
        self.current_time = "00:00"
        self.duration = "00:00"
        self.is_running = False
        self.monitor_thread = None
        self.auto_next_callback = None
        self.auto_download = False  # Mode auto-download dinonaktifkan secara default

    def play(self, url, auto_next_callback=None, local=False):
        """Memutar lagu dari URL atau file lokal"""
        try:
            self.stop()  # Hentikan proses sebelumnya jika ada
            self.auto_next_callback = auto_next_callback  # Simpan callback untuk auto-next

            # Tentukan command berdasarkan jenis sumber (URL atau file lokal)
            command = [
                "mpv", 
                "--no-video", 
                "--audio-display=no", 
                "--sub-auto=no",
                "--cache=yes",           # Enable cache
                "--cache-secs=30",       # Cache 30 seconds ahead
                "--demuxer-readahead-secs=5"  # Read 5 seconds ahead
            ]
            
            if not local:
                # Tambahkan opsi format audio terbaik jika streaming dari URL
                command.extend([
                    "--ytdl-format=bestaudio",
                    "--ytdl-raw-options=format-sort=+codec:aac"
                ])
            
            command.append(url)  # Tambahkan URL atau path file

            # Proses dibuat dengan prioritas buffer yang lebih tinggi
            self.process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE, 
                text=True, 
                bufsize=1,  # Line buffered mode untuk respons yang lebih cepat
                universal_newlines=True
            )

            # Tambahkan jeda kecil untuk memastikan buffer terisi di awal
            # tapi tidak terlalu lama agar tidak terasa lambat
            time.sleep(0.2)

            self.is_running = True
            self.current_time = "00:00"

            # Mulai thread untuk memantau status pemutaran
            self.monitor_thread = threading.Thread(target=self._monitor_playback)
            self.monitor_thread.daemon = True
            self.monitor_thread.start()

            return True, ""
        except FileNotFoundError:
            return False, "Error: Program MPV tidak ditemukan. Pastikan MPV terinstal di sistem Anda."
        except Exception as e:
            return False, f"Error saat memutar lagu: {e}"

    def _monitor_playback(self):
        """Memantau status pemutaran untuk mengetahui kapan lagu selesai dan update waktu"""
        buffer_period = True
        buffer_start_time = time.time()
        
        while self.is_running and self.process and self.process.poll() is None:
            try:
                # Beri waktu buffer di awal pemutaran
                if buffer_period and (time.time() - buffer_start_time < 1.0):
                    time.sleep(0.1)
                    continue
                else:
                    buffer_period = False
                
                line = self.process.stdout.readline()
                if not line:
                    # Jika tidak ada output, cek status proses
                    if self.process.poll() is not None:
                        break
                    # Jika masih running tapi tidak ada output, tunggu sebentar
                    time.sleep(0.1)  # Sedikit lebih lama untuk stabilitas
                    continue

                if "AV:" in line or "A:" in line:
                    time_match = re.search(r'A:\s*(\d+):(\d+):(\d+)|\s*A:\s*(\d+):(\d+)', line)
                    if time_match:
                        if time_match.group(1) is not None:
                            h, m, s = int(time_match.group(1)), int(time_match.group(2)), int(time_match.group(3))
                            self.current_time = f"{h*60+m:02d}:{s:02d}"
                        else:
                            m, s = int(time_match.group(4)), int(time_match.group(5))
                            self.current_time = f"{m:02d}:{s:02d}"

                if "EOF" in line or "Exiting..." in line:
                    break

            except Exception:
                pass

            # Jeda monitoring yang lebih seimbang
            time.sleep(0.2)  # Lebih lambat tetapi masih responsif

        # Setelah lagu selesai
        if self.is_running and self.auto_next_callback:
            self.is_running = False
            self.auto_next_callback()

    def stop(self):
        """Menghentikan pemutaran lagu"""
        if self.process and self.process.poll() is None:
            self.is_running = False
            try:
                # Kirim sinyal 'q' untuk mpv agar keluar dengan bersih
                self.process.communicate(input='q', timeout=0.5)
            except:
                # Jika gagal, gunakan metode terminasi standar
                self.process.terminate()
                try:
                    self.process.wait(timeout=1)
                except subprocess.TimeoutExpired:
                    self.process.kill()

        if self.monitor_thread and self.monitor_thread.is_alive():
            self.monitor_thread.join(0.5)

    def get_song_info(self, url):
        """Mendapatkan info lagu dari URL (memerlukan yt-dlp)"""
        try:
            result = subprocess.run(
                ["yt-dlp", "--dump-json", "--no-warnings", url],
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                text=True
            )
            info = json.loads(result.stdout)

            duration_seconds = int(info.get("duration", 0))
            minutes = duration_seconds // 60
            seconds = duration_seconds % 60
            duration = f"{minutes:02d}:{seconds:02d}"

            return {
                "duration": duration,
                "title": info.get("title", "Unknown Title"),
                "uploader": info.get("uploader", "Unknown Artist")
            }
        except Exception:
            return {
                "duration": "Unknown",
                "title": "Unknown Title",
                "uploader": "Unknown Artist"
            }
            
    def download_song(self, url, output_file):
        """Download song using yt-dlp with optimized settings"""
        try:
            command = [
                "yt-dlp", 
                "-x",                         # Extract audio
                "--audio-format", "mp3",      # Convert to mp3
                "--audio-quality", "0",       # Best quality
                "-o", output_file,            # Output file
                "--embed-metadata",           # Embed metadata
                "--no-playlist",              # Don't download playlist
                "--no-overwrites",            # Don't overwrite existing files
                "--no-continue",              # Don't continue partial downloads
                url                           # URL to download
            ]
            
            result = subprocess.run(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Check if download was successful
            if result.returncode == 0 and os.path.exists(output_file):
                return True
            else:
                print(f"Download error: {result.stderr}")
                return False
        except Exception as e:
            print(f"Download error: {str(e)}")
            return False

    def get_current_time(self):
        """Mendapatkan waktu pemutaran saat ini"""
        return self.current_time

    def is_playing(self):
        """Cek apakah sedang memutar lagu"""
        return self.is_running and self.process and self.process.poll() is None
        
    def toggle_auto_download(self):
        """Toggle mode auto-download"""
        self.auto_download = not self.auto_download
        return self.auto_download
        
    def is_auto_download(self):
        """Cek apakah mode auto-download aktif"""
        return self.auto_download
