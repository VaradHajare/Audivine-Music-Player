import tkinter as tk
from tkinter import ttk
import threading
import pygame
import os
import tempfile
import yt_dlp
from youtubesearchpython import VideosSearch
from ctypes import cast, POINTER
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
import sys
import subprocess
import speech_recognition as sr
from PIL import Image, ImageTk
import base64
import io

# Initialize pygame mixer
pygame.mixer.init()

def resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    
    return os.path.join(base_path, relative_path)

def check_dependencies():
    """Check for required dependencies and show appropriate error messages"""
    try:
        import pygame
        import yt_dlp
        from youtubesearchpython import VideosSearch
        from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
    except ImportError as e:
        import tkinter as tk
        from tkinter import messagebox
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror("Missing Dependencies", 
            f"Error: {str(e)}\nPlease ensure all required packages are installed.")
        sys.exit(1)

class MusicPlayer:
    def __init__(self):
        self.window = tk.Tk()
        self.window.title("Audivine Music Player")
        self.window.configure(bg='#1E1E1E')
        
        # Make window appear in taskbar and alt-tab
        self.window.attributes('-toolwindow', False)  # Not a tool window
        self.window.wm_attributes('-topmost', False)  # Don't stay on top
        self.window.resizable(True, True)  # Allow resizing
        
        # Set minimum window size
        self.window.minsize(800, 600)
        
        # Music player variables
        self.is_playing = False
        self.current_url = None
        self.temp_dir = tempfile.gettempdir()
        self.queue = []
        self.current_song_index = -1
        
        # Remove the fixed window size and use full screen dimensions
        screen_width = self.window.winfo_screenwidth()
        screen_height = self.window.winfo_screenheight()
        self.window.geometry(f'{screen_width}x{screen_height}+0+0')
        
        # Remove resizable restriction
        self.window.resizable(True, True)
        
        # Main container with padding
        self.container = tk.Frame(self.window, bg='#1E1E1E')
        self.container.pack(expand=True, fill='both', padx=40, pady=30)
        
        # Configure grid weights for responsive layout
        self.container.grid_columnconfigure(0, weight=1)
        self.container.grid_rowconfigure(3, weight=1)  # Make queue frame expandable
        
        # Title Frame with cyberpunk style
        title_frame = tk.Frame(self.container, bg='#1E1E1E')
        title_frame.grid(row=0, column=0, pady=(0, 30), sticky='ew')
        
        # Center the decorations and title
        title_frame.grid_columnconfigure(1, weight=1)
        
        # Music note decorations
        left_decor = tk.Label(title_frame, 
                             text="♫ ♪ ═══",
                             font=('Consolas', 24),
                             bg='#1E1E1E',
                             fg='#4CAF50')
        left_decor.grid(row=0, column=0, padx=10)
        
        # Main title
        title_label = tk.Label(title_frame, 
                              text="AUDIVINE",
                              font=('Arial Black', 32, 'bold'),
                              bg='#1E1E1E',
                              fg='#4CAF50',
                              pady=5)
        title_label.grid(row=0, column=1)
        
        # Right decoration
        right_decor = tk.Label(title_frame, 
                              text="═══ ♪ ♫",
                              font=('Consolas', 24),
                              bg='#1E1E1E',
                              fg='#4CAF50')
        right_decor.grid(row=0, column=2, padx=10)
        
        # Add glowing effect to title
        def glow_effect():
            current_color = title_label.cget("fg")
            if current_color == '#4CAF50':  # Base green
                title_label.config(fg='#45a049')  # Darker green
            else:
                title_label.config(fg='#4CAF50')  # Back to base green
            self.window.after(1000, glow_effect)  # Repeat every 1 second
        
        # Start the glowing effect
        glow_effect()
        
        # Search Frame
        self.search_frame = tk.Frame(self.container, bg='#1E1E1E')
        self.search_frame.grid(row=1, column=0, pady=(0, 25), sticky='ew')
        self.search_frame.grid_columnconfigure(0, weight=1)
        
        # Search elements container
        search_center = tk.Frame(self.search_frame, bg='#1E1E1E')
        search_center.grid(row=0, column=0)
        
        # Search container
        search_container = tk.Frame(search_center, bg='#4CAF50', padx=2, pady=2)
        search_container.pack(side=tk.LEFT, padx=5)
        
        self.search_var = tk.StringVar()
        self.search_entry = tk.Entry(search_container, textvariable=self.search_var,
                                    width=50, font=('Arial', 12),
                                    bg='#2D2D2D', fg='white',
                                    insertbackground='white',
                                    relief='flat')
        self.search_entry.pack(padx=1, pady=1, ipady=8)
        
        # Add placeholder text behavior
        self.search_entry.insert(0, "Search for a song...")
        self.search_entry.bind('<FocusIn>', self.on_entry_click)
        self.search_entry.bind('<FocusOut>', self.on_focus_out)
        self.search_entry.bind('<Return>', self.search_and_add)
        self.search_entry.config(fg='grey')
        
        # Style the add button with rounded corners
        self.add_button = tk.Button(search_center, text="Search & Add",
                                   command=self.search_and_add,
                                   font=('Arial', 11, 'bold'),
                                   bg='#4CAF50', fg='white',
                                   relief='flat',
                                   padx=20, pady=8,
                                   cursor='hand2')  # Hand cursor on hover
        self.add_button.pack(side=tk.LEFT, padx=5)
        
        # Add voice search button
        self.voice_button = tk.Button(search_center, text="🎤",
                                    font=('Arial', 14, 'bold'),
                                    bg='#4CAF50', fg='white',
                                    relief='flat',
                                    padx=10, pady=6,
                                    cursor='hand2',
                                    command=self.voice_search)
        self.voice_button.pack(side=tk.LEFT, padx=5)
        
        # Add hover effects for buttons
        for button in [self.add_button, self.voice_button]:
            def on_enter(e, btn=button):
                btn['background'] = '#45a049'

            def on_leave(e, btn=button):
                btn['background'] = '#4CAF50'

            button.bind("<Enter>", on_enter)
            button.bind("<Leave>", on_leave)
        
        # Add these styles to make the window look better
        style = ttk.Style()
        style.configure('Rounded.TEntry',
                        fieldbackground='#2D2D2D',
                        background='#2D2D2D',
                        foreground='white',
                        borderwidth=0,
                        relief='flat')
        
        # Queue Frame
        self.queue_frame = tk.Frame(self.container, bg='#2D2D2D')
        self.queue_frame.grid(row=2, column=0, sticky='nsew', pady=20)
        self.queue_frame.grid_columnconfigure(0, weight=1)
        self.queue_frame.grid_rowconfigure(1, weight=1)
        
        # Queue Header
        queue_header = tk.Frame(self.queue_frame, bg='#2D2D2D')
        queue_header.grid(row=0, column=0, sticky='ew', padx=10, pady=10)
        queue_header.grid_columnconfigure(1, weight=1)
        
        tk.Label(queue_header, text="Queue", 
                font=('Arial', 14, 'bold'),
                bg='#2D2D2D', fg='white').grid(row=0, column=0, sticky='w')
        
        # Add replay toggle button
        self.replay_queue = False  # Add this variable to track replay state
        self.replay_button = tk.Button(queue_header,
                                      text="🔁",  # Loop symbol
                                      font=('Arial', 14),
                                      bg='#2D2D2D',
                                      fg='grey',  # Start with grey (disabled)
                                      relief='flat',
                                      command=self.toggle_replay,
                                      cursor='hand2')
        self.replay_button.grid(row=0, column=2, sticky='e')
        
        # Queue Listbox with scrollbar
        listbox_frame = tk.Frame(self.queue_frame, bg='#2D2D2D')
        listbox_frame.grid(row=1, column=0, sticky='nsew', padx=10, pady=(0, 10))
        listbox_frame.grid_columnconfigure(0, weight=1)
        listbox_frame.grid_rowconfigure(0, weight=1)
        
        # Create a frame to hold both listbox and remove buttons
        self.queue_container = tk.Frame(listbox_frame, bg='#2D2D2D')
        self.queue_container.pack(side=tk.LEFT, fill='both', expand=True)
        
        # Queue Listbox
        self.queue_listbox = tk.Listbox(self.queue_container, 
                                       font=('Arial', 11),
                                       bg='#333333', fg='white',
                                       selectmode=tk.SINGLE,
                                       relief='flat',
                                       activestyle='none',
                                       selectbackground='#4CAF50',
                                       selectforeground='white')
        self.queue_listbox.pack(side=tk.LEFT, fill='both', expand=True)
        
        # Remove buttons container
        self.remove_buttons_frame = tk.Frame(self.queue_container, bg='#333333')
        self.remove_buttons_frame.pack(side=tk.RIGHT, fill='y')
        
        # Scrollbar
        scrollbar = tk.Scrollbar(listbox_frame, orient="vertical",
                                 command=self.queue_listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill='y')
        self.queue_listbox.config(yscrollcommand=scrollbar.set)
        
        # Now Playing Frame
        now_playing_frame = tk.Frame(self.container, bg='#2D2D2D')
        now_playing_frame.grid(row=3, column=0, sticky='ew', pady=(0, 20))
        
        self.now_playing_label = tk.Label(now_playing_frame, 
                                        text="Not Playing",
                                        font=('Arial', 12),
                                        bg='#2D2D2D', fg='white')
        self.now_playing_label.pack(pady=10)
        
        # Add keyboard shortcuts info
        shortcuts_label = tk.Label(now_playing_frame,
                                 text="Shortcuts: Space (Play/Pause) | ← → (Previous/Next) | ↑ ↓ (Volume)",
                                 font=('Arial', 10),
                                 bg='#2D2D2D', fg='#888888')
        shortcuts_label.pack(pady=(0, 5))
        
        # Controls Frame
        controls_frame = tk.Frame(self.container, bg='#1E1E1E')
        controls_frame.grid(row=4, column=0, sticky='ew')
        controls_frame.grid_columnconfigure(0, weight=1)
        
        # Update button style with hover effects and better styling
        button_style = {
            'font': ('Arial', 16),
            'bg': '#2D2D2D',
            'fg': 'white',
            'relief': 'flat',
            'width': 4,
            'padx': 20,  # Increased padding
            'pady': 10,  # Increased padding
            'cursor': 'hand2',  # Hand cursor on hover
            'activebackground': '#4CAF50',  # Green background when clicked
            'activeforeground': 'white',  # White text when clicked
        }
        
        # Create a frame for control buttons with better spacing
        self.buttons_frame = tk.Frame(controls_frame, bg='#1E1E1E')
        self.buttons_frame.grid(row=0, column=0, pady=20)  # Changed from pack to grid
        
        # Control Buttons with hover effects
        self.prev_button = tk.Button(self.buttons_frame, text="⏮",
                                   command=self.play_previous, **button_style)
        self.prev_button.grid(row=0, column=0, padx=10)  # Changed from pack to grid
        
        self.play_button = tk.Button(self.buttons_frame, text="▶",
                                   command=self.toggle_play, **button_style)
        self.play_button.grid(row=0, column=1, padx=10)  # Changed from pack to grid
        
        self.next_button = tk.Button(self.buttons_frame, text="⏭",
                                   command=self.play_next, **button_style)
        self.next_button.grid(row=0, column=2, padx=10)  # Changed from pack to grid
        
        self.stop_button = tk.Button(self.buttons_frame, text="⏹",
                                   command=self.stop_music, **button_style)
        self.stop_button.grid(row=0, column=3, padx=10)  # Changed from pack to grid
        
        # Add hover effects for all control buttons
        for button in [self.prev_button, self.play_button, self.next_button, self.stop_button]:
            self.add_button_hover_effect(button)
        
        # Volume Frame
        volume_frame = tk.Frame(controls_frame, bg='#1E1E1E')
        volume_frame.grid(row=1, column=0, pady=15, sticky='ew')
        volume_frame.grid_columnconfigure(0, weight=1)
        
        # Volume container
        volume_container = tk.Frame(volume_frame, bg='#2D2D2D', padx=20, pady=15)
        volume_container.grid(row=0, column=0)
        
        # Initialize system volume control first
        try:
            devices = AudioUtilities.GetSpeakers()
            interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
            self.volume_controller = cast(interface, POINTER(IAudioEndpointVolume))
            current_vol = round((self.volume_controller.GetMasterVolumeLevelScalar() * 100))
        except Exception as e:
            print(f"Could not initialize system volume control: {e}")
            self.volume_controller = None
            current_vol = 50
        
        # Store last volume before mute (moved after current_vol is defined)
        self.last_volume = current_vol
        self.is_muted = False
        
        # Volume Label with icon in container as a button
        self.volume_button = tk.Button(volume_container,
                                     text="🔊",
                                     font=('Arial', 14),
                                     bg='#2D2D2D',
                                     fg='#4CAF50',
                                     relief='flat',
                                     bd=0,
                                     cursor='hand2',
                                     command=self.toggle_mute)
        self.volume_button.grid(row=0, column=0, padx=(0, 10))  # Changed from pack to grid
        
        # Enhanced volume slider in container
        self.volume_slider = tk.Scale(volume_container,
                                    from_=0, to=100,
                                    orient=tk.HORIZONTAL,
                                    length=200,
                                    bg='#2D2D2D',
                                    fg='#FFFFFF',
                                    troughcolor='#4CAF50',
                                    activebackground='#2D2D2D',
                                    highlightthickness=0,
                                    sliderrelief='flat',
                                    bd=0,
                                    width=15,
                                    showvalue=False,
                                    command=self.set_volume)
        
        # Set initial volume
        self.volume_slider.set(current_vol)
        self.volume_slider.grid(row=0, column=1, padx=(10, 15), pady=8)  # Changed from pack to grid
        
        # Add percentage label in container
        self.volume_label = tk.Label(volume_container,
                                    text=f"{current_vol}%",
                                    font=('Arial', 10),
                                    bg='#2D2D2D',
                                    fg='#FFFFFF',
                                    width=4)
        self.volume_label.grid(row=0, column=2)  # Changed from pack to grid
        
        # Bind mouse wheel to volume slider
        self.volume_slider.bind('<MouseWheel>', self.on_mouse_wheel)  # Windows
        self.volume_slider.bind('<Button-4>', self.on_mouse_wheel)    # Linux up
        self.volume_slider.bind('<Button-5>', self.on_mouse_wheel)    # Linux down
        
        # Start checking for end of track
        self.check_music_end()
        
        # Bind double-click to play selected song
        self.queue_listbox.bind('<Button-1>', self.play_selected)
        
        # Add keyboard bindings
        self.window.bind('<space>', self.toggle_play_keyboard)
        self.window.bind('<Left>', self.play_previous_keyboard)
        self.window.bind('<Right>', self.play_next_keyboard)
        self.window.bind('<Up>', self.volume_up)
        self.window.bind('<Down>', self.volume_down)
        
        # Update volume slider to maintain size
        self.volume_slider.config(length=min(200, self.window.winfo_width() // 4))
        
        # Bind window resize event
        self.window.bind('<Configure>', self.on_window_resize)
        
        self.window.mainloop()
    
    def center_window(self, width, height):
        """Make window fullscreen and on top when opened"""
        self.window.lift()
        self.window.attributes('-topmost', True)
        self.window.attributes('-topmost', False)
    
    def play_selected(self, event=None):
        """Play the selected song when clicked"""
        selection = self.queue_listbox.curselection()
        if selection:
            index = selection[0]
            # Only play if clicking a different song than currently playing
            if index != self.current_song_index:
                self.current_song_index = index - 1  # Set index to play selected song
                self.play_next()
    
    def add_to_queue(self):
        url = self.url_var.get().strip()
        if url:
            try:
                # Get video info without downloading
                with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
                    info = ydl.extract_info(url, download=False)
                    title = info.get('title', 'Unknown Title')
                
                self.queue.append({'url': url, 'title': title})
                self.queue_listbox.insert(tk.END, title)
                self.url_var.set("")  # Clear entry
                
                # If nothing is playing, start playing
                if not self.is_playing and len(self.queue) == 1:
                    self.current_song_index = -1  # Reset index
                    self.play_next()
                    
            except Exception as e:
                self.now_playing_label.config(text=f"Error: {str(e)}")
                print(f"Error adding to queue: {str(e)}")
    
    def play_music(self, url, title):
        try:
            # Configure yt-dlp options with audio-only preference
            ydl_opts = {
                'format': 'bestaudio[ext=m4a]/bestaudio/best',
                'outtmpl': os.path.join(self.temp_dir, '%(id)s.%(ext)s'),
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                    'nopostoverwrites': False,
                }],
                'prefer_ffmpeg': True,
                'keepvideo': False,
                'extract_audio': True,
                'audio_quality': 0,
                'quiet': True,
                'no_warnings': True,
                'nocheckcertificate': True,
                'buffersize': 1024*8,
                'concurrent_fragments': 4,
            }

            # Download audio using yt-dlp
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                # Extract info first
                info = ydl.extract_info(url, download=False)
                video_id = info['id']
                
                # Determine the output file path
                temp_file = os.path.join(self.temp_dir, f'{video_id}.mp3')
                
                # Check if file already exists
                if not os.path.exists(temp_file):
                    # Download if doesn't exist
                    ydl.download([url])

                # Stop current playback if any
                pygame.mixer.music.stop()
                pygame.mixer.music.unload()
                
                # Load and play the new audio
                pygame.mixer.music.load(temp_file)
                pygame.mixer.music.set_volume(self.volume_slider.get() / 100.0)
                pygame.mixer.music.play()
                
                self.is_playing = True
                self.play_button.config(text="⏸")
                self.current_url = url
                self.now_playing_label.config(text=f"Now Playing: {title}")
                
        except Exception as e:
            print(f"Playback error: {str(e)}")  # For debugging
            self.play_button.config(text="▶")
            self.is_playing = False
            if self.current_song_index < len(self.queue) - 1:
                self.window.after(1000, self.play_next)
    
    def toggle_play(self):
        """Enhanced toggle play with visual feedback"""
        if self.is_playing:
            pygame.mixer.music.pause()
            self.is_playing = False
            self.play_button.config(text="▶")
            # Add visual feedback
            self.play_button.config(bg='#2D2D2D')
            self.now_playing_label.config(text=f"Paused: {self.queue[self.current_song_index]['title']}")
        else:
            if self.current_url:
                pygame.mixer.music.unpause()
                self.is_playing = True
                self.play_button.config(text="⏸")
                # Add visual feedback
                self.play_button.config(bg='#4CAF50')  # Green when playing
                self.now_playing_label.config(text=f"Now Playing: {self.queue[self.current_song_index]['title']}")
            elif self.queue:
                if self.current_song_index == -1:
                    self.current_song_index = 0
                song = self.queue[self.current_song_index]
                threading.Thread(target=self.play_music, 
                               args=(song['url'], song['title']), 
                               daemon=True).start()
    
    def stop_music(self):
        pygame.mixer.music.stop()
        pygame.mixer.music.unload()  # Unload the current track
        self.is_playing = False
        self.play_button.config(text="▶")
        self.now_playing_label.config(text="Not Playing")
        self.current_url = None  # Reset current URL
    
    def play_next(self):
        """Play next song in queue"""
        if self.current_song_index < len(self.queue) - 1:
            self.current_song_index += 1
            song = self.queue[self.current_song_index]
            threading.Thread(target=self.play_music, 
                           args=(song['url'], song['title']), 
                           daemon=True).start()
            self.queue_listbox.selection_clear(0, tk.END)
            self.queue_listbox.selection_set(self.current_song_index)
            self.queue_listbox.see(self.current_song_index)
        else:
            if self.replay_queue and self.queue:  # Check replay mode here too
                self.current_song_index = 0
                song = self.queue[0]
                threading.Thread(target=self.play_music, 
                               args=(song['url'], song['title']), 
                               daemon=True).start()
                self.queue_listbox.selection_clear(0, tk.END)
                self.queue_listbox.selection_set(0)
                self.queue_listbox.see(0)
            else:
                # Reset to stopped state if we're at the end of queue
                self.stop_music()
                self.now_playing_label.config(text="End of Queue")
    
    def play_previous(self):
        """Handle previous song or restart current song"""
        # Only allow previous if music is playing or paused
        if self.current_url and self.current_song_index >= 0:
            if pygame.mixer.music.get_pos() > 3000:  # More than 3 seconds
                # Just restart current song
                pygame.mixer.music.rewind()
                pygame.mixer.music.play()
                self.is_playing = True
                self.play_button.config(text="⏸")
                return
            
            # Go to previous song if within first 3 seconds
            if self.current_song_index > 0:  # Check if we can go to previous song
                self.current_song_index -= 1
                song = self.queue[self.current_song_index]
                threading.Thread(target=self.play_music, 
                               args=(song['url'], song['title']), 
                               daemon=True).start()
                self.queue_listbox.selection_clear(0, tk.END)
                self.queue_listbox.selection_set(self.current_song_index)
                self.queue_listbox.see(self.current_song_index)
            else:
                # If at first song, just restart it
                pygame.mixer.music.rewind()
                pygame.mixer.music.play()
                self.is_playing = True
                self.play_button.config(text="⏸")
    
    def remove_selected(self):
        selection = self.queue_listbox.curselection()
        if selection:
            index = selection[0]
            self.queue_listbox.delete(index)
            removed_song = self.queue.pop(index)
            
            # Update current_song_index and playback
            if index == self.current_song_index:
                self.stop_music()
                if index < len(self.queue):
                    # Play next song if available
                    self.play_next()
                elif self.queue:
                    # Play last song if we removed the last item
                    self.current_song_index = len(self.queue) - 1
                    self.play_next()
            elif index < self.current_song_index:
                self.current_song_index -= 1
    
    def set_volume(self, value):
        """Set both pygame and system volume"""
        volume = float(value) / 100.0
        # Set pygame volume
        pygame.mixer.music.set_volume(volume)
        # Update label
        self.volume_label.config(text=f"{int(float(value))}%")
        # Update volume icon
        self.update_volume_icon(value)
        # Update mute state
        self.is_muted = (float(value) == 0)
        # Set system volume
        if self.volume_controller:
            try:
                self.volume_controller.SetMasterVolumeLevelScalar(volume, None)
            except Exception as e:
                print(f"Could not set system volume: {e}")
    
    def check_music_end(self):
        """Check if current song has ended and handle next song"""
        if self.is_playing:
            # Check if music is actually playing
            if not pygame.mixer.music.get_busy() and not pygame.mixer.get_init() is None:
                # Double check with a small delay to avoid false triggers
                self.window.after(500, self.confirm_song_end)
        
        # Check again after 1 second
        self.window.after(1000, self.check_music_end)

    def confirm_song_end(self):
        """Double check if song has actually ended"""
        if self.is_playing and not pygame.mixer.music.get_busy():
            # Song has definitely ended
            if self.current_song_index < len(self.queue) - 1:
                self.play_next()
            else:
                if self.replay_queue and self.queue:  # If replay is on and queue isn't empty
                    self.current_song_index = -1  # Reset to start
                    self.play_next()
                    self.queue_listbox.selection_clear(0, tk.END)
                    self.queue_listbox.selection_set(0)
                    self.queue_listbox.see(0)
                else:
                    self.stop_music()
                    self.now_playing_label.config(text="End of Queue")
    
    def toggle_play_keyboard(self, event=None):
        self.toggle_play()
    
    def play_previous_keyboard(self, event=None):
        self.play_previous()
    
    def play_next_keyboard(self, event=None):
        self.play_next()
    
    def volume_up(self, event=None):
        current_volume = self.volume_slider.get()
        new_volume = min(100, current_volume + 5)
        self.volume_slider.set(new_volume)
        self.set_volume(new_volume)
    
    def volume_down(self, event=None):
        current_volume = self.volume_slider.get()
        new_volume = max(0, current_volume - 5)
        self.volume_slider.set(new_volume)
        self.set_volume(new_volume)
    
    def on_entry_click(self, event):
        """Function that gets called whenever search entry is clicked"""
        if self.search_entry.get() == "Search for a song...":
            self.search_entry.delete(0, tk.END)  # Delete placeholder
            self.search_entry.config(fg='white')  # Change text color to white
    
    def on_focus_out(self, event):
        """Function that gets called whenever focus is lost from entry"""
        if not self.search_entry.get():  # Only add placeholder if entry is empty
            self.search_entry.insert(0, "Search for a song...")
            self.search_entry.config(fg='grey')
    
    def search_and_add(self, event=None):
        """Search YouTube and add the top result to queue"""
        query = self.search_var.get().strip()
        if query and query != "Search for a song...":
            try:
                # Search for the video with updated options
                search = VideosSearch(query, limit=1, region='US')
                results = search.result()
                
                if results and results['result']:
                    video = results['result'][0]
                    url = video['link']
                    title = video['title']
                    duration = video.get('duration', 'Unknown')
                    
                    # Add to queue with duration info
                    self.queue.append({
                        'url': url, 
                        'title': f"{title} ({duration})"
                    })
                    self.queue_listbox.insert(tk.END, f"{title} ({duration})")
                    
                    # Clear search entry and give it focus
                    self.search_var.set("")
                    self.search_entry.focus_set()  # Keep focus on search entry
                    self.search_entry.config(fg='white')  # Keep text color white
                    
                    # If this is the first song, play it immediately
                    if len(self.queue) == 1:
                        self.current_song_index = 0
                        threading.Thread(target=self.play_music, 
                                      args=(url, f"{title} ({duration})"), 
                                      daemon=True).start()
                        self.queue_listbox.selection_clear(0, tk.END)
                        self.queue_listbox.selection_set(0)
                        self.queue_listbox.see(0)
                else:
                    self.now_playing_label.config(text="No results found")
                    
            except Exception as e:
                # Try alternative search method with same immediate playback logic
                try:
                    with yt_dlp.YoutubeDL({
                        'quiet': True,
                        'format': 'bestaudio/best',
                        'default_search': 'ytsearch',
                        'noplaylist': True
                    }) as ydl:
                        search_query = f"ytsearch1:{query}"
                        result = ydl.extract_info(search_query, download=False)
                        
                        if 'entries' in result and result['entries']:
                            video = result['entries'][0]
                            url = video['webpage_url']
                            title = video['title']
                            duration = str(video.get('duration', 'Unknown'))
                            
                            # Add to queue
                            self.queue.append({
                                'url': url, 
                                'title': f"{title} ({duration}s)"
                            })
                            self.queue_listbox.insert(tk.END, f"{title} ({duration}s)")
                            
                            # Clear search entry and give it focus
                            self.search_var.set("")
                            self.search_entry.focus_set()  # Keep focus on search entry
                            self.search_entry.config(fg='white')  # Keep text color white
                            
                            # If this is the first song, play it immediately
                            if len(self.queue) == 1:
                                self.current_song_index = 0
                                threading.Thread(target=self.play_music, 
                                              args=(url, f"{title} ({duration}s)"), 
                                              daemon=True).start()
                                self.queue_listbox.selection_clear(0, tk.END)
                                self.queue_listbox.selection_set(0)
                                self.queue_listbox.see(0)
                        else:
                            self.now_playing_label.config(text="No results found")
                            
                except Exception as e2:
                    self.now_playing_label.config(text="Could not find song")

        # After adding song to queue_listbox, add remove button
        remove_btn = tk.Button(self.remove_buttons_frame,
                              text="✕",
                              font=('Arial', 10),
                              bg='#FF5252',
                              fg='white',
                              relief='flat',
                              command=lambda idx=len(self.queue)-1: self.remove_song(idx))
        remove_btn.pack(pady=1)

    def remove_song(self, index):
        """Remove song at specified index"""
        if 0 <= index < len(self.queue):
            # Remove from queue and listbox
            self.queue_listbox.delete(index)
            self.queue.pop(index)
            
            # Remove the corresponding button
            for widget in self.remove_buttons_frame.winfo_children():
                widget.destroy()
            
            # Recreate buttons for remaining songs
            for i in range(len(self.queue)):
                remove_btn = tk.Button(self.remove_buttons_frame,
                                     text="✕",
                                     font=('Arial', 10),
                                     bg='#FF5252',
                                     fg='white',
                                     relief='flat',
                                     command=lambda idx=i: self.remove_song(idx))
                remove_btn.pack(pady=1)
            
            # Update playback if needed
            if index == self.current_song_index:
                self.stop_music()
                if index < len(self.queue):
                    self.play_next()
                elif self.queue:
                    self.current_song_index = len(self.queue) - 1
                    self.play_next()
            elif index < self.current_song_index:
                self.current_song_index -= 1

    def toggle_replay(self):
        """Toggle queue replay mode"""
        self.replay_queue = not self.replay_queue
        if self.replay_queue:
            self.replay_button.config(fg='#4CAF50')  # Green when active
        else:
            self.replay_button.config(fg='grey')  # Grey when inactive

    def add_button_hover_effect(self, button):
        """Add hover effect to a button"""
        def on_enter(e):
            button['background'] = '#3D3D3D'  # Lighter background on hover
        
        def on_leave(e):
            button['background'] = '#2D2D2D'  # Original background
        
        def on_click(e):
            button.after(100, lambda: button.config(background='#2D2D2D'))  # Reset after click
        
        button.bind("<Enter>", on_enter)
        button.bind("<Leave>", on_leave)
        button.bind("<Button-1>", on_click)  # Left click

    def voice_search(self):
        """Handle voice search functionality"""
        try:
            # Initialize recognizer
            r = sr.Recognizer()
            
            # Change button color to indicate recording
            self.voice_button.config(bg='#FF5252')  # Red while recording
            self.voice_button.update()
            
            # Use microphone as source
            with sr.Microphone() as source:
                # Update label to show listening status
                self.now_playing_label.config(text="Listening... Speak now")
                
                # Adjust for ambient noise
                r.adjust_for_ambient_noise(source, duration=0.5)
                
                # Listen for audio
                audio = r.listen(source, timeout=5, phrase_time_limit=5)
                
                # Update label to show processing status
                self.now_playing_label.config(text="Processing speech...")
                
                # Recognize speech
                query = r.recognize_google(audio)
                
                # Set the search entry text
                self.search_var.set(query)
                self.search_entry.config(fg='white')  # Ensure text is visible
                
                # Perform search
                self.search_and_add()
                
        except sr.WaitTimeoutError:
            self.now_playing_label.config(text="No speech detected. Please try again.")
        except sr.RequestError:
            self.now_playing_label.config(text="Could not connect to speech recognition service.")
        except sr.UnknownValueError:
            self.now_playing_label.config(text="Could not understand audio. Please try again.")
        except Exception as e:
            self.now_playing_label.config(text=f"Error: {str(e)}")
        finally:
            # Reset button color
            self.voice_button.config(bg='#4CAF50')

    def on_mouse_wheel(self, event):
        """Handle mouse wheel volume control"""
        current_volume = self.volume_slider.get()
        # Determine direction
        if event.num == 5 or event.delta < 0:  # Down
            new_volume = max(0, current_volume - 5)
        else:  # Up
            new_volume = min(100, current_volume + 5)
        
        # Update volume
        self.volume_slider.set(new_volume)
        self.set_volume(new_volume)

    def toggle_mute(self):
        if not self.is_muted:
            # Store current volume and mute
            self.last_volume = self.volume_slider.get()
            self.volume_slider.set(0)
            self.set_volume(0)
            self.volume_button.config(text="🔇", fg='grey')
            self.is_muted = True
        else:
            # Restore last volume
            self.volume_slider.set(self.last_volume)
            self.set_volume(self.last_volume)
            self.update_volume_icon(self.last_volume)
            self.is_muted = False

    def update_volume_icon(self, value):
        """Update volume icon based on volume level"""
        if float(value) == 0:
            self.volume_button.config(text="🔇", fg='grey')
        elif float(value) < 50:
            self.volume_button.config(text="🔉", fg='#4CAF50')
        else:
            self.volume_button.config(text="🔊", fg='#4CAF50')

    def on_window_resize(self, event):
        """Handle window resize events"""
        if event.widget == self.window:
            # Update volume slider length based on window width
            new_length = min(200, self.window.winfo_width() // 4)
            self.volume_slider.config(length=new_length)

if __name__ == "__main__":
    check_dependencies()
    MusicPlayer()