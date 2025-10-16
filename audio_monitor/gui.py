"GUI components for the audio monitor."
from typing import Optional, List
import tkinter as tk
from tkinter import messagebox
import numpy as np
import os
import configparser
import sounddevice as sd
import soundfile as sf

from .constants import (
    PADDING, WINDOW_WIDTH, WINDOW_HEIGHT, NUM_BANDS,
    SOUND_THRESHOLD, DEFAULT_CAPTURE_DURATION, AUDIO_SAMPLERATE,
    AUDIO_BLOCKSIZE, CONFIG_FILE, OUTPUT_DIR
)
from .audio_processor import AudioProcessor
from .analyzer import AudioAnalyzer
from .visualizer import Visualizer
from .logger_config import logger

class EqualizerGUI:
    """Main GUI for the audio equalizer monitor."""
    
    def __init__(self, root: tk.Tk, test_timeout: Optional[int] = None):
        """Initialize the GUI. 
        
        Args:
            root: Tkinter root window
            test_timeout: Optional timeout in seconds for test runs.
        """
        self.root = root
        self.test_timeout = test_timeout
        logger.debug(f"EqualizerGUI initialized with test_timeout: {test_timeout}")
        
        self.dark_theme = tk.BooleanVar(value=True)
        self.debug_enabled = tk.BooleanVar(value=False)
        
        self.BUTTON_HEIGHT = 50
        
        self.colors = {
            'bg': '#1E1E1E',
            'accent': '#3C4FE0',
            'text': '#FFFFFF',
            'grid': '#333333',
            'button_bg': '#2D2D2D',
            'button_hover': '#3D3D3D',
            'alert': '#FF4444',
            'success': '#00C853',
            'warning': '#FFD600',
            'bar_colors': {
                'low': '#3C4FE0',
                'mid': '#00C853',
                'high': '#FFD600',
                'peak': '#FF4444'
            }
        }

        self.config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', CONFIG_FILE)
        self.setup_window()
        self._start_loading_screen()
        # Schedule the rest of the initialization to allow the loading animation to play
        self.root.after(500, self._initialize_app_components)

    def _start_loading_screen(self) -> None:
        """Sets up and displays the initial loading screen."""
        logger.debug("Starting loading screen.")
        self.loading_label = tk.Label(
            self.root,
            text="Loading",
            font=('Helvetica', 24, 'bold'),
            fg=self.colors['text'],
            bg=self.colors['bg']
        )
        self.loading_label.place(relx=0.5, rely=0.5, anchor=tk.CENTER)

    def _initialize_app_components(self) -> None:
        """Initializes the main application components after the loading screen."""
        logger.debug("Initializing app components...")
        self.setup_fonts()
        self.setup_window()
        self.setup_variables()
        
        self.root.after(50, self._continue_initialization_step1)

    def _continue_initialization_step1(self) -> None:
        """Continues application initialization (Visualizer, Canvas)."""
        logger.debug("Continuing initialization step 1: Visualizer, Canvas.")
        self.audio_processor = AudioProcessor(callback=self.process_audio) # Initialize here to get NUM_ACTUAL_BANDS
        self.audio_analyzer = AudioAnalyzer()
        self.visualizer = Visualizer(self.root, self.colors, self.fonts, self.audio_processor.NUM_ACTUAL_BANDS, self.audio_processor.band_labels)
        self.canvas = self.visualizer.create_canvas(self.root, WINDOW_WIDTH, WINDOW_HEIGHT, self.BUTTON_HEIGHT)

        self.root.after(50, self._continue_initialization_step2)

    def _continue_initialization_step2(self) -> None:
        """Continues application initialization (Controls, Visualizer setup)."""
        logger.debug("Continuing initialization step 2: Controls, Visualizer setup.")
        self.create_controls()
        self.create_visualizer()
        # Manually trigger a resize event to set initial dimensions for the visualizer
        self.on_window_resize(type('Event', (), {'widget': self.root, 'width': WINDOW_WIDTH, 'height': WINDOW_HEIGHT}))
        self.visualizer.update_layering()

        self.root.after(50, self._continue_initialization_step3)

    def _continue_initialization_step3(self) -> None:
        """Continues application initialization (Audio Processor, Analyzer)."""
        logger.debug("Continuing initialization step 3: Audio Processor, Analyzer.")
        # self.audio_processor and self.audio_analyzer are already initialized in step 1

        self.root.after(50, self._continue_initialization_step4)

    def _continue_initialization_step4(self) -> None:
        """Finalizes application initialization (UI update, Filesystem poll, Destroy spinner, Test Run message)."""
        logger.debug("Continuing initialization step 4: Finalizing.")
        self.start_ui_update()
        self.poll_filesystem()

        # Destroy loading spinner after initialization
        if hasattr(self, 'loading_label') and self.loading_label:
            self.loading_label.destroy()
            logger.debug("Loading label destroyed.")
        
        self.update_filename_label() # Initial call to display the most recent file
        
        # Display Test Run message if in test mode
        if self.test_timeout:
            logger.info(f"Test Run mode active. Application will close in {self.test_timeout} seconds.")
            self.test_message_label = tk.Label(
                self.root,
                text="Test Run",
                font=('Roboto', 48, 'bold'),
                fg='red',
                bg='black'
            )
            self.test_message_label.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
            self.root.update_idletasks()
            
            def update_countdown_message(seconds_left):
                if seconds_left > 0:
                    self.test_message_label.config(text=f"Test Run\nClosing in {seconds_left}...")
                    self.root.after(1000, update_countdown_message, seconds_left - 1)
                else:
                    self.exit_application()
            
            # Schedule the visual countdown
            self.root.after(1000, update_countdown_message, self.test_timeout)
            # Schedule the actual application exit directly
            self.root.after(self.test_timeout * 1000, self.exit_application)

    def exit_application(self) -> None:
        """Exits the application cleanly."""
        logger.info("Exiting application.")
        self._save_window_geometry() # Save geometry before destroying
        self.root.destroy()
        
    def setup_fonts(self) -> None:
        """Setup modern fonts for the interface."""
        logger.debug("Setting up fonts.")
        self.fonts = {
            'title': ('Helvetica', 16, 'bold'),
            'label': ('Helvetica', 12),
            'button': ('Helvetica', 11),
            'small': ('Helvetica', 10),
            'timer': ('Helvetica', 20, 'bold')
        }
        
    def _load_window_geometry(self) -> bool:
        """Loads the window geometry from the config file."""
        config = configparser.ConfigParser()
        if os.path.exists(self.config_path):
            config.read(self.config_path)
            if 'Window' in config and 'geometry' in config['Window']:
                geometry = config['Window']['geometry']
                try:
                    self.root.geometry(geometry)
                    logger.info(f"Loaded window geometry: {geometry}")
                    return True
                except tk.TclError:
                    logger.warning(f"Invalid geometry string in config: {geometry}. Using default.")
            else:
                logger.debug("No window geometry found in config file.")
        else:
            logger.debug("Config file not found. Using default window geometry.")
        return False

    def _save_window_geometry(self) -> None:
        """Saves the current window geometry to the config file."""
        config = configparser.ConfigParser()
        if os.path.exists(self.config_path):
            config.read(self.config_path)
        
        if 'Window' not in config:
            config['Window'] = {}
        
        geometry = self.root.winfo_geometry()
        config['Window']['geometry'] = geometry
        
        with open(self.config_path, 'w') as configfile:
            config.write(configfile)
        logger.info(f"Saved window geometry: {geometry}")

    def setup_window(self) -> None:
        """Configure the main window."""
        logger.debug("Setting up main window.")
        self.root.title('Audio Output Equalizer')
        geometry_loaded = self._load_window_geometry() # Load geometry
        if not geometry_loaded: # If no geometry was loaded, set default
            self.root.geometry(f'{WINDOW_WIDTH}x{WINDOW_HEIGHT}')
        self.root.resizable(True, True)
        self.root.minsize(WINDOW_WIDTH, WINDOW_HEIGHT)
        self.root.configure(bg=self.colors['bg'])
        self.root.bind('<Configure>', self.on_window_resize)
        self.root.bind('<Map>', self.on_window_map)
        self.root.bind('<Unmap>', self.on_window_unmap)
        self.root.protocol("WM_DELETE_WINDOW", self.exit_application) # Bind close button to exit_application
        
        self.window_state = {
            'width': WINDOW_WIDTH,
            'height': WINDOW_HEIGHT,
            'minimized': False
        }
        
        self.BUTTON_FRAME_HEIGHT = 50

    def setup_variables(self) -> None:
        """Initialize instance variables."""
        logger.debug("Setting up instance variables.")
        self.capturing = False
        self.timer_running = False
        self.capture_seconds_left = DEFAULT_CAPTURE_DURATION
        self.band_values = [0.0] * NUM_BANDS
        self.running = True
        self.playback_stream = None # To hold the sounddevice playback stream
        
    def create_modern_button(self, parent, text, command, width=12, state='normal'):
        """Create a modern-styled button."""
        logger.debug(f"Creating modern button: {text}")
        btn = tk.Button(
            parent,
            text=text,
            command=command,
            width=width,
            font=self.fonts['button'],
            bg=self.colors['button_bg'],
            fg=self.colors['text'],
            activebackground=self.colors['button_hover'],
            activeforeground=self.colors['text'],
            relief='flat',
            bd=0,
            state=state
        )
        
        def on_enter(e):
            if btn['state'] != 'disabled':
                btn['background'] = self.colors['button_hover']
        def on_leave(e):
            if btn['state'] != 'disabled':
                btn['background'] = self.colors['button_bg']
                
        btn.bind('<Enter>', on_enter)
        btn.bind('<Leave>', on_leave)
        return btn
        
    def create_controls(self) -> None:
        """Create control buttons and indicators."""
        logger.debug("Creating control buttons...")
        self.button_frame = tk.Frame(self.root, bg=self.colors['button_bg'])
        self.button_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=(0, PADDING))
        logger.debug(f"button_frame packed: side=BOTTOM, fill=X, pady=(0, {PADDING})")
        
        # Configure grid for button_frame
        self.button_frame.grid_rowconfigure(0, weight=1)
        self.button_frame.grid_columnconfigure(0, weight=0) # capture_indicator
        self.button_frame.grid_columnconfigure(1, weight=0) # start_button
        self.button_frame.grid_columnconfigure(2, weight=0) # stop_button
        self.button_frame.grid_columnconfigure(3, weight=0) # analyze_button
        self.button_frame.grid_columnconfigure(4, weight=0) # timer_label
        self.button_frame.grid_columnconfigure(5, weight=1) # filename_entry (expands)
        logger.debug("Grid configured for button_frame.")
        
        self.capture_indicator = tk.Label(
            self.button_frame,
            text="●",
            fg=self.colors['bg'],
            bg=self.colors['button_bg'],
            font=('Arial', 18, 'bold')
        )
        self.capture_indicator.grid(row=0, column=0, padx=(20, 10), sticky='w')
        logger.debug(f"capture_indicator grid: row=0, column=0, padx=(20, 10), sticky=w")
        
        self.start_button = self.create_modern_button(
            self.button_frame,
            "Start Capture",
            self.start_capture
        )
        self.start_button.grid(row=0, column=1, padx=(0, 10), sticky='w')
        logger.debug(f"start_button grid: row=0, column=1, padx=(0, 10), sticky=w")
        
        self.stop_button = self.create_modern_button(
            self.button_frame,
            "Stop Capture",
            self.stop_capture,
            state='disabled'
        )
        self.stop_button.grid(row=0, column=2, padx=(0, 10), sticky='w')
        logger.debug(f"stop_button grid: row=0, column=2, padx=(0, 10), sticky=w")
        
        self.analyze_button = self.create_modern_button(
            self.button_frame,
            "Analyze",
            self.analyze_file,
            width=10
        )
        self.analyze_button.grid(row=0, column=3, padx=(0, 10), sticky='w')
        logger.debug(f"analyze_button grid: row=0, column=3, padx=(0, 10), sticky=w")
        
        self.timer_label = tk.Label(
            self.button_frame,
            text="05:00",
            fg=self.colors['text'],
            bg=self.colors['button_bg'],
            font=self.fonts['timer']
        )
        # Initially hide the timer
        self.timer_label.grid(row=0, column=4, padx=(20, 5), sticky='w')
        self.timer_label.grid_remove()
        logger.debug(f"timer_label created and initially hidden.")
        
        self.filename_var = tk.StringVar()
        self.filename_entry = tk.Entry(
            self.button_frame,
            textvariable=self.filename_var,
            fg=self.colors['text'],
            bg=self.colors['button_bg'],
            font=self.fonts['label'],
            state='readonly',
            relief='flat',
            readonlybackground=self.colors['button_bg'],
            borderwidth=0,
            highlightthickness=0
        )
        self.filename_entry.grid(row=0, column=5, padx=(5, 20), sticky='ew')
        logger.debug(f"filename_entry grid: row=0, column=5, padx=(5, 20), sticky=ew")
        
    def create_visualizer(self) -> None:
        """Create the visualizer components."""
        logger.debug("Creating visualizer components.")
        self.visualizer.setup_grid()
        self.visualizer.setup_frequency_bars()
        
    def update_timer_label(self) -> None:
        """Update the capture timer display."""
        mins = self.capture_seconds_left // 60
        secs = self.capture_seconds_left % 60
        self.timer_label.config(text=f"{mins:02d}:{secs:02d}")
        logger.debug(f"Timer label updated to {mins:02d}:{secs:02d}")
        
    def start_capture(self) -> None:
        """Start audio capture."""
        if not self.capturing:
            logger.info("Starting audio capture.")
            self.audio_processor.start_capture()
            self.capturing = True
            self.start_button.config(state='disabled')
            self.stop_button.config(state='normal')
            self.capture_indicator.config(fg='red')
            self.capture_seconds_left = DEFAULT_CAPTURE_DURATION
            self.update_timer_label()
            self.timer_label.grid() # Show the timer
            self.timer_running = True
            self.root.after(1000, self.capture_timer_tick)
        else:
            logger.debug("Attempted to start capture, but already capturing.")
            
    def stop_capture(self) -> None:
        """Stop audio capture."""
        if self.capturing:
            logger.info("Stopping audio capture.")
            filename = self.audio_processor.stop_capture()
            self.capturing = False
            self.start_button.config(state='normal')
            self.stop_button.config(state='disabled')
            self.capture_indicator.config(fg='black')
            self.capture_seconds_left = DEFAULT_CAPTURE_DURATION
            self.update_timer_label()
            self.timer_label.grid_remove() # Hide the timer
            self.timer_running = False
            
            if filename:
                logger.info(f"Audio captured to: {filename}")
                self.update_filename_label()
            else:
                logger.warning("Audio capture stopped, but no filename returned.")
        else:
            logger.debug("Attempted to stop capture, but not currently capturing.")
            
    def capture_timer_tick(self) -> None:
        """Decrements the capture timer and updates the display."""
        if self.timer_running and self.capture_seconds_left > 0:
            self.capture_seconds_left -= 1
            self.update_timer_label()
            if self.capture_seconds_left > 0:
                self.root.after(1000, self.capture_timer_tick)
            else:
                logger.info("Capture timer reached zero. Stopping capture.")
                self.stop_capture()
        else:
            logger.debug("Capture timer tick called but timer not running or already zero.")
            
    def analyze_file(self) -> None:
        """Analyze the current audio file and play it in a loop until the results popup is closed."""
        file_path = self.filename_var.get()
        logger.info(f"Attempting to analyze file: {file_path}")
        if not file_path or not os.path.exists(file_path):
            logger.warning(f"No audio file found or path invalid for analysis: {file_path}")
            messagebox.showinfo("Analyze", "No audio file found to analyze.")
            return
            
        try:
            # Load audio file
            data, samplerate = sf.read(file_path, dtype='float32')
            if data.ndim > 1: # Convert to mono if stereo
                data = data.mean(axis=1)

            # Analyze audio file
            results = self.audio_analyzer.analyze_file(file_path)
            logger.info(f"Analysis results for {file_path}: {results}")
            
            report = "Instrument Detection (YAMNet):\n"
            for instrument, result_data in results.items():
                status = "Yes" if result_data['detected'] else "No"
                report += f"{instrument.title()}: {status} (score: {result_data['score']:.2f})\n"

            # Create a Toplevel window for results and playback control
            self.results_popup = tk.Toplevel(self.root)
            self.results_popup.title("Analysis Results")
            self.results_popup.geometry("400x300")
            self.results_popup.configure(bg=self.colors['bg'])

            # Center the popup window
            self.results_popup.update_idletasks()
            x = self.root.winfo_x() + (self.root.winfo_width() // 2) - (self.results_popup.winfo_width() // 2)
            y = self.root.winfo_y() + (self.root.winfo_height() // 2) - (self.results_popup.winfo_height() // 2)
            self.results_popup.geometry(f"400x300+{x}+{y}")

            # Display analysis report
            report_label = tk.Label(
                self.results_popup,
                text=report,
                font=self.fonts['label'],
                fg=self.colors['text'],
                bg=self.colors['bg'],
                justify=tk.LEFT
            )
            report_label.pack(padx=PADDING, pady=PADDING)

            # Add an OK button to close the popup and stop playback
            ok_button = self.create_modern_button(
                self.results_popup,
                "OK",
                self._stop_playback_and_destroy_popup,
                width=8
            )
            ok_button.pack(pady=(0, PADDING))

            # Play audio in a loop
            self.current_frame = 0
            def play_audio_loop():
                if not hasattr(self, 'results_popup') or not self.results_popup.winfo_exists():
                    if self.playback_stream:
                        self.playback_stream.stop()
                        self.playback_stream.close()
                        self.playback_stream = None
                    return

                if self.playback_stream and self.playback_stream.stopped:
                    self.playback_stream.start()

                blocksize = AUDIO_BLOCKSIZE # Use a reasonable block size for playback
                outdata = data[self.current_frame:self.current_frame + blocksize]
                self.current_frame += blocksize
                if self.current_frame >= len(data):
                    self.current_frame = 0 # Loop back to start

                if self.playback_stream:
                    self.playback_stream.write(outdata)
                self.results_popup.after(1, play_audio_loop) # Schedule next block

            self.playback_stream = sd.OutputStream(
                samplerate=samplerate,
                channels=1, # Assuming mono playback
                dtype='float32',
                callback=None # Using write method for explicit control
            )
            self.playback_stream.start()
            self.results_popup.after(1, play_audio_loop)

            # Bind close button to stop playback
            self.results_popup.protocol("WM_DELETE_WINDOW", self._stop_playback_and_destroy_popup)

        except Exception as e:
            logger.error(f"Error analyzing or playing file {file_path}: {e}", exc_info=True)
            messagebox.showerror("Analysis/Playback Error", f"Error analyzing or playing file: {str(e)}")
            if self.playback_stream:
                self.playback_stream.stop()
                self.playback_stream.close()
                self.playback_stream = None

    def _stop_playback_and_destroy_popup(self) -> None:
        """Stops audio playback and destroys the results popup window."""
        if self.playback_stream:
            self.playback_stream.stop()
            self.playback_stream.close()
            self.playback_stream = None
            logger.info("Audio playback stopped.")
        if hasattr(self, 'results_popup') and self.results_popup.winfo_exists():
            self.results_popup.destroy()
            logger.debug("Analysis results popup destroyed.")

    def process_audio(self, band_values: np.ndarray) -> None:
        """Process incoming audio data for visualization."""
        self.band_values = band_values
        logger.debug(f"Audio processed, band values updated. First 5: {band_values[:5]}")
        
    def start_ui_update(self) -> None:
        """Start the UI update loop."""
        logger.info("Starting UI update loop and audio stream.")
        try:
            self.audio_processor.start_stream()
            self.update_ui()
        except Exception as e:
            logger.error(f"Error starting audio stream or UI update: {e}", exc_info=True)
            messagebox.showerror("Audio Stream Error", f"Failed to start audio stream: {str(e)}\nPlease ensure your audio input device is working and not in use by another application.")
            self.root.destroy()
            return
        
    def stop(self) -> None:
        """Stop all processing and clean up."""
        logger.info("Stopping all processing and cleaning up.")
        self.running = False
        self.audio_processor.stop_stream()
        
    def update_ui(self) -> None:
        """Update the UI elements."""
        self.visualizer.update_frequency_bars(self.band_values)
        if self.running:
            self.root.after(50, self.update_ui)
        else:
            logger.debug("UI update loop stopped.")
            
    def poll_filesystem(self) -> None:
        """Check for new audio files periodically."""
        self.update_filename_label()
        logger.debug("Polling filesystem for new audio files.")
        self.root.after(2000, self.poll_filesystem)
        
    def update_filename_label(self) -> None:
        """Update the filename display with the most recent capture."""
        if not os.path.exists(OUTPUT_DIR):
            self.filename_var.set("")
            logger.debug("Output directory does not exist.")
            return
            
        files = [f for f in os.listdir(OUTPUT_DIR) if f.endswith('.wav')]
        if not files:
            self.filename_var.set("")
            logger.debug("No WAV files found in output directory.")
            return
            
        files.sort(key=lambda f: os.path.getmtime(os.path.join(OUTPUT_DIR, f)), reverse=True)
        most_recent = files[0]
        full_path = os.path.abspath(os.path.join(OUTPUT_DIR, most_recent))
        self.filename_var.set(full_path)
        logger.info(f"Most recent audio file: {full_path}")
        
    def on_window_resize(self, event=None) -> None:
        """Handle window resize events."""
        logger.debug(f"Window resize event. New size: {self.root.winfo_width()}x{self.root.winfo_height()}")
        if hasattr(self, 'visualizer') and self.visualizer and hasattr(self, 'button_frame') and self.button_frame:
            self.visualizer.on_window_resize(event, self.window_state, self.button_frame, self.band_values)
            
    def on_window_map(self, event=None):
        """Handle window restore."""
        logger.debug("Window restored from minimized state.")
        self.window_state['minimized'] = False
        self.root.update_idletasks()
        # Only call on_window_resize if visualizer and button_frame are initialized
        if hasattr(self, 'visualizer') and self.visualizer and hasattr(self, 'button_frame') and self.button_frame:
            self.on_window_resize(type('Event', (), {
                'widget': self.root,
                'width': self.window_state['width'],
                'height': self.window_state['height']
            }))
        
    def on_window_unmap(self, event=None):
        """Handle window minimize."""
        logger.debug("Window minimized.")
        self.window_state['minimized'] = True