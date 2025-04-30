from playlist_manager import PlaylistManager
from player import MusicPlayer
from ui import UI
import time
import threading
import os
import queue
import functools

# Define event types for event-driven architecture
EVENT_PLAYBACK_ENDED = "playback_ended"
EVENT_PLAYBACK_STARTED = "playback_started"
EVENT_DOWNLOAD_COMPLETED = "download_completed"
EVENT_OPERATION_COMPLETED = "operation_completed"
EVENT_ERROR = "error"

class TerminalMusicPlayerApp:
    """Main application class using event-driven architecture"""
    
    def __init__(self):
        self.playlist_manager = PlaylistManager()
        self.player = MusicPlayer()
        self.ui = UI()
        
        # Application state
        self.current_index = 0
        self.is_running = True
        self.downloaded_songs = {}
        self.event_queue = queue.Queue()
        
        # Load downloaded songs cache
        self._load_downloaded_songs()
    
    def _load_downloaded_songs(self):
        """Load cache of previously downloaded songs"""
        songs = self.playlist_manager.get_songs()
        if os.path.exists("downloads"):
            for song in songs:
                safe_title = "".join([c if c.isalnum() or c in [' ', '-', '_'] else '_' for c in song["title"]])
                potential_file = f"downloads/{safe_title}.mp3"
                if os.path.exists(potential_file):
                    self.downloaded_songs[song["url"]] = potential_file
        
        # Create downloads directory if it doesn't exist
        if not os.path.exists("downloads"):
            os.makedirs("downloads")
    
    def run(self):
        """Main application loop using event-driven approach"""
        # Start with initial UI render
        self._update_ui()
        
        # Main event loop
        while self.is_running:
            try:
                # Process any pending events
                self._process_events()
                
                # Get user command with short timeout for responsiveness
                command = self.ui.get_command(timeout=0.3)
                if command:
                    self._handle_command(command)
                
                # Update UI after each command or timeout
                self._update_ui()
                
            except KeyboardInterrupt:
                self.is_running = False
            except Exception as e:
                self.ui.add_message(f"Error: {e}", error=True)
        
        # Clean up before exit
        if self.player.is_playing():
            self.player.stop()
    
    def _process_events(self):
        """Process all pending events from the event queue"""
        try:
            # Process all available events without blocking
            while not self.event_queue.empty():
                event_type, event_data = self.event_queue.get_nowait()
                self._handle_event(event_type, event_data)
                self.event_queue.task_done()
        except queue.Empty:
            pass
    
    def _handle_event(self, event_type, event_data):
        """Handle events from the event queue"""
        if event_type == EVENT_PLAYBACK_ENDED:
            # Auto advance to next song
            self.current_index = self.playlist_manager.get_next_song_index(self.current_index)
            songs = self.playlist_manager.get_songs()
            if songs and self.current_index < len(songs):
                self.ui.add_message(f"Lagu selesai: '{songs[event_data]['title']}'")
                self._play_song(self.current_index)
        
        elif event_type == EVENT_PLAYBACK_STARTED:
            song_title = event_data.get("title", "Unknown")
            self.ui.add_message(f"Memutar: {song_title}")
            
        elif event_type == EVENT_DOWNLOAD_COMPLETED:
            success, song_url, filename, title = event_data
            if success:
                self.downloaded_songs[song_url] = filename
                self.ui.add_message(f"Download berhasil: {title}")
            else:
                self.ui.add_message(f"Download gagal: {title}", error=True)
                
        elif event_type == EVENT_OPERATION_COMPLETED:
            message = event_data.get("message", "Operasi selesai")
            error = event_data.get("error", False)
            self.ui.add_message(message, error=error)
            
        elif event_type == EVENT_ERROR:
            self.ui.add_message(f"Error: {event_data}", error=True)
    
    def _update_ui(self):
        """Update UI based on current state"""
        songs = self.playlist_manager.get_songs()
        
        if self.player.is_playing() and self.current_index < len(songs):
            current_song = songs[self.current_index]
            playback_source = "LOKAL" if current_song["url"] in self.downloaded_songs else "STREAM"
            
            # Render playing state
            self.ui.render_playing_state(
                songs, 
                self.current_index,
                self.playlist_manager.is_shuffle_mode(),
                self.player.get_current_time(),
                current_song,
                playback_source,
                self.player.is_auto_download(),
                len(self.downloaded_songs),
                len(songs)
            )
        else:
            # Render idle state
            self.ui.render_idle_state(
                songs,
                self.current_index,
                self.playlist_manager.is_shuffle_mode(),
                self.player.is_auto_download(),
                len(self.downloaded_songs),
            )
    
    def _handle_command(self, command):
        """Handle user commands"""
        songs = self.playlist_manager.get_songs()
        
        # Handle numeric input (direct song selection)
        if command.isdigit():
            selected_index = int(command) - 1
            if 0 <= selected_index < len(songs):
                if self.player.is_playing():
                    self.player.stop()
                self.current_index = selected_index
                self.ui.add_message(f"Lagu dipilih: {songs[self.current_index]['title']}")
            else:
                self.ui.add_message("Nomor lagu tidak valid", error=True)
            return
            
        # Handle commands
        command_handlers = {
            'q': self._cmd_quit,
            'p': self._cmd_play,
            's': self._cmd_stop,
            'n': self._cmd_next,
            'prev': self._cmd_prev,
            'r': self._cmd_toggle_shuffle,
            'a': self._cmd_add_song,
            'e': self._cmd_edit_song,
            'd': self._cmd_delete_song,
            'i': self._cmd_get_song_info,
            'save': self._cmd_save_playlist,
            'dl': self._cmd_download_current,
            'auto': self._cmd_toggle_auto_download,
            'dla': self._cmd_download_all,
            'pause': self._cmd_pause,  # New command for pause/resume
        }
        
        handler = command_handlers.get(command)
        if handler:
            handler()
        else:
            self.ui.add_message(f"Perintah tidak dikenal: {command}", error=True)
    
    def _cmd_quit(self):
        """Quit the application"""
        if self.player.is_playing():
            self.player.stop()
        self.is_running = False
    
    def _cmd_play(self):
        """Play current song"""
        songs = self.playlist_manager.get_songs()
        if songs and self.current_index < len(songs):
            self._play_song(self.current_index)
        else:
            self.ui.add_message("Tidak ada lagu dalam playlist", error=True)
    
    def _cmd_stop(self):
        """Stop playback"""
        if self.player.is_playing():
            self.player.stop()
            self.ui.add_message("Pemutaran dihentikan")
        else:
            self.ui.add_message("Tidak ada lagu yang sedang diputar", error=True)
    
    def _cmd_next(self):
        """Skip to next song"""
        songs = self.playlist_manager.get_songs()
        if songs:
            if self.player.is_playing():
                self.player.stop()
            self.current_index = self.playlist_manager.get_next_song_index(self.current_index)
            self.ui.add_message(f"Lagu dipindahkan ke: {songs[self.current_index]['title']}")
        else:
            self.ui.add_message("Tidak ada lagu dalam playlist", error=True)
    
    def _cmd_prev(self):
        """Go to previous song"""
        songs = self.playlist_manager.get_songs()
        if songs:
            if self.player.is_playing():
                self.player.stop()
            self.current_index = self.playlist_manager.get_prev_song_index(self.current_index)
            self.ui.add_message(f"Lagu dipindahkan ke: {songs[self.current_index]['title']}")
        else:
            self.ui.add_message("Tidak ada lagu dalam playlist", error=True)
    
    def _cmd_toggle_shuffle(self):
        """Toggle shuffle mode"""
        is_shuffle = self.playlist_manager.toggle_shuffle()
        self.ui.add_message(f"Mode shuffle {'AKTIF' if is_shuffle else 'NONAKTIF'}")
    
    def _cmd_add_song(self):
        """Add a new song to the playlist"""
        if self.player.is_playing():
            self.player.stop()
        
        # Show form in processing state
        self.ui.render_processing_state("Tambah Lagu Baru")
        title, artist, url, duration = self.ui.add_song_form()
        
        if title and url:
            # If duration not provided, try to fetch it
            if duration == "Unknown":
                self.ui.add_message("Mengambil informasi lagu... Mohon tunggu.")
                # Use async worker to fetch duration
                self._run_in_background(
                    self._fetch_song_info,
                    url,
                    lambda song_info: self._add_song_after_fetch(title, artist, url, song_info)
                )
            else:
                # Add song directly if duration is provided
                self.current_index = self.playlist_manager.add_song(title, artist, url, duration)
                self.ui.add_message(f"Lagu '{title}' berhasil ditambahkan")
    
    def _add_song_after_fetch(self, title, artist, url, song_info):
        """Add song after fetching metadata"""
        duration = song_info["duration"]
        self.current_index = self.playlist_manager.add_song(title, artist, url, duration)
        self.ui.add_message(f"Lagu '{title}' berhasil ditambahkan dengan durasi: {duration}")
    
    def _cmd_edit_song(self):
        """Edit the current song"""
        songs = self.playlist_manager.get_songs()
        if songs and self.current_index < len(songs):
            if self.player.is_playing():
                self.player.stop()
            
            song = songs[self.current_index]
            title, artist, url, duration = self.ui.edit_song_form(song)
            success, message = self.playlist_manager.update_song(self.current_index, title, artist, url, duration)
            self.ui.add_message(message, error=not success)
        else:
            self.ui.add_message("Tidak ada lagu yang dipilih", error=True)
    
    def _cmd_delete_song(self):
        """Delete the current song"""
        songs = self.playlist_manager.get_songs()
        if songs and self.current_index < len(songs):
            if self.player.is_playing():
                self.player.stop()
            
            song = songs[self.current_index]
            if self.ui.confirm_delete(song):
                success, message = self.playlist_manager.delete_song(self.current_index)
                songs = self.playlist_manager.get_songs()
                if songs:
                    self.current_index = min(self.current_index, len(songs) - 1)
                else:
                    self.current_index = 0
                self.ui.add_message(message, error=not success)
        else:
            self.ui.add_message("Tidak ada lagu yang dipilih", error=True)
    
    def _cmd_get_song_info(self):
        """Get and update song info from the internet"""
        songs = self.playlist_manager.get_songs()
        if songs and self.current_index < len(songs):
            url = songs[self.current_index]["url"]
            self.ui.add_message("Mengambil informasi lagu... Mohon tunggu.")
            
            # Use async worker to fetch song info
            self._run_in_background(
                self._fetch_song_info,
                url,
                lambda song_info: self._update_song_info(song_info)
            )
        else:
            self.ui.add_message("Tidak ada lagu yang dipilih", error=True)
    
    def _update_song_info(self, song_info):
        """Update song with fetched info"""
        songs = self.playlist_manager.get_songs()
        if songs and self.current_index < len(songs):
            self.playlist_manager.update_song(
                self.current_index, 
                None, 
                None, 
                None, 
                song_info["duration"]
            )
            self.ui.add_message(f"Informasi lagu berhasil diperbarui: {song_info['duration']}")
    
    def _cmd_save_playlist(self):
        """Save the playlist to disk"""
        success, message = self.playlist_manager.save_playlist()
        self.ui.add_message(message, error=not success)
    
    def _cmd_download_current(self):
        """Download the current song"""
        songs = self.playlist_manager.get_songs()
        if songs and self.current_index < len(songs):
            song = songs[self.current_index]
            
            # Show downloading message
            self.ui.add_message(f"Mendownload: {song['title']}... Mohon tunggu.")
            
            # Download in background
            self._run_in_background(
                self._download_song,
                song["url"],
                song["title"],
                lambda result: self._handle_download_result(result, song["url"], song["title"])
            )
        else:
            self.ui.add_message("Tidak ada lagu yang dipilih", error=True)
    
    def _handle_download_result(self, result, url, title):
        """Handle download completion"""
        success, filename = result
        self.event_queue.put((
            EVENT_DOWNLOAD_COMPLETED, 
            (success, url, filename, title)
        ))
    
    def _cmd_toggle_auto_download(self):
        """Toggle auto-download mode"""
        is_auto = self.player.toggle_auto_download()
        self.ui.add_message(f"Mode auto-download {'AKTIF' if is_auto else 'NONAKTIF'}")
    
    def _cmd_download_all(self):
        """Download all songs in the playlist"""
        songs = self.playlist_manager.get_songs()
        if not songs:
            self.ui.add_message("Tidak ada lagu dalam playlist", error=True)
            return
            
        self.ui.add_message(f"Mendownload {len(songs)} lagu... Mohon tunggu.")
        
        # Use background thread to download all songs
        self._run_in_background(
            self._download_all_songs,
            songs,
            lambda result: self._handle_download_all_result(result)
        )
    
    def _download_all_songs(self, songs):
        """Background task to download all songs"""
        success_count = 0
        results = []
        
        for i, song in enumerate(songs):
            # Update progress through event queue
            self.event_queue.put((
                EVENT_OPERATION_COMPLETED, 
                {"message": f"Mendownload [{i+1}/{len(songs)}]: {song['title']}..."}
            ))
            
            # Download song
            result, filename = self._download_song(song["url"], song["title"])
            if result:
                success_count += 1
                results.append((song["url"], filename))
            
            # Small delay to allow UI updates
            time.sleep(0.1)
            
        return success_count, len(songs), results
    
    def _handle_download_all_result(self, result):
        """Handle completion of downloading all songs"""
        success_count, total_count, download_results = result
        
        # Update downloaded_songs dictionary
        for url, filename in download_results:
            self.downloaded_songs[url] = filename
            
        self.ui.add_message(f"Berhasil mendownload {success_count} dari {total_count} lagu")
        
    def _cmd_pause(self):
        """Pause or resume playback"""
        if self.player.is_playing():
            if self.player.is_paused():
                self.player.resume()
                self.ui.add_message("Pemutaran dilanjutkan")
            else:
                self.player.pause()
                self.ui.add_message("Pemutaran dijeda")
        else:
            self.ui.add_message("Tidak ada lagu yang sedang diputar", error=True)
    
    def _play_song(self, index):
        """Play a song with auto-download if needed"""
        songs = self.playlist_manager.get_songs()
        if index < len(songs):
            song = songs[index]
            song_url = song["url"]
            
            # Check if song is already downloaded
            filename = self.downloaded_songs.get(song_url)
            
            # Auto-download if enabled and song is not downloaded yet
            if self.player.is_auto_download() and not filename:
                self.ui.add_message(f"Auto-download: {song['title']}... Mohon tunggu.")
                self.ui.render_processing_state(f"Mendownload: {song['title']}")
                
                # Download in background then play
                self._run_in_background(
                    self._download_song,
                    song_url,
                    song["title"],
                    lambda result: self._play_after_download(result, index, song)
                )
            else:
                # Play directly
                self._play_now(index, filename)
    
    def _play_after_download(self, result, index, song):
        """Play song after download completes"""
        success, filename = result
        song_url = song["url"]
        
        if success:
            self.downloaded_songs[song_url] = filename
            self._play_now(index, filename)
        else:
            # Fall back to streaming if download fails
            self.ui.add_message(f"Download gagal, streaming: {song['title']}")
            self._play_now(index, None)
    
    def _play_now(self, index, filename=None):
        """Play song either from file or by streaming"""
        songs = self.playlist_manager.get_songs()
        if index < len(songs):
            song = songs[index]
            song_url = song["url"]
            
            # Setup callback for when song finishes
            def on_song_complete():
                self.event_queue.put((EVENT_PLAYBACK_ENDED, index))
            
            # Play from local file if available, otherwise stream
            if filename and os.path.exists(filename):
                success, message = self.player.play(filename, on_song_complete, local=True)
                source = "LOKAL"
            else:
                success, message = self.player.play(song_url, on_song_complete)
                source = "STREAM"
                
            if success:
                self.event_queue.put((
                    EVENT_PLAYBACK_STARTED, 
                    {"title": song["title"], "source": source}
                ))
            else:
                self.event_queue.put((EVENT_ERROR, message))
    
    def _download_song(self, url, title):
        """Download a song using yt-dlp"""
        try:
            # Create a safe filename
            safe_title = "".join([c if c.isalnum() or c in [' ', '-', '_'] else '_' for c in title])
            filename = f"downloads/{safe_title}.mp3"
            
            # Check if file already exists
            if os.path.exists(filename):
                return True, filename
                
            # Download the song
            result = self.player.download_song(url, filename)
            return result, filename
        except Exception as e:
            return False, None
    
    def _fetch_song_info(self, url):
        """Fetch song information from URL"""
        return self.player.get_song_info(url)
    
    def _run_in_background(self, task_func, *args, callback=None):
        """Run a task in background thread with optional callback"""
        def _background_task():
            try:
                result = task_func(*args)
                if callback:
                    callback(result)
            except Exception as e:
                self.event_queue.put((EVENT_ERROR, str(e)))
        
        thread = threading.Thread(target=_background_task)
        thread.daemon = True
        thread.start()

def main():
    try:
        app = TerminalMusicPlayerApp()
        app.run()
    except KeyboardInterrupt:
        print("\nProgram dihentikan.")
    except Exception as e:
        print(f"\nTerjadi kesalahan: {e}")

if __name__ == "__main__":
    main()
