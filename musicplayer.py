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

pygame.mixer.init()

def resource_path(relative_path):
    try:
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
        self.window.title("Audivine Music Player")
        self.window.configure(bg='#1E1E1E')
        
        self.window.attributes('-toolwindow', False)
        self.window.wm_attributes('-topmost', False)
        self.window.resizable(True, True)
        
        self.window.minsize(800, 600)
        
        self.is_playing = False
        self.current_url = None
        self.temp_dir = tempfile.gettempdir()
        self.queue = []
        self.current_song_index = -1
        
        screen_width = self.window.winfo_screenwidth()
        screen_height = self.window.winfo_screenheight()
        self.window.geometry(f'{screen_width}x{screen_height}+0+0')
        
        self.window.resizable(True, True)
        
        self.container = tk.Frame(self.window, bg='#1E1E1E')
        self.container.pack(expand=True, fill='both', padx=40, pady=30)
        
        self.container.grid_columnconfigure(0, weight=1)
        self.container.grid_rowconfigure(3, weight=1)
        
        title_frame = tk.Frame(self.container, bg='#1E1E1E')
        title_frame.grid(row=0, column=0, pady=(0, 30), sticky='ew')
        
        title_frame.grid_columnconfigure(1, weight=1)
        
        left_decor = tk.Label(title_frame, 
                             text="♫ ♪ ═══",
                             font=('Consolas', 24),
                             bg='#1E1E1E',
                             fg='#4CAF50')
        left_decor.grid(row=0, column=0, padx=10)
        
        title_label = tk.Label(title_frame, 
                              text="AUDIVINE",
                              font=('Arial Black', 32, 'bold'),
                              bg='#1E1E1E',
                              fg='#4CAF50',
                              pady=5)
        title_label.grid(row=0, column=1)
        
        right_decor = tk.Label(title_frame, 
                              text="═══ ♪ ♫",
                              font=('Consolas', 24),
                              bg='#1E1E1E',
                              fg='#4CAF50')
        right_decor.grid(row=0, column=2, padx=10)
        
        def glow_effect():
            current_color = title_label.cget("fg")
            if current_color == '#4CAF50':  # Base green
                title_label.config(fg='#45a049')  # Darker green
            else:
                title_label.config(fg='#4CAF50')  # Back to base green
            self.window.after(1000, glow_effect)  # Repeat every 1 second
        
        glow_effect()
        
        self.search_frame = tk.Frame(self.container, bg='#1E1E1E')
        self.search_frame.grid(row=1, column=0, pady=(0, 25), sticky='ew')
        self.search_frame.grid_columnconfigure(0, weight=1)
        
        search_center = tk.Frame(self.search_frame, bg='#1E1E1E')
        search_center.grid(row=0, column=0)
        
        search_container = tk.Frame(search_center, bg='#4CAF50', padx=2, pady=2)
        search_container.pack(side=tk.LEFT, padx=5)
        
        self.search_var = tk.StringVar()
        self.search_entry = tk.Entry(search_container, textvariable=self.search_var,
                                    width=50, font=('Arial', 12),
                                    bg='#2D2D2D', fg='white',
                                    insertbackground='white',
                                    relief='flat')
        self.search_entry.pack(padx=1, pady=1, ipady=8)
        
        self.search_entry.insert(0, "Search for a song...")
        self.search_entry.bind('<FocusIn>', self.on_entry_click)
        self.search_entry.bind('<FocusOut>', self.on_focus_out)
        self.search_entry.bind('<Return>', self.search_and_add)
        self.search_entry.config(fg='grey')
        
        self.add_button = tk.Button(search_center, text="Search & Add",
                                   command=self.search_and_add,
                                   font=('Arial', 11, 'bold'),
                                   bg='#4CAF50', fg='white',
                                   relief='flat',
                                   padx=20, pady=8,
                                   cursor='hand2')
        self.add_button.pack(side=tk.LEFT, padx=5)
        
        self.voice_button = tk.Button(search_center, text="🎤",
                                    font=('Arial', 14, 'bold'),
                                    bg='#4CAF50', fg='white',
                                    relief='flat',
                                    padx=10, pady=6,
                                    cursor='hand2',
                                    command=self.voice_search)
        self.voice_button.pack(side=tk.LEFT, padx=5)
        
        for button in [self.add_button, self.voice_button]:
            def on_enter(e, btn=button):
                btn['background'] = '#45a049'

            def on_leave(e, btn=button):
                btn['background'] = '#4CAF50'

            button.bind("<Enter>", on_enter)
            button.bind("<Leave>", on_leave)
        
        style = ttk.Style()
        style.configure('Rounded.TEntry',
                        fieldbackground='#2D2D2D',
                        background='#2D2D2D',
                        foreground='white',
                        borderwidth=0,
                        relief='flat')
        
        self.queue_frame = tk.Frame(self.container, bg='#2D2D2D')
        self.queue_frame.grid(row=2, column=0, sticky='nsew', pady=20)
        self.queue_frame.grid_columnconfigure(0, weight=1)
        self.queue_frame.grid_rowconfigure(1, weight=1)
        
        queue_header = tk.Frame(self.queue_frame, bg='#2D2D2D')
        queue_header.grid(row=0, column=0, sticky='ew', padx=10, pady=10)
        queue_header.grid_columnconfigure(1, weight=1)
        
        tk.Label(queue_header, text="Queue", 
                font=('Arial', 14, 'bold'),
                bg='#2D2D2D', fg='white').grid(row=0, column=0, sticky='w')
        
        self.replay_queue = False
        self.replay_button = tk.Button(queue_header,
                                      text="🔁",
                                      font=('Arial', 14),
                                      bg='#2D2D2D',
                                      fg='grey',
                                      relief='flat',
                                      command=self.toggle_replay,
                                      cursor='hand2')
        self.replay_button.grid(row=0, column=2, sticky='e')
        
        listbox_frame = tk.Frame(self.queue_frame, bg='#2D2D2D')
        listbox_frame.grid(row=1, column=0, sticky='nsew', padx=10, pady=(0, 10))
        listbox_frame.grid_columnconfigure(0, weight=1)
        listbox_frame.grid_rowconfigure(0, weight=1)
        
        self.queue_container = tk.Frame(listbox_frame, bg='#2D2D2D')
        self.queue_container.pack(side=tk.LEFT, fill='both', expand=True)
        
        self.queue_listbox = tk.Listbox(self.queue_container, 
                                       font=('Arial', 11),
                                       bg='#333333', fg='white',
                                       selectmode=tk.SINGLE,
                                       relief='flat',
                                       activestyle='none',
                                       selectbackground='#4CAF50',
                                       selectforeground='white')
        self.queue_listbox.pack(side=tk.LEFT, fill='both', expand=True)
        
        self.remove_buttons_frame = tk.Frame(self.queue_container, bg='#333333')
        self.remove_buttons_frame.pack(side=tk.RIGHT, fill='y')
        
        scrollbar = tk.Scrollbar(listbox_frame, orient="vertical",
                                 command=self.queue_listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill='y')
        self.queue_listbox.config(yscrollcommand=scrollbar.set)
        
        now_playing_frame = tk.Frame(self.container, bg='#2D2D2D')
        now_playing_frame.grid(row=3, column=0, sticky='ew', pady=(0, 20))
        
        self.now_playing_label = tk.Label(now_playing_frame, 
                                        text="Not Playing",
                                        font=('Arial', 12),
                                        bg='#2D2D2D', fg='white')
        self.now_playing_label.pack(pady=10)
        
        shortcuts_label = tk.Label(now_playing_frame,
                                 text="Shortcuts: Space (Play/Pause) | ← → (Previous/Next) | ↑ ↓ (Volume)",
                                 font=('Arial', 10),
                                 bg='#2D2D2D', fg='#888888')
        shortcuts_label.pack(pady=(0, 5))
        
        controls_frame = tk.Frame(self.container, bg='#1E1E1E')
        controls_frame.grid(row=4, column=0, sticky='ew')
        controls_frame.grid_columnconfigure(0, weight=1)
        
        button_style = {
            'font': ('Arial', 16),
            'bg': '#2D2D2D',
            'fg': 'white',
            'relief': 'flat',
            'width': 4,
            'padx': 20,
            'pady': 10,
            'cursor': 'hand2',
            'activebackground': '#4CAF50',
            'activeforeground': 'white',
        }
        
        self.buttons_frame = tk.Frame(controls_frame, bg='#1E1E1E')
        self.buttons_frame.grid(row=0, column=0, pady=20)
        
        self.prev_button = tk.Button(self.buttons_frame, text="⏮",
                                   command=self.play_previous, **button_style)
        self.prev_button.grid(row=0, column=0, padx=10)
        
        self.play_button = tk.Button(self.buttons_frame, text="▶",
                                   command=self.toggle_play, **button_style)
        self.play_button.grid(row=0, column=1, padx=10)
        
        self.next_button = tk.Button(self.buttons_frame, text="⏭",
                                   command=self.play_next, **button_style)
        self.next_button.grid(row=0, column=2, padx=10)
        
        self.stop_button = tk.Button(self.buttons_frame, text="⏹",
                                   command=self.stop_music, **button_style)
        self.stop_button.grid(row=0, column=3, padx=10)
        
        for button in [self.prev_button, self.play_button, self.next_button, self.stop_button]:
            self.add_button_hover_effect(button)
        
        volume_frame = tk.Frame(controls_frame, bg='#1E1E1E')
        volume_frame.grid(row=1, column=0, pady=15, sticky='ew')
        volume_frame.grid_columnconfigure(0, weight=1)
        
        volume_container = tk.Frame(volume_frame, bg='#2D2D2D', padx=20, pady=15)
        volume_container.grid(row=0, column=0)
        
        try:
            devices = AudioUtilities.GetSpeakers()
            interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
            self.volume_controller = cast(interface, POINTER(IAudioEndpointVolume))
            current_vol = round((self.volume_controller.GetMasterVolumeLevelScalar() * 100))
        except Exception as e:
            print(f"Could not initialize system volume control: {e}")
            self.volume_controller = None
            current_vol = 50
        
        self.last_volume = current_vol
        self.is_muted = False
        
        self.volume_button = tk.Button(volume_container,
                                     text="🔊",
                                     font=('Arial', 14),
                                     bg='#2D2D2D',
                                     fg='#4CAF50',
                                     relief='flat',
                                     bd=0,
                                     cursor='hand2',
                                     command=self.toggle_mute)
        self.volume_button.grid(row=0, column=0, padx=(0, 10))
        
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
        
        self.volume_slider.set(current_vol)
        self.volume_slider.grid(row=0, column=1, padx=(10, 15), pady=8)
        
        self.volume_label = tk.Label(volume_container,
                                    text=f"{current_vol}%",
                                    font=('Arial', 10),
                                    bg='#2D2D2D',
                                    fg='#FFFFFF',
                                    width=4)
        self.volume_label.grid(row=0, column=2)
        
        self.volume_slider.bind('<MouseWheel>', self.on_mouse_wheel)
        self.volume_slider.bind('<Button-4>', self.on_mouse_wheel)
        self.volume_slider.bind('<Button-5>', self.on_mouse_wheel)
        
        self.check_music_end()
        
        self.queue_listbox.bind('<Button-1>', self.play_selected)
        
        self.window.bind('<space>', self.toggle_play_keyboard)
        self.window.bind('<Left>', self.play_previous_keyboard)
        self.window.bind('<Right>', self.play_next_keyboard)
        self.window.bind('<Up>', self.volume_up)
        self.window.bind('<Down>', self.volume_down)
        
        self.volume_slider.config(length=min(200, self.window.winfo_width() // 4))
        
        self.window.bind('<Configure>', self.on_window_resize)
        
        self.window.mainloop()
    
    def center_window(self, width, height):
        self.window.lift()
        self.window.attributes('-topmost', True)
        self.window.attributes('-topmost', False)
    
    def play_selected(self, event=None):
        selection = self.queue_listbox.curselection()
        if selection:
            index = selection[0]
            if index != self.current_song_index:
                self.current_song_index = index - 1
                self.play_next()
    
    def add_to_queue(self):
        url = self.url_var.get().strip()
        if url:
            try:
                with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
                    info = ydl.extract_info(url, download=False)
                    title = info.get('title', 'Unknown Title')
                
                self.queue.append({'url': url, 'title': title})
                self.queue_listbox.insert(tk.END, title)
                self.url_var.set("")
                
                if not self.is_playing and len(self.queue) == 1:
                    self.current_song_index = -1
                    self.play_next()
                    
            except Exception as e:
                self.now_playing_label.config(text=f"Error: {str(e)}")
                print(f"Error adding to queue: {str(e)}")
    
    def play_music(self, url, title):
        try:
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

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                video_id = info['id']
                temp_file = os.path.join(self.temp_dir, f'{video_id}.mp3')
                
                if not os.path.exists(temp_file):
                    ydl.download([url])

                pygame.mixer.music.stop()
                pygame.mixer.music.unload()
                pygame.mixer.music.load(temp_file)
                pygame.mixer.music.set_volume(self.volume_slider.get() / 100.0)
                pygame.mixer.music.play()
                
                self.is_playing = True
                self.play_button.config(text="⏸")
                self.current_url = url
                self.now_playing_label.config(text=f"Now Playing: {title}")
                
        except Exception as e:
            print(f"Playback error: {str(e)}")
            self.play_button.config(text="▶")
            self.is_playing = False
            if self.current_song_index < len(self.queue) - 1:
                self.window.after(1000, self.play_next)
    
    def toggle_play(self):
        if self.is_playing:
            pygame.mixer.music.pause()
            self.is_playing = False
            self.play_button.config(text="▶")
            self.play_button.config(bg='#2D2D2D')
            self.now_playing_label.config(text=f"Paused: {self.queue[self.current_song_index]['title']}")
        else:
            if self.current_url:
                pygame.mixer.music.unpause()
                self.is_playing = True
                self.play_button.config(text="⏸")
                self.play_button.config(bg='#4CAF50')
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
        pygame.mixer.music.unload()
        self.is_playing = False
        self.play_button.config(text="▶")
        self.now_playing_label.config(text="Not Playing")
        self.current_url = None
    
    def play_next(self):
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
            if self.replay_queue and self.queue:
                self.current_song_index = 0
                song = self.queue[0]
                threading.Thread(target=self.play_music, 
                               args=(song['url'], song['title']), 
                               daemon=True).start()
                self.queue_listbox.selection_clear(0, tk.END)
                self.queue_listbox.selection_set(0)
                self.queue_listbox.see(0)
            else:
                self.stop_music()
                self.now_playing_label.config(text="End of Queue")
    
    def play_previous(self):
        if self.current_url and self.current_song_index >= 0:
            if pygame.mixer.music.get_pos() > 3000:
                pygame.mixer.music.rewind()
                pygame.mixer.music.play()
                self.is_playing = True
                self.play_button.config(text="⏸")
                return
            
            if self.current_song_index > 0:
                self.current_song_index -= 1
                song = self.queue[self.current_song_index]
                threading.Thread(target=self.play_music, 
                               args=(song['url'], song['title']), 
                               daemon=True).start()
                self.queue_listbox.selection_clear(0, tk.END)
                self.queue_listbox.selection_set(self.current_song_index)
                self.queue_listbox.see(self.current_song_index)
            else:
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
            
            if index == self.current_song_index:
                self.stop_music()
                if index < len(self.queue):
                    self.play_next()
                elif self.queue:
                    self.current_song_index = len(self.queue) - 1
                    self.play_next()
            elif index < self.current_song_index:
                self.current_song_index -= 1
    
    def set_volume(self, value):
        volume = float(value) / 100.0
        pygame.mixer.music.set_volume(volume)
        self.volume_label.config(text=f"{int(float(value))}%")
        self.update_volume_icon(value)
        self.is_muted = (float(value) == 0)
        if self.volume_controller:
            try:
                self.volume_controller.SetMasterVolumeLevelScalar(volume, None)
            except Exception as e:
                print(f"Could not set system volume: {e}")
    
    def check_music_end(self):
        if self.is_playing:
            if not pygame.mixer.music.get_busy() and not pygame.mixer.get_init() is None:
                self.window.after(500, self.confirm_song_end)
        
        self.window.after(1000, self.check_music_end)

    def confirm_song_end(self):
        if self.is_playing and not pygame.mixer.music.get_busy():
            if self.current_song_index < len(self.queue) - 1:
                self.play_next()
            else:
                if self.replay_queue and self.queue:
                    self.current_song_index = -1
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
        if self.search_entry.get() == "Search for a song...":
            self.search_entry.delete(0, tk.END)
            self.search_entry.config(fg='white')
    
    def on_focus_out(self, event):
        if not self.search_entry.get():
            self.search_entry.insert(0, "Search for a song...")
            self.search_entry.config(fg='grey')
    
    def search_and_add(self, event=None):
        query = self.search_var.get().strip()
        if query and query != "Search for a song...":
            try:
                search = VideosSearch(query, limit=1, region='US')
                results = search.result()
                
                if results and results['result']:
                    video = results['result'][0]
                    url = video['link']
                    title = video['title']
                    duration = video.get('duration', 'Unknown')
                    
                    self.queue.append({
                        'url': url, 
                        'title': f"{title} ({duration})"
                    })
                    self.queue_listbox.insert(tk.END, f"{title} ({duration})")
                    
                    self.search_var.set("")
                    self.search_entry.focus_set()
                    self.search_entry.config(fg='white')
                    
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
                            
                            self.queue.append({
                                'url': url, 
                                'title': f"{title} ({duration}s)"
                            })
                            self.queue_listbox.insert(tk.END, f"{title} ({duration}s)")
                            
                            self.search_var.set("")
                            self.search_entry.focus_set()
                            self.search_entry.config(fg='white')
                            
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

        remove_btn = tk.Button(self.remove_buttons_frame,
                              text="✕",
                              font=('Arial', 10),
                              bg='#FF5252',
                              fg='white',
                              relief='flat',
                              command=lambda idx=len(self.queue)-1: self.remove_song(idx))
        remove_btn.pack(pady=1)

    def remove_song(self, index):
        if 0 <= index < len(self.queue):
            self.queue_listbox.delete(index)
            self.queue.pop(index)
            
            for widget in self.remove_buttons_frame.winfo_children():
                widget.destroy()
            
            for i in range(len(self.queue)):
                remove_btn = tk.Button(self.remove_buttons_frame,
                                     text="✕",
                                     font=('Arial', 10),
                                     bg='#FF5252',
                                     fg='white',
                                     relief='flat',
                                     command=lambda idx=i: self.remove_song(idx))
                remove_btn.pack(pady=1)
            
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
        self.replay_queue = not self.replay_queue
        if self.replay_queue:
            self.replay_button.config(fg='#4CAF50')
        else:
            self.replay_button.config(fg='grey')

    def add_button_hover_effect(self, button):
        def on_enter(e):
            button['background'] = '#3D3D3D'
        
        def on_leave(e):
            button['background'] = '#2D2D2D'
        
        def on_click(e):
            button.after(100, lambda: button.config(background='#2D2D2D'))
        
        button.bind("<Enter>", on_enter)
        button.bind("<Leave>", on_leave)
        button.bind("<Button-1>", on_click)

    def voice_search(self):
        try:
            r = sr.Recognizer()
            
            self.voice_button.config(bg='#FF5252')
            self.voice_button.update()
            
            with sr.Microphone() as source:
                self.now_playing_label.config(text="Listening... Speak now")
                
                r.adjust_for_ambient_noise(source, duration=0.5)
                
                audio = r.listen(source, timeout=5, phrase_time_limit=5)
                
                self.now_playing_label.config(text="Processing speech...")
                
                query = r.recognize_google(audio)
                
                self.search_var.set(query)
                self.search_entry.config(fg='white')
                
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
            self.voice_button.config(bg='#4CAF50')

    def on_mouse_wheel(self, event):
        current_volume = self.volume_slider.get()
        if event.num == 5 or event.delta < 0:
            new_volume = max(0, current_volume - 5)
        else:
            new_volume = min(100, current_volume + 5)
        
        self.volume_slider.set(new_volume)
        self.set_volume(new_volume)

    def toggle_mute(self):
        if not self.is_muted:
            self.last_volume = self.volume_slider.get()
            self.volume_slider.set(0)
            self.set_volume(0)
            self.volume_button.config(text="🔇", fg='grey')
            self.is_muted = True
        else:
            self.volume_slider.set(self.last_volume)
            self.set_volume(self.last_volume)
            self.update_volume_icon(self.last_volume)
            self.is_muted = False

    def update_volume_icon(self, value):
        if float(value) == 0:
            self.volume_button.config(text="🔇", fg='grey')
        elif float(value) < 50:
            self.volume_button.config(text="🔉", fg='#4CAF50')
        else:
            self.volume_button.config(text="🔊", fg='#4CAF50')

    def on_window_resize(self, event):
        if event.widget == self.window:
            new_length = min(200, self.window.winfo_width() // 4)
            self.volume_slider.config(length=new_length)

if __name__ == "__main__":
    check_dependencies()
    MusicPlayer()