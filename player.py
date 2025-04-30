import subprocess
import json
import time
import threading
import re
import os
import socket
import tempfile
import random
from queue import Queue, Empty
from typing import Optional, Dict, Any, List, Callable, Tuple

class MusicPlayer:
    """
    Enhanced Music Player with advanced controls and features
    - Uses MPV's JSON IPC for communication instead of stdout polling
    - Supports pause/resume, seek, volume adjustment
    - Provides real-time playback statistics
    - Detects end-of-file events via subscriptions
    - Supports audio visualization
    """
    def __init__(self):
        self.process = None
        self.current_time = "00:00"
        self.duration = "00:00"
        self.volume = 100
        self.is_running = False
        self.is_paused = False
        self.socket_path = None
        self.ipc_socket = None
        self.command_queue = Queue()
        self.response_queue = Queue()
        self.monitor_thread = None
        self.command_thread = None
        self.request_id = 1
        self.auto_next_callback = None
        self.auto_download = False
        self.visualizer_enabled = False
        self.visualizer_mode = "spectrum"  # spectrum, wave, or bars
        self.visualizer_data = []
        self.visualizer_thread = None
        self.event_handlers = {}
        self.playback_stats = {
            "position": 0.0,
            "duration": 0.0,
            "percent_pos": 0.0,
            "cache_used": 0.0,
            "cache_size": 0.0,
            "bitrate": 0,
            "volume": 100.0,
            "metadata": {},
            "filename": "",
            "path": ""
        }

    def play(self, url, auto_next_callback=None, local=False):
        """Play audio from URL or local file using MPV with JSON IPC"""
        try:
            self.stop()  # Stop previous playback if any
            self.auto_next_callback = auto_next_callback
            
            # Create a temporary socket file for IPC
            self.socket_path = os.path.join(tempfile.gettempdir(), f"mpv_socket_{random.randint(1000, 9999)}")
            
            # Prepare MPV command with optimized settings and IPC socket
            command = [
                "mpv", 
                "--no-video", 
                "--audio-display=no", 
                "--sub-auto=no",
                "--input-ipc-server=" + self.socket_path,  # Use JSON IPC socket
                "--idle=yes",           # Remain in idle state after playback
                "--cache=yes",          # Enable cache
                "--cache-secs=30",      # Cache 30 seconds ahead
                "--demuxer-readahead-secs=5",  # Read 5 seconds ahead
                "--keep-open=always",   # Keep mpv running after EOF
                "--force-window=no"     # No visible window
            ]
            
            if not local:
                # Add best audio format options for streaming
                command.extend([
                    "--ytdl-format=bestaudio",
                    "--ytdl-raw-options=format-sort=+codec:aac"
                ])
            
            command.append(url)  # Add URL or file path
            
            # Start MPV process
            self.process = subprocess.Popen(
                command,
                stdout=subprocess.DEVNULL,  # Don't need to parse stdout anymore
                stderr=subprocess.PIPE,     # Only capture stderr for error logging
                text=True
            )
            
            # Wait for socket to be available
            retry_count = 0
            while not os.path.exists(self.socket_path) and retry_count < 50:
                time.sleep(0.1)
                retry_count += 1
                
            if not os.path.exists(self.socket_path):
                return False, "Failed to establish IPC connection with MPV"
                
            # Connect to the IPC socket
            self.ipc_socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            self.ipc_socket.connect(self.socket_path)
            self.ipc_socket.settimeout(0.5)  # Short timeout for responsive UI
            
            # Set initial state
            self.is_running = True
            self.is_paused = False
            self.current_time = "00:00"
            
            # Start command thread to handle sending commands
            self.command_thread = threading.Thread(target=self._command_handler)
            self.command_thread.daemon = True
            self.command_thread.start()
            
            # Start monitor thread to receive responses
            self.monitor_thread = threading.Thread(target=self._monitor_playback)
            self.monitor_thread.daemon = True
            self.monitor_thread.start()
            
            # Subscribe to important events
            self._subscribe_to_events()
            
            # Start fetching initial playback data
            self._update_playback_stats()
            
            # Start visualizer if enabled
            if self.visualizer_enabled:
                self._start_visualizer()
                
            return True, ""
            
        except FileNotFoundError:
            return False, "Error: MPV not found. Please ensure MPV is installed on your system."
        except Exception as e:
            return False, f"Error playing audio: {e}"

    def _command_handler(self):
        """Thread to handle sending commands to MPV"""
        while self.is_running and self.ipc_socket:
            try:
                # Get command from queue or wait for 0.1 seconds
                try:
                    command, callback = self.command_queue.get(timeout=0.1)
                    
                    # Send command to MPV
                    command_json = json.dumps(command) + "\n"
                    self.ipc_socket.sendall(command_json.encode('utf-8'))
                    
                    # Store callback if provided
                    if callback:
                        self.event_handlers[command.get('request_id', 0)] = callback
                        
                    self.command_queue.task_done()
                except Empty:
                    # No command in queue, continue loop
                    continue
                    
            except Exception as e:
                # Log error and continue
                print(f"Command handler error: {e}")
                time.sleep(0.1)
                
    def _monitor_playback(self):
        """Thread to monitor MPV responses and events"""
        buffer = ""
        
        while self.is_running and self.ipc_socket:
            try:
                # Receive data from socket
                try:
                    data = self.ipc_socket.recv(4096).decode('utf-8')
                    if not data:
                        # Connection closed
                        if self.is_running:
                            self.stop()
                        break
                        
                    # Add data to buffer
                    buffer += data
                    
                    # Process complete JSON objects
                    while '\n' in buffer:
                        line, buffer = buffer.split('\n', 1)
                        try:
                            response = json.loads(line)
                            self._handle_mpv_response(response)
                        except json.JSONDecodeError:
                            # Invalid JSON, discard
                            pass
                            
                except socket.timeout:
                    # Socket timeout, continue loop
                    continue
                    
                # Check playback status periodically
                if self.is_running and not self.is_paused:
                    self._update_playback_stats()
                    
                # Short sleep to prevent CPU hogging
                time.sleep(0.05)
                
            except Exception as e:
                # Log error and continue
                print(f"Monitor error: {e}")
                time.sleep(0.1)
                
        # Clean up when monitoring stops
        if self.auto_next_callback and self.is_running:
            self.is_running = False
            self.auto_next_callback()

    def _handle_mpv_response(self, response):
        """Handle responses from MPV"""
        # Handle event messages
        if 'event' in response:
            event_name = response['event']
            
            # Handle end-file event
            if event_name == 'end-file':
                reason = response.get('reason', '')
                # Only trigger auto-next if playback ended naturally (not by user)
                if reason == 'eof' and self.auto_next_callback and self.is_running:
                    self.auto_next_callback()
                    
            # Handle property changes
            elif event_name == 'property-change':
                prop = response.get('name', '')
                value = response.get('data')
                
                if prop == 'time-pos' and value is not None:
                    # Update current position
                    self.playback_stats['position'] = value
                    minutes = int(value) // 60
                    seconds = int(value) % 60
                    self.current_time = f"{minutes:02d}:{seconds:02d}"
                    
                elif prop == 'duration' and value is not None:
                    # Update duration
                    self.playback_stats['duration'] = value
                    minutes = int(value) // 60
                    seconds = int(value) % 60
                    self.duration = f"{minutes:02d}:{seconds:02d}"
                    
                elif prop == 'percent-pos' and value is not None:
                    self.playback_stats['percent_pos'] = value
                    
                elif prop == 'metadata' and value is not None:
                    self.playback_stats['metadata'] = value
                    
                elif prop == 'volume' and value is not None:
                    self.playback_stats['volume'] = value
                    self.volume = int(value)
                    
        # Handle command responses
        elif 'request_id' in response:
            request_id = response['request_id']
            
            # Process callback if registered
            if request_id in self.event_handlers:
                callback = self.event_handlers.pop(request_id)
                callback(response)

    def _subscribe_to_events(self):
        """Subscribe to MPV events and property changes"""
        # Subscribe to end-file event
        self._send_command({
            "command": ["observe_property", 1, "time-pos"]
        })
        
        self._send_command({
            "command": ["observe_property", 2, "duration"]
        })
        
        self._send_command({
            "command": ["observe_property", 3, "percent-pos"]
        })
        
        self._send_command({
            "command": ["observe_property", 4, "metadata"]
        })
        
        self._send_command({
            "command": ["observe_property", 5, "volume"]
        })
        
        # Enable events
        self._send_command({
            "command": ["request_event", "end-file", True]
        })

    def _send_command(self, command, callback=None):
        """Send command to MPV"""
        if not self.is_running or not self.ipc_socket:
            return
            
        # Add request ID if not present
        if 'request_id' not in command:
            command['request_id'] = self.request_id
            self.request_id += 1
            
        # Add to command queue
        self.command_queue.put((command, callback))
        
    def _update_playback_stats(self):
        """Update playback statistics"""
        if not self.is_running:
            return
            
        # Get current playback position
        self._send_command({
            "command": ["get_property", "time-pos"]
        })
        
        # Get audio stats
        self._send_command({
            "command": ["get_property", "audio-bitrate"]
        }, lambda resp: self._update_stat('bitrate', resp.get('data')))
        
        # Get cache stats
        self._send_command({
            "command": ["get_property", "cache-used"]
        }, lambda resp: self._update_stat('cache_used', resp.get('data')))
        
        self._send_command({
            "command": ["get_property", "cache-size"]
        }, lambda resp: self._update_stat('cache_size', resp.get('data')))

    def _update_stat(self, stat_name, value):
        """Update a specific playback stat"""
        if value is not None:
            self.playback_stats[stat_name] = value

    def pause(self):
        """Toggle pause/resume playback"""
        if not self.is_running:
            return False
            
        self._send_command({
            "command": ["cycle", "pause"]
        })
        
        self.is_paused = not self.is_paused
        return True

    def seek(self, offset):
        """Seek forward/backward by offset seconds"""
        if not self.is_running:
            return False
            
        self._send_command({
            "command": ["seek", offset]
        })
        
        return True

    def set_volume(self, volume):
        """Set volume (0-100)"""
        if not self.is_running:
            return False
            
        # Ensure volume is within valid range
        volume = max(0, min(100, volume))
        
        self._send_command({
            "command": ["set_property", "volume", volume]
        })
        
        self.volume = volume
        return True

    def adjust_volume(self, delta):
        """Adjust volume by delta"""
        return self.set_volume(self.volume + delta)

    def stop(self):
        """Stop playback"""
        # Set flags to stop threads
        self.is_running = False
        
        # Stop visualizer if running
        if self.visualizer_thread and self.visualizer_thread.is_alive():
            self.visualizer_enabled = False
            try:
                self.visualizer_thread.join(0.5)
            except:
                pass
                
        # Close socket connection
        if self.ipc_socket:
            try:
                self._send_command({
                    "command": ["quit"]
                })
                time.sleep(0.1)  # Give time for quit command to be processed
                self.ipc_socket.close()
            except:
                pass
            self.ipc_socket = None
                
        # Terminate MPV process
        if self.process and self.process.poll() is None:
            try:
                self.process.terminate()
                try:
                    self.process.wait(timeout=1)
                except subprocess.TimeoutExpired:
                    self.process.kill()
            except:
                pass
                
        # Wait for monitor thread to finish
        if self.monitor_thread and self.monitor_thread.is_alive():
            try:
                self.monitor_thread.join(0.5)
            except:
                pass
                
        # Wait for command thread to finish
        if self.command_thread and self.command_thread.is_alive():
            try:
                self.command_thread.join(0.5)
            except:
                pass
                
        # Remove socket file
        if self.socket_path and os.path.exists(self.socket_path):
            try:
                os.unlink(self.socket_path)
            except:
                pass
                
        # Reset state
        self.current_time = "00:00"
        self.duration = "00:00"
        self.volume = 100
        self.is_paused = False

    def get_song_info(self, url):
        """Get song info from URL using yt-dlp"""
        try:
            result = subprocess.run(
                ["yt-dlp", "--dump-json", "--no-warnings", "--no-simulate", url],
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                text=True,
                timeout=15  # Add timeout to prevent hanging
            )
            
            if result.returncode != 0:
                return {
                    "duration": "Unknown",
                    "title": "Unknown Title",
                    "uploader": "Unknown Artist",
                    "error": True
                }
                
            info = json.loads(result.stdout)
            
            # Extract duration
            duration_seconds = int(info.get("duration", 0))
            minutes = duration_seconds // 60
            seconds = duration_seconds % 60
            duration = f"{minutes:02d}:{seconds:02d}"
            
            # Extract more metadata
            return {
                "duration": duration,
                "duration_seconds": duration_seconds,
                "title": info.get("title", "Unknown Title"),
                "uploader": info.get("uploader", "Unknown Artist"),
                "thumbnail": info.get("thumbnail", ""),
                "upload_date": info.get("upload_date", ""),
                "view_count": info.get("view_count", 0),
                "like_count": info.get("like_count", 0),
                "format": info.get("format", "Unknown Format"),
                "error": False
            }
        except subprocess.TimeoutExpired:
            return {
                "duration": "Unknown",
                "title": "Unknown Title",
                "uploader": "Unknown Artist",
                "error": True,
                "error_msg": "Request timed out"
            }
        except Exception as e:
            return {
                "duration": "Unknown",
                "title": "Unknown Title",
                "uploader": "Unknown Artist",
                "error": True,
                "error_msg": str(e)
            }
            
    def download_song(self, url, output_file, progress_callback=None):
        """Download song using yt-dlp with progress updates"""
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(os.path.abspath(output_file)), exist_ok=True)
            
            # Prepare command
            command = [
                "yt-dlp", 
                "-x",                         # Extract audio
                "--audio-format", "mp3",      # Convert to mp3
                "--audio-quality", "0",       # Best quality
                "-o", output_file,            # Output file
                "--embed-metadata",           # Embed metadata
                "--embed-thumbnail",          # Embed thumbnail
                "--no-playlist",              # Don't download playlist
                "--no-overwrites",            # Don't overwrite existing files
                "--progress",                 # Show progress
                url                           # URL to download
            ]
            
            # Start process
            process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            
            # Process output for progress updates
            for line in process.stdout:
                # Parse progress info
                if progress_callback and "[download]" in line and "%" in line:
                    try:
                        # Extract percentage from line like: "[download]  50.0% of 5.20MiB at 500KiB/s ETA 00:05"
                        percent_match = re.search(r'(\d+\.\d+)%', line)
                        if percent_match:
                            progress = float(percent_match.group(1))
                            progress_callback(progress)
                    except:
                        pass
                        
            # Wait for process to finish
            return_code = process.wait()
            
            # Check if download was successful
            if return_code == 0 and os.path.exists(output_file):
                # Send 100% progress if successful
                if progress_callback:
                    progress_callback(100.0)
                return True
            else:
                return False
                
        except Exception as e:
            print(f"Download error: {str(e)}")
            return False

    def toggle_visualizer(self):
        """Toggle audio visualizer on/off"""
        self.visualizer_enabled = not self.visualizer_enabled
        
        if self.visualizer_enabled:
            self._start_visualizer()
        elif self.visualizer_thread and self.visualizer_thread.is_alive():
            self.visualizer_thread.join(0.5)
            
        return self.visualizer_enabled
        
    def cycle_visualizer_mode(self):
        """Cycle through visualizer modes"""
        modes = ["spectrum", "wave", "bars"]
        current_index = modes.index(self.visualizer_mode)
        self.visualizer_mode = modes[(current_index + 1) % len(modes)]
        return self.visualizer_mode
        
    def _start_visualizer(self):
        """Start audio visualizer thread"""
        if self.visualizer_thread and self.visualizer_thread.is_alive():
            return
            
        self.visualizer_thread = threading.Thread(target=self._visualizer_loop)
        self.visualizer_thread.daemon = True
        self.visualizer_thread.start()
        
    def _visualizer_loop(self):
        """Audio visualizer loop - simulates a terminal-based audio visualizer"""
        # In a real implementation, this would analyze audio data from MPV
        # For this example, we'll simulate visualization data
        while self.is_running and self.visualizer_enabled:
            try:
                if self.is_paused:
                    time.sleep(0.1)
                    continue
                    
                # Get audio data for visualization
                # In a real implementation, this would get data from MPV's audio buffer
                # For this example, we'll generate random data
                self._update_visualizer_data()
                
                # Sleep to control visualization frame rate
                time.sleep(0.05)
                
            except Exception as e:
                print(f"Visualizer error: {e}")
                time.sleep(0.1)
                
    def _update_visualizer_data(self):
        """Update visualizer data based on current audio"""
        # In a real implementation, this would analyze audio data
        # For this example, we'll generate random data
        
        if self.visualizer_mode == "spectrum":
            # Generate spectrum data (frequency analysis)
            # Real implementation would use FFT
            self.visualizer_data = [random.randint(0, 15) for _ in range(32)]
            
        elif self.visualizer_mode == "wave":
            # Generate waveform data
            self.visualizer_data = [random.randint(-7, 7) for _ in range(60)]
            
        elif self.visualizer_mode == "bars":
            # Generate bar equalizer data
            self.visualizer_data = [random.randint(0, 10) for _ in range(16)]
    
    def get_visualizer_data(self):
        """Get current visualizer data"""
        return {
            "mode": self.visualizer_mode,
            "data": self.visualizer_data,
            "enabled": self.visualizer_enabled
        }
        
    def toggle_auto_download(self):
        """Toggle auto-download mode"""
        self.auto_download = not self.auto_download
        return self.auto_download
        
    def is_auto_download(self):
        """Check if auto-download is enabled"""
        return self.auto_download
        
    def get_current_time(self):
        """Get current playback time"""
        return self.current_time
        
    def get_duration(self):
        """Get total duration"""
        return self.duration
        
    def get_volume(self):
        """Get current volume"""
        return self.volume
        
    def is_playing(self):
        """Check if player is playing"""
        return self.is_running and self.process and self.process.poll() is None
        
    def is_paused_state(self):
        """Check if player is paused"""
        return self.is_running and self.is_paused
        
    def get_playback_stats(self):
        """Get all playback statistics"""
        return self.playback_stats
