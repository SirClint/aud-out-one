"""Constants for the audio monitor application."""

import os

# Window and equalizer parameters
PADDING = 40  # Increased padding for better label visibility
WINDOW_WIDTH = 1200 + 2 * PADDING
WINDOW_HEIGHT = 600 + 2 * PADDING  # Increased height for buttons below graph
NUM_BANDS = 20

# Audio parameters
AUDIO_BLOCKSIZE = 2048
AUDIO_SAMPLERATE = 44100
AUDIO_CHANNELS = 1
SOUND_THRESHOLD = 1e-4
BAR_SCALE = 3.5  # Increase for taller bars
AMP_TOP = 0.6    # Amplitude value that maps to top of display

# Frequency analysis parameters
AUDIBLE_MIN = 20  # Hz
AUDIBLE_MAX = 16000  # Hz - adjusted to ensure better frequency band distribution
LOW_SPLIT = 10000  # Hz

# Capture parameters
DEFAULT_CAPTURE_DURATION = 5 * 60  # 5 minutes in seconds
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', "output")
CONFIG_FILE = "window_config.ini"

# Analysis parameters
YAMNET_MODEL_URL = 'https://tfhub.dev/google/yamnet/1'
YAMNET_CLASS_MAP_URL = 'https://raw.githubusercontent.com/tensorflow/models/master/research/audioset/yamnet/yamnet_class_map.csv'
YAMNET_DETECTION_THRESHOLD = 0.1