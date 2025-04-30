import subprocess
import json
import time
import threading
import re
import os
import socket
import tempfile
import atexit
import logging
from pathlib import Path
from dataclasses import dataclass
from typing import Optional, Dict, Any, Callable, Union, List, Tuple

# Setup basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("MusicPlayer")

@dataclass
class PlaybackStatus:
    """Data class to store playback status information"""
    playing: bool = False
    paused: bool = False
    duration: float = 0  # in seconds
    position: float = 0  # in seconds
    volume: int = 100    # percentage
    source_path: str = ""
    is_stream: bool = False
    media_title: str = ""
    
    @property
    def position_formatted(self) -> str:
        """Return formatted position as MM:SS"""
        minutes = int(self.position // 60)
        seconds = int(self.position % 60)
        return f"{minutes:02d}:{seconds:02d}"
        
    @property
    def duration_formatted(self) -> str:
        """Return formatted duration as MM:SS"""
        minutes = int(self.duration // 60)
        seconds = int(self.duration % 60)
        return f"{minutes:02d}:{seconds:02d}"
        
    @property
    def progress_percentage(self) -> float:
        """Return playback progress as percentage"""
        if self.duration <= 0:
            return 0
        return min(100, max(0, (self.position / self.duration) * 100))

class MusicPlayer:
    def __init__(self, socket_dir=None):
        """Initialize MusicPlayer with improved IPC communication"""
        self.process = None
        self.is_running = False
        self.ipc_thread = None
        self.auto_next_callback = None
        self.auto_download = False  # Mode auto-download dinonaktifkan secara default
        
        # Setup socket path for IPC
        self.socket_dir = socket_dir or tempfile.gettempdir()
        self.socket_path = os.path.join(self.socket_dir, f"mpv-socket-{os.getpid()}")
        if os.name == 'nt':
            self.socket_path = self.socket_path.replace('\\', '/')
        
        # For event callbacks
        self._event_handlers = {}
        
        # Status tracking
        self.status = PlaybackStatus()
        
        # Clean up socket file on exit
        atexit.register(self._cleanup)

    def _cleanup(self):
        """Clean up resources when player is destroyed"""
        self.stop()
        try:
            if os.path.exists(self.socket_path):
                os.unlink(self.socket_path)
        except:
            pass
            
    def _send_command(self, command: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Send command to mpv via IPC socket and get response"""
        if not self.is_running or not os.path.exists(self.socket_path):
            logger.debug("Cannot send command: player not running or socket not available")
            return None
            
        try:
            with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as sock:
                sock.connect(self.socket_path)
                sock.sendall(json.dumps(command).encode('utf-8') + b'\n')
                
                if command.get('request_id') is not None:
                    sock.settimeout(1.0)
                    response = b''
                    while True:
                        try:
                            chunk = sock.recv(4096)
                            if not chunk:
                                break
                            response += chunk
                            if b'\n' in response:
                                break
                        except socket.timeout:
                            break
                            
                    if response:
                        try:
                            return json.loads(response)
                        except json.JSONDecodeError:
                            logger.warning("Invalid JSON response from mpv")
                            
            return None
        except Exception as e:
            logger.error(f"Error sending command to mpv: {e}")
            return None
            
    def _ipc_listen_thread(self):
        """Thread that listens for events from mpv's IPC socket"""
        reconnect_delay = 0.1
        max_reconnect_delay = 2.0
        
        while self.is_running and self.process and self.process.poll() is None:
            try:
                if not os.path.exists(self.socket_path):
                    time.sleep(reconnect_delay)
                    reconnect_delay = min(reconnect_delay * 1.5, max_reconnect_delay)
                    continue
                    
                reconnect_delay = 0.1
                
                with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as sock:
                    sock.connect(self.socket_path)
                    sock.settimeout(0.5)
                    
                    buffer = b''
                    while self.is_running and self.process and self.process.poll() is None:
                        try:
                            data = sock.recv(4096)
                            if not data:
                                break
                                
                            buffer += data
                            
                            while b'\n' in buffer:
                                line, buffer = buffer.split(b'\n', 1)
                                if line:
                                    try:
                                        event = json.loads(line)
                                        self._handle_event(event)
                                    except json.JSONDecodeError:
                                        logger.warning(f"Invalid JSON from mpv: {line}")
                        except socket.timeout:
                            continue
                        except Exception as e:
                            logger.error(f"Socket error: {e}")
                            break
            except Exception as e:
                logger.error(f"IPC thread error: {e}")
                time.sleep(reconnect_delay)
                reconnect_delay = min(reconnect_delay * 1.5, max_reconnect_delay)
                
        if self.status.playing and self.auto_next_callback:
            self.status.playing = False
            self.auto_next_callback()
            
    def _handle_event(self, event: Dict[str, Any]):
        """Handle events from mpv"""
        if not event:
            return
            
        event_name = event.get('event')
        
        if event_name == 'property-change':
            prop = event.get('name')
            value = event.get('data')
            
            if prop == 'time-pos' and value is not None:
                self.status.position = float(value)
            elif prop == 'duration' and value is not None:
                self.status.duration = float(value)
            elif prop == 'pause' and value is not None:
                self.status.paused = bool(value)
            elif prop == 'volume' and value is not None:
                self.status.volume = int(value)
            elif prop == 'media-title' and value is not None:
                self.status.media_title = str(value)
                
        elif event_name == 'end-file':
            reason = event.get('reason')
            if reason == 'eof' and self.auto_next_callback:
                self.status.playing = False
                self.auto_next_callback()
                
        if event_name in self._event_handlers:
            for handler in self._event_handlers.get(event_name, []):
                try:
                    handler(event)
                except Exception as e:
                    logger.error(f"Error in event handler: {e}")
                
    def on_event(self, event_name: str, callback: Callable[[Dict[str, Any]], None]):
        """Register callback for specific mpv events"""
        if event_name not in self._event_handlers:
            self._event_handlers[event_name] = []
        self._event_handlers[event_name].append(callback)
        return self

    def play(self, url: str, auto_next_callback=None, local=False) -> Tuple[bool, str]:
        """Memutar lagu dari URL atau file lokal"""
        try:
            self.stop()
            self.auto_next_callback = auto_next_callback
            self.status = PlaybackStatus(
                source_path=url,
                is_stream=not local
            )

            command = [
                "mpv", 
                "--no-video", 
                "--audio-display=no", 
                "--sub-auto=no",
                "--cache=yes",
                "--cache-secs=30",
                "--demuxer-readahead-secs=5",
                f"--input-ipc-server={self.socket_path}"
            ]
             
            if not local:
                command.extend([
                    "--ytdl-format=bestaudio",
                    "--ytdl-raw-options=format-sort=+codec:aac"
                ])
                
            command.extend([
                "--pause=no",
                "--force-window=no",
                "--msg-level=all=v",
                "--idle=yes",
                "--property-expansion",
                "--observe-property=1,time-pos",
                "--observe-property=2,duration",
                "--observe-property=3,pause",
                "--observe-property=4,volume",
                "--observe-property=5,media-title"
            ])
             
            command.append(url)

            self.process = subprocess.Popen(
                command,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                universal_newlines=True
            )

            time.sleep(0.2)

            self.is_running = True
            self.status.playing = True
            self.status.paused = False

            self.ipc_thread = threading.Thread(target=self._ipc_listen_thread)
            self.ipc_thread.daemon = True
            self.ipc_thread.start()

            return True, ""
        except FileNotFoundError:
            return False, "Error: Program MPV tidak ditemukan. Pastikan MPV terinstal di sistem Anda."
        except Exception as e:
            logger.error(f"Error starting playback: {e}")
            return False, f"Error saat memutar lagu: {e}"

    def stop(self):
        """Menghentikan pemutaran lagu"""
        if self.process and self.process.poll() is None:
            self.is_running = False
            self.status.playing = False
            try:
                self._send_command({"command": ["quit"]})
                time.sleep(0.1)
                if self.process.poll() is None:
                    self.process.communicate(input='q', timeout=0.5)
            except:
                self.process.terminate()
                try:
                    self.process.wait(timeout=1)
                except subprocess.TimeoutExpired:
                    self.process.kill()

        if self.ipc_thread and self.ipc_thread.is_alive():
            self.ipc_thread.join(0.5)

    def pause(self) -> bool:
        """Pause playback"""
        if not self.is_playing():
            return False
            
        result = self._send_command({
            "command": ["set_property", "pause", True],
            "request_id": 1
        })
        success = result and result.get('error') == 'success'
        if success:
            self.status.paused = True
        return success
        
    def resume(self) -> bool:
        """Resume playback"""
        if not self.is_playing() or not self.status.paused:
            return False
            
        result = self._send_command({
            "command": ["set_property", "pause", False],
            "request_id": 2
        })
        success = result and result.get('error') == 'success'
        if success:
            self.status.paused = False
        return success
        
    def toggle_pause(self) -> bool:
        """Toggle pause state"""
        if not self.is_playing():
            return False
            
        if self.status.paused:
            return self.resume()
        else:
            return self.pause()
            
    def seek(self, position: Union[int, float, str]) -> bool:
        """
        Seek to position
        
        Args:
            position: Can be absolute seconds (float), 
                      relative seconds (str with +/- prefix),
                      or time format "MM:SS"
        """
        if not self.is_playing():
            return False
            
        try:
            if isinstance(position, str) and ':' in position:
                minutes, seconds = position.split(':')
                position = int(minutes) * 60 + int(seconds)
            
            if isinstance(position, (int, float)):
                position_str = str(position)
            else:
                position_str = position
                
            result = self._send_command({
                "command": ["seek", position_str, "absolute"],
                "request_id": 3
            })
            return result and result.get('error') == 'success'
        except Exception as e:
            logger.error(f"Error seeking: {e}")
            return False
            
    def set_volume(self, volume: int) -> bool:
        """Set volume (0-100)"""
        if not self.is_playing():
            return False
            
        try:
            volume = max(0, min(100, int(volume)))
            result = self._send_command({
                "command": ["set_property", "volume", volume],
                "request_id": 4
            })
            success = result and result.get('error') == 'success'
            if success:
                self.status.volume = volume
            return success
        except Exception as e:
            logger.error(f"Error setting volume: {e}")
            return False
            
    def adjust_volume(self, delta: int) -> bool:
        """Adjust volume by delta (-100 to +100)"""
        try:
            current = self.status.volume
            return self.set_volume(current + delta)
        except Exception as e:
            logger.error(f"Error adjusting volume: {e}")
            return False

    def get_song_info(self, url):
        """Mendapatkan info lagu dari URL (memerlukan yt-dlp)"""
        try:
            result = subprocess.run(
                ["yt-dlp", "--dump-json", "--no-warnings", "--no-playlist", url],
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                text=True,
                timeout=15
            )
            
            if result.returncode != 0:
                return {
                    "duration": "Unknown",
                    "title": "Unknown Title",
                    "uploader": "Unknown Artist"
                }
                
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
        except Exception as e:
            logger.error(f"Error getting song info: {e}")
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
                "-x",
                "--audio-format", "mp3",
                "--audio-quality", "0",
                "-o", output_file,
                "--embed-metadata",
                "--no-playlist",
                "--no-overwrites",
                "--no-continue",
                url
            ]
             
            result = subprocess.run(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=300
            )
             
            if result.returncode == 0 and os.path.exists(output_file):
                return True
            else:
                logger.error(f"Download error: {result.stderr}")
                return False
        except Exception as e:
            logger.error(f"Download error: {str(e)}")
            return False

    def get_current_time(self):
        """Mendapatkan waktu pemutaran saat ini"""
        return self.status.position_formatted
         
    def get_duration(self):
        """Get formatted duration of current track"""
        return self.status.duration_formatted
         
    def get_progress_percentage(self):
        """Get playback progress as percentage (0-100)"""
        return self.status.progress_percentage
         
    def get_volume(self):
        """Get current volume (0-100)"""
        return self.status.volume
 
    def is_paused(self):
        """Check if playback is paused"""
        return self.status.paused and self.is_playing()

    def is_playing(self):
        """Cek apakah sedang memutar lagu"""
        return self.is_running and self.status.playing and self.process and self.process.poll() is None
        
    def is_streaming(self):
        """Check if currently playing from stream vs local file"""
        return self.status.is_stream
         
    def toggle_auto_download(self):
        """Toggle mode auto-download"""
        self.auto_download = not self.auto_download
        return self.auto_download
         
    def is_auto_download(self):
        """Cek apakah mode auto-download aktif"""
        return self.auto_download
