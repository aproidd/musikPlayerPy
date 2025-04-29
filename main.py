from playlist_manager import PlaylistManager
from player import MusicPlayer
from ui import UI
import time
import threading
import os

def fetch_all_durations(playlist_manager, player):
    """Fetch all missing durations at startup"""
    songs = playlist_manager.get_songs()
    updated = False

    for i, song in enumerate(songs):
        if "duration" not in song or song["duration"] == "Unknown":
            print(f"Mengambil durasi untuk: {song['title']}...")
            song_info = player.get_song_info(song["url"])
            if song_info["duration"] != "Unknown":
                playlist_manager.update_song(i, None, None, None, song_info["duration"])
                updated = True

    if updated:
        playlist_manager.save_playlist()

    return playlist_manager.get_songs()

def download_song(player, url, title):
    """Download a song using yt-dlp"""
    try:
        # Create downloads directory if it doesn't exist
        if not os.path.exists("downloads"):
            os.makedirs("downloads")
            
        # Buat nama file yang aman
        safe_title = "".join([c if c.isalnum() or c in [' ', '-', '_'] else '_' for c in title])
        filename = f"downloads/{safe_title}.mp3"
        
        # Check if file already exists
        if os.path.exists(filename):
            return True, filename
            
        result = player.download_song(url, filename)
        return result, filename
    except Exception as e:
        print(f"Error saat mendownload: {e}")
        return False, None

def main():
    playlist_manager = PlaylistManager()
    player = MusicPlayer()
    ui = UI()
    
    # Fetch all durations at startup
    print("Memperbarui informasi durasi lagu...")
    songs = fetch_all_durations(playlist_manager, player)
    
    current_index = 0
    last_message = ""
    
    songs = playlist_manager.get_songs()
    
    # Cache untuk lagu yang sudah didownload
    downloaded_songs = {}
    
    # Cek file yang sudah didownload sebelumnya
    if os.path.exists("downloads"):
        for song in songs:
            safe_title = "".join([c if c.isalnum() or c in [' ', '-', '_'] else '_' for c in song["title"]])
            potential_file = f"downloads/{safe_title}.mp3"
            if os.path.exists(potential_file):
                downloaded_songs[song["url"]] = potential_file
    
    def auto_next():
        """Callback untuk pemutaran otomatis lagu berikutnya"""
        nonlocal current_index, last_message
        last_message = f"Lagu '{songs[current_index]['title']}' selesai diputar"
        current_index = playlist_manager.get_next_song_index(current_index)
        if songs and current_index < len(songs):
            play_song(current_index)
    
    def play_song(index):
        """Helper function to play a song with auto-download"""
        nonlocal last_message
        if index < len(songs):
            song = songs[index]
            song_url = song["url"]
            
            # Check if song is already downloaded
            filename = downloaded_songs.get(song_url)
            
            # If auto-download is enabled and song is not downloaded yet, download it
            if player.is_auto_download() and not filename:
                # Beri tahu pengguna bahwa download sedang berlangsung
                ui.clear_screen()
                ui.print_header()
                ui.print_playlist(songs, current_index, playlist_manager.is_shuffle_mode())
                ui.print_message(f"Mendownload: {song['title']}... Mohon tunggu.")
                
                success, filename = download_song(player, song_url, song["title"])
                if success:
                    downloaded_songs[song_url] = filename
                    last_message = f"Download berhasil, memutar: {song['title']}"
                else:
                    last_message = f"Download gagal, streaming: {song['title']}"
            
            # Play from local file if available, otherwise stream
            if filename and os.path.exists(filename):
                success, message = player.play(filename, auto_next, local=True)
                if not success:
                    last_message = message
            else:
                # Beri tahu pengguna bahwa streaming sedang dimulai
                ui.clear_screen()
                ui.print_header()
                ui.print_playlist(songs, current_index, playlist_manager.is_shuffle_mode())
                ui.print_message(f"Memulai streaming: {song['title']}... Mohon tunggu.")
                
                success, message = player.play(song_url, auto_next)
                if not success:
                    last_message = message
    
    # Thread untuk update tampilan
    def update_display_thread():
        while True:
            # Hanya update jika pemain sedang memutar
            if player.is_playing():
                ui.clear_screen()
                ui.print_header()
                ui.print_playlist(songs, current_index, playlist_manager.is_shuffle_mode())
                
                if player.is_playing() and current_index < len(songs):
                    ui.print_now_playing(songs[current_index], player.get_current_time())
                    # Tambahkan informasi tentang mode pemutaran
                    if songs[current_index]["url"] in downloaded_songs:
                        print("\n[LOKAL] Memutar dari file lokal")
                    else:
                        print("\n[STREAM] Memutar dari internet")
                
                if last_message:
                    ui.print_message(last_message)
                
                ui.print_controls()
                print("\nMenunggu lagu selesai atau ketik perintah baru...")
            
            # Jeda yang lebih seimbang untuk mengurangi CPU usage tapi tetap responsif
            time.sleep(0.3)  # Seimbang antara responsivitas dan overhead
    
    # Mulai thread update
    display_thread = threading.Thread(target=update_display_thread)
    display_thread.daemon = True
    display_thread.start()
    
    while True:
        ui.clear_screen()
        ui.print_header()
        ui.print_playlist(songs, current_index, playlist_manager.is_shuffle_mode())
        
        if player.is_playing() and current_index < len(songs):
            ui.print_now_playing(songs[current_index], player.get_current_time())
            # Tambahkan informasi tentang mode pemutaran
            if songs[current_index]["url"] in downloaded_songs:
                print("\n[LOKAL] Memutar dari file lokal")
            else:
                print("\n[STREAM] Memutar dari internet")
        
        if last_message:
            ui.print_message(last_message)
            last_message = ""
        
        ui.print_controls()
        ui.print_download_status(player.is_auto_download(), len(downloaded_songs), len(songs))
        
        command = ui.get_command()
        
        # Cek jika input adalah angka (pilih lagu langsung)
        if command.isdigit():
            selected_index = int(command) - 1  # Konversi nomor lagu ke indeks (dimulai dari 0)
            if 0 <= selected_index < len(songs):
                if player.is_playing():
                    player.stop()
                current_index = selected_index
                last_message = f"Lagu dipindahkan ke: {songs[current_index]['title']}"
            else:
                last_message = "Nomor lagu tidak valid"
        
        elif command == 'q':  # Quit
            if player.is_playing():
                player.stop()
            break
        
        elif command == 'p':  # Play
            if songs and current_index < len(songs):
                play_song(current_index)
            else:
                last_message = "Tidak ada lagu dalam playlist"
        
        elif command == 's':  # Stop
            if player.is_playing():
                player.stop()
                last_message = "Pemutaran dihentikan"
            else:
                last_message = "Tidak ada lagu yang sedang diputar"
        
        elif command == 'n':  # Next
            if songs:
                if player.is_playing():
                    player.stop()
                current_index = playlist_manager.get_next_song_index(current_index)
                last_message = f"Lagu dipindahkan ke: {songs[current_index]['title']}"
            else:
                last_message = "Tidak ada lagu dalam playlist"
        
        elif command == 'prev':  # Previous
            if songs:
                if player.is_playing():
                    player.stop()
                current_index = playlist_manager.get_prev_song_index(current_index)
                last_message = f"Lagu dipindahkan ke: {songs[current_index]['title']}"
                play_song(current_index)
            else:
                last_message = "Tidak ada lagu dalam playlist"
        
        elif command == 'r':  # Toggle shuffle
            is_shuffle = playlist_manager.toggle_shuffle()
            last_message = f"Mode shuffle {'AKTIF' if is_shuffle else 'NONAKTIF'}"
        
        elif command == 'a':  # Add song
            if player.is_playing():
                player.stop()
            
            title, artist, url, duration = ui.add_song_form()
            if title and url:
                # Jika durasi tidak dimasukkan, coba ambil dari internet
                if duration == "Unknown":
                    song_info = player.get_song_info(url)
                    duration = song_info["duration"]
                
                current_index = playlist_manager.add_song(title, artist, url, duration)
                songs = playlist_manager.get_songs()
                last_message = f"Lagu '{title}' berhasil ditambahkan"
        
        elif command == 'e':  # Edit song
            if songs and current_index < len(songs):
                if player.is_playing():
                    player.stop()
                
                song = songs[current_index]
                title, artist, url, duration = ui.edit_song_form(song)
                success, message = playlist_manager.update_song(current_index, title, artist, url, duration)
                songs = playlist_manager.get_songs()
                last_message = message
            else:
                last_message = "Tidak ada lagu yang dipilih"
        
        elif command == 'd':  # Delete song
            if songs and current_index < len(songs):
                if player.is_playing():
                    player.stop()
                
                song = songs[current_index]
                if ui.confirm_delete(song):
                    success, message = playlist_manager.delete_song(current_index)
                    songs = playlist_manager.get_songs()
                    if songs:
                        current_index = min(current_index, len(songs) - 1)
                    else:
                        current_index = 0
                    last_message = message
            else:
                last_message = "Tidak ada lagu yang dipilih"
        
        elif command == 'i':  # Get song info
            if songs and current_index < len(songs):
                url = songs[current_index]["url"]
                last_message = "Mengambil informasi lagu... Mohon tunggu."
                
                # Update tampilan untuk menampilkan pesan
                ui.clear_screen()
                ui.print_header()
                ui.print_playlist(songs, current_index, playlist_manager.is_shuffle_mode())
                ui.print_message(last_message)
                
                # Ambil info lagu
                song_info = player.get_song_info(url)
                
                # Update lagu dengan info baru
                playlist_manager.update_song(
                    current_index, 
                    None, 
                    None, 
                    None, 
                    song_info["duration"]
                )
                songs = playlist_manager.get_songs()
                last_message = f"Informasi lagu berhasil diperbarui: {song_info['duration']}"
            else:
                last_message = "Tidak ada lagu yang dipilih"
        
        elif command == 'save':  # Save playlist
            success, message = playlist_manager.save_playlist()
            last_message = message
            
        elif command == 'dl':  # Download current song
            if songs and current_index < len(songs):
                song = songs[current_index]
                
                # Tampilkan pesan download sedang berlangsung
                ui.clear_screen()
                ui.print_header()
                ui.print_playlist(songs, current_index, playlist_manager.is_shuffle_mode())
                ui.print_message(f"Mendownload: {song['title']}... Mohon tunggu.")
                
                success, filename = download_song(player, song["url"], song["title"])
                if success:
                    downloaded_songs[song["url"]] = filename
                    last_message = f"Lagu '{song['title']}' berhasil didownload"
                else:
                    last_message = f"Gagal mendownload lagu '{song['title']}'"
            else:
                last_message = "Tidak ada lagu yang dipilih"
                
        elif command == 'auto':  # Toggle auto-download
            is_auto = player.toggle_auto_download()
            last_message = f"Mode auto-download {'AKTIF' if is_auto else 'NONAKTIF'}"
            
        elif command == 'dla':  # Download all songs
            last_message = "Mendownload semua lagu... Mohon tunggu."
            
            # Update tampilan untuk menampilkan pesan
            ui.clear_screen()
            ui.print_header()
            ui.print_playlist(songs, current_index, playlist_manager.is_shuffle_mode())
            ui.print_message(last_message)
            
            # Download semua lagu
            success_count = 0
            total_count = len(songs)
            
            for i, song in enumerate(songs):
                # Update tampilan dengan progress
                ui.clear_screen()
                ui.print_header()
                ui.print_playlist(songs, current_index, playlist_manager.is_shuffle_mode())
                ui.print_message(f"Mendownload [{i+1}/{total_count}]: {song['title']}...")
                
                success, filename = download_song(player, song["url"], song["title"])
                if success:
                    downloaded_songs[song["url"]] = filename
                    success_count += 1
            
            last_message = f"Berhasil mendownload {success_count} dari {len(songs)} lagu"

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nProgram dihentikan.")
    except Exception as e:
        print(f"\nTerjadi kesalahan: {e}")
