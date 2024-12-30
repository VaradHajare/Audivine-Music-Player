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
        self.window.title("Varad's Music Player")
        self.window.configure(bg='#1E1E1E')  # Darker background
        
        # Music player variables
        self.is_playing = False
        self.current_url = None
        self.temp_dir = tempfile.gettempdir()
        self.queue = []
        self.current_song_index = -1
        
        # Set window size and position
        window_width = 1000
        window_height = 700  # Increased height
        self.window.geometry(f'{window_width}x{window_height}')
        self.window.resizable(False, False)  # Fixed window size
        
        # Center window
        self.center_window(window_width, window_height)
        
        # Main container with padding
        self.container = tk.Frame(self.window, bg='#1E1E1E')
        self.container.pack(expand=True, fill='both', padx=30, pady=20)
        
        # Title
        title_label = tk.Label(self.container, 
                             text="Varad's Music Player",
                             font=('Arial', 24, 'bold'),
                             bg='#1E1E1E', fg='#FFFFFF')
        title_label.pack(pady=(0, 20))
        
        # Search Entry and Add Button Frame with modern styling
        self.search_frame = tk.Frame(self.container, bg='#1E1E1E')
        self.search_frame.pack(fill='x', pady=(0, 20))
        
        # Center container for search elements
        search_center = tk.Frame(self.search_frame, bg='#1E1E1E')
        search_center.pack(expand=True, anchor='center')
        
        # Create a rounded frame effect for search bar
        search_container = tk.Frame(search_center, bg='#4CAF50', padx=2, pady=2)  # Green border
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
        
        # Add hover effect for the button
        def on_enter(e):
            self.add_button['background'] = '#45a049'

        def on_leave(e):
            self.add_button['background'] = '#4CAF50'

        self.add_button.bind("<Enter>", on_enter)
        self.add_button.bind("<Leave>", on_leave)
        
        # Add these styles to make the window look better
        style = ttk.Style()
        style.configure('Rounded.TEntry',
                        fieldbackground='#2D2D2D',
                        background='#2D2D2D',
                        foreground='white',
                        borderwidth=0,
                        relief='flat')
        
        # Queue Frame with better styling
        self.queue_frame = tk.Frame(self.container, bg='#2D2D2D')
        self.queue_frame.pack(fill='both', expand=True, pady=20)
        
        # Queue Header
        queue_header = tk.Frame(self.queue_frame, bg='#2D2D2D')
        queue_header.pack(fill='x', padx=10, pady=10)
        
        tk.Label(queue_header, text="Queue", 
                font=('Arial', 14, 'bold'),
                bg='#2D2D2D', fg='white').pack(side=tk.LEFT)
        
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
        self.replay_button.pack(side=tk.RIGHT)
        
        # Queue Listbox with scrollbar
        listbox_frame = tk.Frame(self.queue_frame, bg='#2D2D2D')
        listbox_frame.pack(fill='both', expand=True, padx=10, pady=(0, 10))

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
        now_playing_frame.pack(fill='x', pady=(0, 20))
        
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
        controls_frame.pack(fill='x')
        
        # Buttons Frame
        self.buttons_frame = tk.Frame(controls_frame, bg='#1E1E1E')
        self.buttons_frame.pack(pady=10)
        
        # Control Buttons with better styling
        button_style = {
            'font': ('Arial', 16),
            'bg': '#2D2D2D',
            'fg': 'white',
            'relief': 'flat',
            'width': 4,
            'padx': 10,
            'pady': 5
        }
        
        self.prev_button = tk.Button(self.buttons_frame, text="⏮",
                                   command=self.play_previous, **button_style)
        self.prev_button.pack(side=tk.LEFT, padx=5)
        
        self.play_button = tk.Button(self.buttons_frame, text="▶",
                                   command=self.toggle_play, **button_style)
        self.play_button.pack(side=tk.LEFT, padx=5)
        
        self.next_button = tk.Button(self.buttons_frame, text="⏭",
                                   command=self.play_next, **button_style)
        self.next_button.pack(side=tk.LEFT, padx=5)
        
        self.stop_button = tk.Button(self.buttons_frame, text="⏹",
                                   command=self.stop_music, **button_style)
        self.stop_button.pack(side=tk.LEFT, padx=5)
        
        # Volume Frame
        volume_frame = tk.Frame(controls_frame, bg='#1E1E1E')
        volume_frame.pack(pady=10)
        
        # Volume Label
        tk.Label(volume_frame, text="Volume",
                font=('Arial', 10),
                bg='#1E1E1E', fg='white').pack(side=tk.LEFT, padx=(0, 10))
        
        # Initialize system volume control
        try:
            devices = AudioUtilities.GetSpeakers()
            interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
            self.volume_controller = cast(interface, POINTER(IAudioEndpointVolume))
            # Get current system volume
            current_vol = round((self.volume_controller.GetMasterVolumeLevelScalar() * 100))
        except Exception as e:
            print(f"Could not initialize system volume control: {e}")
            self.volume_controller = None
            current_vol = 50

        # Update volume slider initialization to use system volume
        self.volume_slider = tk.Scale(volume_frame,
                                    from_=0, to=100,
                                    orient=tk.HORIZONTAL,
                                    length=200,
                                    bg='#2D2D2D',
                                    fg='white',
                                    troughcolor='#4CAF50',
                                    highlightthickness=0,
                                    sliderrelief='flat',
                                    command=self.set_volume)
        self.volume_slider.set(current_vol)  # Set to current system volume
        self.volume_slider.pack(side=tk.LEFT)
        
        # Start checking for end of track
        self.check_music_end()
        
        # Bind double-click to play selected song
        self.queue_listbox.bind('<Double-Button-1>', self.play_selected)
        
        # Add keyboard bindings
        self.window.bind('<space>', self.toggle_play_keyboard)
        self.window.bind('<Left>', self.play_previous_keyboard)
        self.window.bind('<Right>', self.play_next_keyboard)
        self.window.bind('<Up>', self.volume_up)
        self.window.bind('<Down>', self.volume_down)
        
        self.window.mainloop()
    
    def center_window(self, width, height):
        screen_width = self.window.winfo_screenwidth()
        screen_height = self.window.winfo_screenheight()
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        self.window.geometry(f'{width}x{height}+{x}+{y}')
    
    def play_selected(self, event=None):
        selection = self.queue_listbox.curselection()
        if selection:
            index = selection[0]
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
                'ffmpeg_location': resource_path('ffmpeg.exe'),
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
        if self.is_playing:
            pygame.mixer.music.pause()
            self.is_playing = False
            self.play_button.config(text="▶")
            self.now_playing_label.config(text=f"Paused: {self.queue[self.current_song_index]['title']}")
        else:
            if self.current_url:
                pygame.mixer.music.unpause()
                self.is_playing = True
                self.play_button.config(text="⏸")
                self.now_playing_label.config(text=f"Now Playing: {self.queue[self.current_song_index]['title']}")
            elif self.queue:
                # If no current song but queue exists, start playing
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

if __name__ == "__main__":
    check_dependencies()
    MusicPlayer()