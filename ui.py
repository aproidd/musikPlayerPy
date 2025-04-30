import os
import sys
import time
import threading
import json
import curses
import locale
import re
import math
from queue import Queue, Empty
from typing import Dict, List, Any, Optional, Callable, Tuple

class ThemeManager:
    """
    Enhanced Theme Manager with support for:
    - Multiple color schemes (dark, light, matrix, etc.)
    - Custom theme loading from JSON files
    - Runtime theme switching
    - Visualizer styles
    """
    def __init__(self, themes_dir="themes"):
        self.themes_dir = themes_dir
        self.current_theme = "default"
        self.themes = self._load_themes()
        
    def _load_themes(self) -> Dict[str, Dict[str, Any]]:
        """Load built-in and custom themes"""
        themes = {
            "default": self._create_default_theme(),
            "dark": self._create_dark_theme(),
            "matrix": self._create_matrix_theme(),
            "light": self._create_light_theme()
        }
        
        # Load custom themes from themes directory
        if os.path.exists(self.themes_dir):
            for theme_file in os.listdir(self.themes_dir):
                if theme_file.endswith(".json"):
                    try:
                        with open(os.path.join(self.themes_dir, theme_file), 'r') as f:
                            theme_data = json.load(f)
                            theme_name = os.path.splitext(theme_file)[0]
                            themes[theme_name] = theme_data
                    except Exception as e:
                        print(f"Error loading theme {theme_file}: {e}")
        
        return themes
    
    def _create_default_theme(self) -> Dict[str, Any]:
        return {
            "name": "Default",
            "description": "Default terminal colors",
            "colors": {
                "background": "",
                "foreground": "\033[37m",
                "accent": "\033[36m",
                "highlight": "\033[33m",
                "error": "\033[31m",
                "success": "\033[32m",
                "playing": "\033[32m",
                "paused": "\033[33m",
                "title": "\033[1;36m",
                "artist": "\033[36m",
                "duration": "\033[37m",
                "progress_bar": "\033[36m",
                "progress_bg": "\033[30;1m",
                "controls": "\033[35m",
                "status": "\033[37m",
                "menu": "\033[37m",
                "menu_selected": "\033[30;47m",
                "header": "\033[1;37m",
                "footer": "\033[37m",
                "visualizer": "\033[36m",
                "visualizer_peak": "\033[1;32m",
                "equalizer": "\033[34m",
                "reset": "\033[0m"
            },
            "symbols": {
                "playing": "▶",
                "paused": "⏸",
                "stopped": "⏹",
                "progress_fill": "█",
                "progress_empty": "░",
                "visualizer_block": "█",
                "visualizer_wave": "▁▂▃▄▅▆▇█",
                "volume": "🔊",
                "playlist": "🎵",
                "download": "⬇",
                "search": "🔍",
                "menu": "≡",
                "next": "⏭",
                "prev": "⏮",
                "shuffle": "🔀",
                "repeat": "🔁",
                "heart": "♥",
                "clock": "⏱"
            }
        }
    
    def _create_dark_theme(self) -> Dict[str, Any]:
        return {
            "name": "Dark Mode",
            "description": "Low-light friendly dark theme",
            "colors": {
                "background": "\033[40m",
                "foreground": "\033[37m",
                "accent": "\033[38;5;39m",
                "highlight": "\033[38;5;208m",
                "error": "\033[38;5;196m",
                "success": "\033[38;5;46m",
                "playing": "\033[38;5;46m",
                "paused": "\033[38;5;214m",
                "title": "\033[1;38;5;39m",
                "artist": "\033[38;5;75m",
                "duration": "\033[38;5;250m",
                "progress_bar": "\033[38;5;39m",
                "progress_bg": "\033[38;5;235m",
                "controls": "\033[38;5;177m",
                "status": "\033[38;5;250m",
                "menu": "\033[38;5;252m",
                "menu_selected": "\033[30;48;5;39m",
                "header": "\033[1;38;5;255m",
                "footer": "\033[38;5;248m",
                "visualizer": "\033[38;5;45m",
                "visualizer_peak": "\033[1;38;5;46m",
                "equalizer": "\033[38;5;33m",
                "reset": "\033[0m"
            },
            "symbols": {
                "playing": "▶",
                "paused": "⏸",
                "stopped": "⏹",
                "progress_fill": "█",
                "progress_empty": "▒",
                "visualizer_block": "█",
                "visualizer_wave": "▁▂▃▄▅▆▇█",
                "volume": "🔊",
                "playlist": "🎵",
                "download": "⬇",
                "search": "🔍",
                "menu": "≡",
                "next": "⏭",
                "prev": "⏮",
                "shuffle": "🔀",
                "repeat": "🔁",
                "heart": "♥",
                "clock": "⏱"
            }
        }
    
    def _create_matrix_theme(self) -> Dict[str, Any]:
        return {
            "name": "Matrix",
            "description": "Matrix-inspired green theme",
            "colors": {
                "background": "\033[40m",
                "foreground": "\033[38;5;46m",
                "accent": "\033[38;5;46m",
                "highlight": "\033[38;5;118m",
                "error": "\033[38;5;196m",
                "success": "\033[1;38;5;46m",
                "playing": "\033[1;38;5;46m",
                "paused": "\033[38;5;22m",
                "title": "\033[1;38;5;46m",
                "artist": "\033[38;5;40m",
                "duration": "\033[38;5;34m",
                "progress_bar": "\033[38;5;46m",
                "progress_bg": "\033[38;5;232m",
                "controls": "\033[38;5;82m",
                "status": "\033[38;5;28m",
                "menu": "\033[38;5;40m",
                "menu_selected": "\033[30;48;5;22m",
                "header": "\033[1;38;5;46m",
                "footer": "\033[38;5;22m",
                "visualizer": "\033[38;5;46m",
                "visualizer_peak": "\033[1;38;5;118m",
                "equalizer": "\033[38;5;28m",
                "reset": "\033[0m"
            },
            "symbols": {
                "playing": "▶",
                "paused": "⏸",
                "stopped": "⏹",
                "progress_fill": "█",
                "progress_empty": "░",
                "visualizer_block": "█",
                "visualizer_wave": "▁▂▃▄▅▆▇█",
                "volume": "🔊",
                "playlist": "🎵",
                "download": "⬇",
                "search": "🔍",
                "menu": "≡",
                "next": "⏭",
                "prev": "⏮",
                "shuffle": "🔀",
                "repeat": "🔁",
                "heart": "♥",
                "clock": "⏱"
            }
        }
    
    def _create_light_theme(self) -> Dict[str, Any]:
        return {
            "name": "Light Mode",
            "description": "Bright theme for well-lit environments",
            "colors": {
                "background": "\033[47m",
                "foreground": "\033[30m",
                "accent": "\033[34m",
                "highlight": "\033[33m",
                "error": "\033[31m",
                "success": "\033[32m",
                "playing": "\033[32m",
                "paused": "\033[33m",
                "title": "\033[1;34m",
                "artist": "\033[34m",
                "duration": "\033[30m",
                "progress_bar": "\033[34m",
                "progress_bg": "\033[37;1m",
                "controls": "\033[35m",
                "status": "\033[30m",
                "menu": "\033[30m",
                "menu_selected": "\033[37;44m",
                "header": "\033[1;30m",
                "footer": "\033[30m",
                "visualizer": "\033[36m",
                "visualizer_peak": "\033[1;34m",
                "equalizer": "\033[33m",
                "reset": "\033[0m"
            },
            "symbols": {
                "playing": "▶",
                "paused": "⏸",
                "stopped": "⏹",
                "progress_fill": "█",
                "progress_empty": "░",
                "visualizer_block": "█",
                "visualizer_wave": "▁▂▃▄▅▆▇█",
                "volume": "🔊",
                "playlist": "🎵",
                "download": "⬇",
                "search": "🔍",
                "menu": "≡",
                "next": "⏭",
                "prev": "⏮",
                "shuffle": "🔀",
                "repeat": "🔁",
                "heart": "♥",
                "clock": "⏱"
            }
        }
    
    def set_theme(self, theme_name: str) -> bool:
        """Set the current theme by name"""
        if theme_name in self.themes:
            self.current_theme = theme_name
            return True
        return False
    
    def get_theme_names(self) -> List[str]:
        """Get list of available theme names"""
        return list(self.themes.keys())
    
    def get_color(self, color_name: str) -> str:
        """Get ANSI color code for the current theme"""
        theme = self.themes.get(self.current_theme, self.themes["default"])
        return theme["colors"].get(color_name, "")
    
    def get_symbol(self, symbol_name: str) -> str:
        """Get symbol for the current theme"""
        theme = self.themes.get(self.current_theme, self.themes["default"])
        return theme["symbols"].get(symbol_name, "")
    
    def get_theme_colors(self) -> Dict[str, str]:
        """Get all colors for the current theme"""
        return self.themes.get(self.current_theme, self.themes["default"])["colors"]
    
    def get_theme_info(self) -> Dict[str, str]:
        """Get theme metadata"""
        return {
            "name": self.themes[self.current_theme]["name"],
            "description": self.themes[self.current_theme]["description"]
        }

class UI:
    """
    Enhanced terminal UI with:
    - Curses-based interface
    - Theme support
    - Advanced playback controls
    - Audio visualization
    - Interactive forms
    - Responsive layout
    """
    def __init__(self):
        # Set up locale for proper UTF-8 support
        locale.setlocale(locale.LC_ALL, '')
        
        # UI state
        self.messages = []
        self.max_messages = 5
        self.command_queue = Queue()
        self.screen = None
        self.screen_height = 0
        self.screen_width = 0
        self.input_buffer = ""
        self.show_help = False
        self.form_active = False
        self.form_result = None
        self.form_fields = []
        self.form_title = ""
        self.form_current_field = 0
        self.visualizer_enabled = True
        self.equalizer_enabled = False
        
        # Initialize theme manager
        self.theme_manager = ThemeManager()
        
        # Initialize curses in a separate thread to avoid blocking
        self.curses_ready = threading.Event()
        threading.Thread(target=self._init_curses, daemon=True).start()
        self.curses_ready.wait()  # Wait for curses to initialize
    
    def _init_curses(self):
        """Initialize curses screen with proper input settings"""
        try:
            self.screen = curses.initscr()
            curses.start_color()
            curses.use_default_colors()
            curses.curs_set(1)  # Show cursor (ubah dari 0 ke 1)
            curses.noecho()     # Don't echo keystrokes
            curses.cbreak()     # Disable line buffering
            self.screen.keypad(True)  # Enable special keys
            self.screen.timeout(300)  # Increase timeout to 300ms (dari 100ms)

            # Get screen dimensions
            self.screen_height, self.screen_width = self.screen.getmaxyx()
            
            self._init_color_pairs()
            self.curses_ready.set()
        except Exception as e:
            if curses.isendwin():
                curses.endwin()
            print(f"Error initializing curses: {e}")
            sys.exit(1)
    
    def _init_color_pairs(self):
        """Initialize color pairs for curses based on current theme"""
        try:
            # Define basic color mappings
            color_map = {
                'black': curses.COLOR_BLACK,
                'red': curses.COLOR_RED,
                'green': curses.COLOR_GREEN,
                'yellow': curses.COLOR_YELLOW,
                'blue': curses.COLOR_BLUE,
                'magenta': curses.COLOR_MAGENTA,
                'cyan': curses.COLOR_CYAN,
                'white': curses.COLOR_WHITE
            }
            
            # Initialize color pairs (foreground, background)
            curses.init_pair(1, color_map['white'], color_map['black'])   # Default
            curses.init_pair(2, color_map['cyan'], color_map['black'])    # Accent
            curses.init_pair(3, color_map['yellow'], color_map['black'])  # Highlight
            curses.init_pair(4, color_map['red'], color_map['black'])     # Error
            curses.init_pair(5, color_map['green'], color_map['black'])   # Success/Playing
            curses.init_pair(6, color_map['magenta'], color_map['black']) # Controls
            curses.init_pair(7, color_map['white'], color_map['blue'])    # Selected menu
            curses.init_pair(8, color_map['cyan'], color_map['black'])    # Visualizer
            curses.init_pair(9, color_map['yellow'], color_map['black'])  # Paused
            curses.init_pair(10, color_map['green'], color_map['black'])  # Visualizer peak
            curses.init_pair(11, color_map['blue'], color_map['black'])   # Equalizer
        except Exception as e:
            self.add_message(f"Error initializing colors: {e}", error=True)
    
    def cleanup(self):
        """Clean up curses before exiting"""
        if self.screen:
            self.screen.keypad(False)
            curses.nocbreak()
            curses.echo()
            curses.endwin()
    
    def get_command(self, timeout=0.3) -> str:
        """Get user input with better key handling"""
        try:
            # First check command queue
            try:
                return self.command_queue.get_nowait()
            except Empty:
                pass

            # Get key from curses
            key = self.screen.getch()
            
            # Handle special keys first
            if key == curses.KEY_RESIZE:
                self._handle_resize()
                return None
        
            # Convert key to character
            char = None
            if 0 <= key <= 255:
                char = chr(key)
        
            # Process control characters
            if char and char.isprintable():
                if char == 'h':
                    self.show_help = not self.show_help
                elif char in ['p', 's', 'n', 'q', 'r', 't', 'v']:
                    return char
                elif char == '\n':  # Enter key
                    if self.input_buffer:
                        cmd = self.input_buffer
                        self.input_buffer = ""
                        return cmd
                elif char == '\x7f' or char == '\b':  # Backspace
                    self.input_buffer = self.input_buffer[:-1]
                else:
                    self.input_buffer += char
                
            return None
        
        except Exception as e:
            self.add_message(f"Input error: {str(e)}", error=True)
            return None
    
    def add_message(self, message: str, error: bool = False):
        """Add a message to the message queue"""
        timestamp = time.strftime("%H:%M:%S")
        self.messages.append({
            "text": message,
            "error": error,
            "time": timestamp
        })
        
        # Limit message queue size
        while len(self.messages) > self.max_messages:
            self.messages.pop(0)
    
    def toggle_theme(self):
        """Cycle through available themes"""
        themes = self.theme_manager.get_theme_names()
        current_idx = themes.index(self.theme_manager.current_theme)
        next_idx = (current_idx + 1) % len(themes)
        self.theme_manager.set_theme(themes[next_idx])
        self._init_color_pairs()  # Reinitialize colors for new theme
        return themes[next_idx]
    
    def toggle_visualizer(self):
        """Toggle visualizer on/off"""
        self.visualizer_enabled = not self.visualizer_enabled
        return self.visualizer_enabled
    
    def toggle_equalizer(self):
        """Toggle equalizer on/off"""
        self.equalizer_enabled = not self.equalizer_enabled
        return self.equalizer_enabled
    
    def _draw_header(self):
        """Draw application header with theme info"""
        if not self.screen or self.screen_height < 1 or self.screen_width < 1:
            return
            
        try:
            header_text = " Terminal Music Player "
            theme_info = f" Theme: {self.theme_manager.current_theme} "
            
            # Pastikan posisi y valid
            if 0 < self.screen_height:
                # Draw header background
                self.screen.addstr(0, 0, " " * min(self.screen_width, 200), curses.color_pair(2) | curses.A_BOLD)
                
                # Draw header text
                x_pos = max(0, (self.screen_width - len(header_text)) // 2)
                if x_pos + len(header_text) < self.screen_width:
                    self.screen.addstr(0, x_pos, header_text, curses.color_pair(2) | curses.A_BOLD)
                
                # Draw theme info
                theme_info_x = max(0, self.screen_width - len(theme_info) - 1)
                if theme_info_x > 0 and theme_info_x + len(theme_info) < self.screen_width:
                    self.screen.addstr(0, theme_info_x, theme_info, curses.color_pair(2))
        except:
            pass

    def _draw_footer(self):
        """Draw application footer with command help"""
        if not self.screen or self.screen_height < 3 or self.screen_width < 1:
            return
            
        try:
            # Pastikan posisi y valid
            y_pos = max(0, min(self.screen_height - 2, self.screen_height - 2))
            
            # Draw footer line
            self.screen.addstr(y_pos, 0, "─" * min(self.screen_width, 200), curses.color_pair(1))
            
            # Draw status line
            y_pos = max(0, min(self.screen_height - 1, self.screen_height - 1))
            
            # Control tips
            if self.show_help:
                help_lines = [
                    "Controls:",
                    " ┌───────────────────────────────┐",
                    " │ q: Quit        s: Stop        │",
                    " │ p: Play        pause: Pause   │",
                    " │ n: Next        prev: Previous │",
                    " │ r: Shuffle     t: Theme       │",
                    " │ v: Visualizer  h: Help        │",
                    " └───────────────────────────────┘",
                    "Playlist:",
                    " ┌─────────────────────────────────────────────┐",
                    " │ a: Add Song   e: Edit Song   d: Delete Song │",
                    " │ i: Info       save: Save Playlist           │",
                    " └─────────────────────────────────────────────┘",
                    "Download:",
                    " ┌────────────────────────────────────────────┐",
                    " │ dl: Download Current  dla: Download All    │",
                    " │ auto: Toggle Auto-Download                 │",
                    " └────────────────────────────────────────────┘",
                ]

                for idx, line in enumerate(help_lines):
                    x_pos = max(0, (self.screen_width - len(line)) // 2)
                    if y_pos + idx < self.screen_height - 1 and x_pos + len(line) < self.screen_width:
                        self.screen.addstr(y_pos + idx, x_pos, line, curses.color_pair(6))
            else:
                status_text = " Press 'h' for help "
                x_pos = max(0, (self.screen_width - len(status_text)) // 2)
                if x_pos + len(status_text) < self.screen_width:
                    self.screen.addstr(y_pos, x_pos, status_text, curses.color_pair(1))

            # Input area
            prompt = " > "
            if len(prompt) + len(self.input_buffer) < self.screen_width:
                self.screen.addstr(y_pos, 0, prompt, curses.color_pair(2))
                self.screen.addstr(y_pos, len(prompt), self.input_buffer, curses.color_pair(1))
                
                # Show cursor at input position
                try:
                    curses.curs_set(1)
                    cursor_x = min(len(prompt) + len(self.input_buffer), self.screen_width - 1)
                    self.screen.move(y_pos, cursor_x)
                except:
                    pass
        except:
            pass
    
    def _draw_messages(self):
        """Draw message area with timestamp"""
        if not self.screen:
            return
            
        start_y = self.screen_height - 2 - len(self.messages)
        for i, msg in enumerate(self.messages):
            y_pos = start_y + i
            if 0 <= y_pos < self.screen_height - 2:
                # Format message with timestamp
                message = f"[{msg['time']}] {msg['text']}"
                
                # Truncate if needed
                if len(message) > self.screen_width:
                    message = message[:self.screen_width - 3] + "..."
                
                # Draw with appropriate color
                color = curses.color_pair(4) if msg["error"] else curses.color_pair(1)
                self.screen.addstr(y_pos, 0, message, color)
    
    def _draw_visualizer(self, visualizer_data, y_pos, height=5):
        """Draw audio visualizer with multiple modes"""
        if not self.screen or not visualizer_data:
            return
            
        mode = visualizer_data.get("mode", "spectrum")
        data = visualizer_data.get("data", [])
        enabled = visualizer_data.get("enabled", False)
        
        if not enabled or not data:
            return
            
        # Get visualizer character from theme
        block_char = self.theme_manager.get_symbol('visualizer_block')
        wave_chars = self.theme_manager.get_symbol('visualizer_wave')
        visualizer_color = curses.color_pair(8)
        peak_color = curses.color_pair(10)
        
        if mode == "spectrum":
            # Draw spectrum analyzer
            width = min(len(data), self.screen_width - 2)
            for i in range(width):
                value = min(data[i], height)
                for j in range(height):
                    if j >= height - value:
                        try:
                            # Use peak color for top of the bar
                            color = peak_color if j == height - value else visualizer_color
                            self.screen.addstr(y_pos + height - j - 1, i + 1, block_char, color)
                        except:
                            pass
        
        elif mode == "wave":
            # Draw waveform
            width = min(len(data), self.screen_width - 2)
            middle = height // 2
            for i in range(width):
                value = data[i]
                pos = middle + value
                try:
                    char_idx = min(int((value + 1) * (len(wave_chars) / 2)), len(wave_chars) - 1)
                    self.screen.addstr(y_pos + pos, i + 1, wave_chars[char_idx], visualizer_color)
                except:
                    pass
        
        elif mode == "bars":
            # Draw equalizer bars
            bar_width = max(1, (self.screen_width - 2) // len(data))
            for i, value in enumerate(data):
                value = min(value, height)
                for j in range(height):
                    if j >= height - value:
                        try:
                            x = i * bar_width + 1
                            # Draw the bar
                            for k in range(bar_width):
                                if x + k < self.screen_width - 1:
                                    # Use peak color for top of the bar
                                    color = peak_color if j == height - value else visualizer_color
                                    self.screen.addstr(y_pos + height - j - 1, x + k, block_char, color)
                        except:
                            pass
    
    def _draw_equalizer(self, eq_data, y_pos, height=5):
        """Draw audio equalizer bars"""
        if not self.screen or not eq_data or not self.equalizer_enabled:
            return
            
        block_char = self.theme_manager.get_symbol('visualizer_block')
        eq_color = curses.color_pair(11)
        
        # Draw frequency bands
        band_width = max(1, (self.screen_width - 2) // len(eq_data))
        for i, value in enumerate(eq_data):
            value = min(value, height)
            for j in range(height):
                if j >= height - value:
                    try:
                        x = i * band_width + 1
                        for k in range(band_width):
                            if x + k < self.screen_width - 1:
                                self.screen.addstr(y_pos + height - j - 1, x + k, block_char, eq_color)
                    except:
                        pass
    
    def _draw_progress_bar(self, current_time, duration, y_pos, is_paused=False):
        """Draw playback progress bar with time display"""
        if not self.screen:
            return
            
        # Calculate progress
        try:
            current_sec = sum(x * int(t) for x, t in zip([60, 1], current_time.split(":")))
            total_sec = sum(x * int(t) for x, t in zip([60, 1], duration.split(":")))
            progress = current_sec / total_sec if total_sec > 0 else 0
        except:
            progress = 0
            
        # Draw time display
        time_text = f"{current_time} / {duration}"
        self.screen.addstr(y_pos, 0, time_text, curses.color_pair(1))
        
        # Draw progress bar
        bar_width = self.screen_width - len(time_text) - 4
        filled_width = int(progress * bar_width)
        
        # Draw container
        self.screen.addstr(y_pos, len(time_text) + 2, "[", curses.color_pair(1))
        self.screen.addstr(y_pos, len(time_text) + 3 + bar_width, "]", curses.color_pair(1))
        
        # Draw filled portion
        fill_char = self.theme_manager.get_symbol('progress_fill')
        empty_char = self.theme_manager.get_symbol('progress_empty')
        bar_color = curses.color_pair(9) if is_paused else curses.color_pair(5)
        
        for i in range(bar_width):
            if i < filled_width:
                self.screen.addstr(y_pos, len(time_text) + 3 + i, fill_char, bar_color)
            else:
                self.screen.addstr(y_pos, len(time_text) + 3 + i, empty_char, curses.color_pair(1))
    
    def _draw_song_info(self, song, y_pos, playback_source="STREAM"):
        """Draw current song information with source indicator"""
        if not self.screen or not song:
            return
            
        # Format song info
        title = song.get("title", "Unknown Title")
        artist = song.get("artist", "Unknown Artist")
        source_text = f"[{playback_source}]" if playback_source else ""
        
        # Draw song title
        title_text = f"♫ {title} {source_text}"
        if len(title_text) > self.screen_width:
            title_text = title_text[:self.screen_width - 3] + "..."
        self.screen.addstr(y_pos, 0, title_text, curses.color_pair(2) | curses.A_BOLD)
        
        # Draw artist
        artist_text = f"🎤 {artist}"
        if len(artist_text) > self.screen_width:
            artist_text = artist_text[:self.screen_width - 3] + "..."
        self.screen.addstr(y_pos + 1, 0, artist_text, curses.color_pair(2))
    
    def _draw_playlist(self, songs, current_index, y_pos, height=10):
        """Draw playlist with current song highlighted"""
        if not self.screen or not songs:
            return
            
        # Calculate visible range
        total_songs = len(songs)
        visible_songs = min(height, total_songs)
        start_idx = max(0, current_index - (visible_songs // 2))
        if start_idx + visible_songs > total_songs:
            start_idx = max(0, total_songs - visible_songs)
            
        # Draw playlist title
        self.screen.addstr(y_pos, 0, "─── Playlist ───", curses.color_pair(2) | curses.A_BOLD)
        
        # Draw playlist items
        for i in range(visible_songs):
            song_idx = start_idx + i
            if song_idx < total_songs:
                song = songs[song_idx]
                
                # Format song entry
                number = f"{song_idx + 1:02d}"
                title = song.get("title", "Unknown")
                artist = song.get("artist", "")
                duration = song.get("duration", "00:00")
                
                # Truncate if needed
                max_title_len = self.screen_width - len(number) - len(duration) - 8
                if len(title) > max_title_len:
                    title = title[:max_title_len - 3] + "..."
                
                song_text = f" {number}. {title} - {duration} "
                text_y_pos = y_pos + i + 1
                
                # Highlight current song
                if song_idx == current_index:
                    self.screen.addstr(text_y_pos, 0, " " * self.screen_width, curses.color_pair(7))
                    play_symbol = self.theme_manager.get_symbol('playing')
                    self.screen.addstr(text_y_pos, 0, f"{play_symbol} {song_text}", curses.color_pair(7))
                else:
                    self.screen.addstr(text_y_pos, 0, f"  {song_text}", curses.color_pair(1))
    
    def _draw_controls(self, y_pos, is_playing=False, is_paused=False, volume=100):
        """Draw playback controls with status indicators"""
        if not self.screen:
            return
            
        # Get control symbols
        play_symbol = self.theme_manager.get_symbol('playing')
        pause_symbol = self.theme_manager.get_symbol('paused')
        stop_symbol = self.theme_manager.get_symbol('stopped')
        next_symbol = self.theme_manager.get_symbol('next')
        prev_symbol = self.theme_manager.get_symbol('prev')
        shuffle_symbol = self.theme_manager.get_symbol('shuffle')
        vol_symbol = self.theme_manager.get_symbol('volume')
        
        # Format controls display
        current_symbol = pause_symbol if is_paused else play_symbol if is_playing else stop_symbol
        controls_text = f"{prev_symbol} {current_symbol} {next_symbol} {shuffle_symbol}  {vol_symbol}: {volume}%"
        
        x_pos = (self.screen_width - len(controls_text)) // 2
        self.screen.addstr(y_pos, x_pos, controls_text, curses.color_pair(6))
    
    def _draw_status(self, y_pos, shuffle_mode=False, auto_download=False, downloaded=0, total=0):
        """Draw status information line"""
        if not self.screen:
            return
            
        # Format status info
        shuffle_status = "SHUFFLE: ON" if shuffle_mode else "SHUFFLE: OFF"
        download_status = "AUTO-DL: ON" if auto_download else "AUTO-DL: OFF"
        cache_status = f"CACHED: {downloaded}/{total}"
        
        status_text = f"{shuffle_status} | {download_status} | {cache_status}"
        x_pos = (self.screen_width - len(status_text)) // 2
        self.screen.addstr(y_pos, x_pos, status_text, curses.color_pair(1))
    
    def render_playing_state(self, songs, current_index, shuffle_mode, current_time, 
                           current_song, playback_source, auto_download, downloaded, total,
                           visualizer_data=None, is_paused=False, volume=100, eq_data=None):
        """Render the full playing state UI"""
        if not self.screen:
            return
            
        try:
            self.screen.clear()
            self._draw_header()
            
            base_y = 2  # Start after header
            
            # Draw song info
            self._draw_song_info(current_song, base_y, playback_source)
            
            # Draw progress bar
            duration = current_song.get("duration", "00:00")
            self._draw_progress_bar(current_time, duration, base_y + 3, is_paused)
            
            # Draw controls
            self._draw_controls(base_y + 5, True, is_paused, volume)
            
            # Draw status
            self._draw_status(base_y + 7, shuffle_mode, auto_download, downloaded, total)
            
            # Draw visualizer if enabled
            vis_height = 0
            if self.visualizer_enabled and visualizer_data:
                self._draw_visualizer(visualizer_data, base_y + 9)
                vis_height = 6
            
            # Draw equalizer if enabled
            if self.equalizer_enabled and eq_data:
                self._draw_equalizer(eq_data, base_y + 9 + vis_height)
                vis_height += 6
            
            # Draw playlist
            playlist_y = base_y + 9 + vis_height
            available_height = self.screen_height - playlist_y - 7
            self._draw_playlist(songs, current_index, playlist_y, available_height)
            
            # Draw messages and footer
            self._draw_messages()
            self._draw_footer()
            
            self.screen.refresh()
        except Exception as e:
            self.add_message(f"UI Error: {str(e)}", error=True)
    
    def render_idle_state(self, songs, current_index, shuffle_mode, auto_download, downloaded):
        """Render the idle state UI"""
        if not self.screen:
            return
            
        try:
            self.screen.clear()
            self._draw_header()
            
            idle_msg = "♫ Ready to play music ♫"
            x_pos = (self.screen_width - len(idle_msg)) // 2
            self.screen.addstr(3, x_pos, idle_msg, curses.color_pair(2) | curses.A_BOLD)
            
            self._draw_status(5, shuffle_mode, auto_download, downloaded, len(songs))
            
            available_height = self.screen_height - 15
            self._draw_playlist(songs, current_index, 7, available_height)
            
            self._draw_messages()
            self._draw_footer()
            
            self.screen.refresh()
        except Exception as e:
            self.add_message(f"UI Error: {str(e)}", error=True)
    
    def render_processing_state(self, operation):
        """Render processing/loading state"""
        if not self.screen:
            return
            
        try:
            self.screen.clear()
            self._draw_header()
            
            msg = f"Processing: {operation}"
            x_pos = (self.screen_width - len(msg)) // 2
            self.screen.addstr(self.screen_height // 2, x_pos, msg, curses.color_pair(3) | curses.A_BOLD)
            
            # Draw spinner animation
            spinner = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"
            idx = int(time.time() * 10) % len(spinner)
            self.screen.addstr(self.screen_height // 2 + 2, self.screen_width // 2, spinner[idx], curses.color_pair(2))
            
            self.screen.refresh()
        except Exception as e:
            self.add_message(f"UI Error: {str(e)}", error=True)
    
    def add_song_form(self):
        """Display form to add a new song"""
        form_fields = [
            {"label": "Title", "value": "", "required": True},
            {"label": "Artist", "value": "", "required": False},
            {"label": "URL", "value": "", "required": True},
            {"label": "Duration", "value": "Unknown", "required": False}
        ]
        return self._display_form("Add New Song", form_fields)
    
    def edit_song_form(self, song):
        """Display form to edit song"""
        form_fields = [
            {"label": "Title", "value": song.get("title", ""), "required": True},
            {"label": "Artist", "value": song.get("artist", ""), "required": False},
            {"label": "URL", "value": song.get("url", ""), "required": True},
            {"label": "Duration", "value": song.get("duration", "Unknown"), "required": False}
        ]
        return self._display_form("Edit Song", form_fields)
    
    def _display_form(self, title, fields):
        """Display and process a form"""
        if not self.screen:
            return None
            
        self.form_active = True
        self.form_fields = fields
        self.form_title = title
        self.form_current_field = 0
        self.form_result = None
        
        while self.form_active:
            self._draw_form()
            key = self.screen.getch()
            self._process_form_key(key)
        
        return tuple(field["value"] for field in self.form_result) if self.form_result else None
    
    def _draw_form(self):
        """Draw form UI"""
        if not self.screen:
            return
            
        try:
            self.screen.clear()
            self._draw_header()
            
            self.screen.addstr(2, 2, f"── {self.form_title} ──", curses.color_pair(2) | curses.A_BOLD)
            
            for i, field in enumerate(self.form_fields):
                label = field["label"]
                value = field["value"]
                required = field["required"]
                
                req_mark = "*" if required else ""
                self.screen.addstr(4 + i * 2, 2, f"{label}{req_mark}: ", curses.color_pair(1))
                
                if i == self.form_current_field:
                    self.screen.addstr(4 + i * 2, len(label) + 4, value, curses.color_pair(7))
                    self.screen.addstr(4 + i * 2, len(label) + 4 + len(value), " ", curses.color_pair(7))
                else:
                    self.screen.addstr(4 + i * 2, len(label) + 4, value, curses.color_pair(1))
            
            help_text = "Tab: Next field | Enter: Submit | Esc: Cancel"
            self.screen.addstr(4 + len(self.form_fields) * 2 + 1, 2, help_text, curses.color_pair(6))
            
            self.screen.refresh()
        except Exception as e:
            self.add_message(f"Form Error: {str(e)}", error=True)
    
    def _process_form_key(self, key):
        """Process form key input"""
        if key == 9:  # Tab
            self.form_current_field = (self.form_current_field + 1) % len(self.form_fields)
        elif key == 10:  # Enter
            all_filled = all(not field["required"] or field["value"] for field in self.form_fields)
            if all_filled:
                self.form_result = self.form_fields
                self.form_active = False
        elif key == 27:  # Escape
            self.form_active = False
        elif key == curses.KEY_BACKSPACE or key == 127 or key == 8:
            if self.form_fields[self.form_current_field]["value"]:
                self.form_fields[self.form_current_field]["value"] = self.form_fields[self.form_current_field]["value"][:-1]
        elif 32 <= key <= 126:  # Printable ASCII
            self.form_fields[self.form_current_field]["value"] += chr(key)
    
    def confirm_delete(self, song):
        """Display confirmation dialog for deletion"""
        if not self.screen:
            return False
        
        title = f"Delete '{song['title']}'?"
        message = "Are you sure you want to delete this song from the playlist?"
        options = ["Yes", "No"]
        
        result = self._show_dialog(title, message, options)
        return result == 0
    
    def _show_dialog(self, title, message, options):
        """Show a dialog with options"""
        if not self.screen:
            return -1
            
        selected = 0
        dialog_active = True
        
        while dialog_active:
            try:
                width = max(len(title), len(message), 40)
                height = 6 + len(options)
                x = (self.screen_width - width) // 2
                y = (self.screen_height - height) // 2
                
                # Clear dialog area
                for i in range(height):
                    self.screen.addstr(y + i, x, " " * width, curses.color_pair(1))
                
                # Draw border
                for i in range(width):
                    self.screen.addstr(y, x + i, "─", curses.color_pair(2))
                    self.screen.addstr(y + height - 1, x + i, "─", curses.color_pair(2))
                
                for i in range(height):
                    self.screen.addstr(y + i, x, "│", curses.color_pair(2))
                    self.screen.addstr(y + i, x + width - 1, "│", curses.color_pair(2))
                
                # Draw corners
                self.screen.addstr(y, x, "┌", curses.color_pair(2))
                self.screen.addstr(y, x + width - 1, "┐", curses.color_pair(2))
                self.screen.addstr(y + height - 1, x, "└", curses.color_pair(2))
                self.screen.addstr(y + height - 1, x + width - 1, "┘", curses.color_pair(2))
                
                # Draw title and message
                title_x = x + (width - len(title)) // 2
                self.screen.addstr(y + 1, title_x, title, curses.color_pair(2) | curses.A_BOLD)
                
                msg_x = x + (width - len(message)) // 2
                self.screen.addstr(y + 3, msg_x, message, curses.color_pair(1))
                
                # Draw options
                for i, option in enumerate(options):
                    opt_x = x + (width - len(option)) // 2
                    if i == selected:
                        self.screen.addstr(y + 5 + i, opt_x - 2, f"> {option} <", curses.color_pair(7))
                    else:
                        self.screen.addstr(y + 5 + i, opt_x, option, curses.color_pair(1))
                
                self.screen.refresh()
                
                # Process input
                key = self.screen.getch()
                if key == curses.KEY_LEFT or key == curses.KEY_UP:
                    selected = max(0, selected - 1)
                elif key == curses.KEY_RIGHT or key == curses.KEY_DOWN:
                    selected = min(len(options) - 1, selected + 1)
                elif key == 10:  # Enter
                    dialog_active = False
                elif key == 27:  # Escape
                    selected = -1
                    dialog_active = False
            except Exception as e:
                self.add_message(f"Dialog Error: {str(e)}", error=True)
                return -1
        
        return selected
