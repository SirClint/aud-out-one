from typing import List, Optional, Tuple, Callable
import numpy as np
import sounddevice as sd
import wave
import datetime
import os
from .constants import (
    AUDIO_BLOCKSIZE, AUDIO_SAMPLERATE, AUDIO_CHANNELS,
    AUDIBLE_MIN, AUDIBLE_MAX, NUM_BANDS, OUTPUT_DIR
)
from .logger_config import logger

class AudioProcessor:
    """Handles audio capture and processing."""
    
    def __init__(self, callback: Optional[Callable] = None):
        """Initialize the audio processor.
        
        Args:
            callback: Optional callback function for processing audio data
        """
        self.callback = callback
        self.capturing = False
        self.audio_frames: List[np.ndarray] = []
        self.capture_filename: Optional[str] = None
        self._setup_frequency_bands()
        # Dynamically set NUM_BANDS based on the actual number of bands created
        self.NUM_ACTUAL_BANDS = len(self.band_bin_indices)
        self.prev_band_values = np.zeros(self.NUM_ACTUAL_BANDS)
        logger.debug("AudioProcessor initialized.")
        
    def _setup_frequency_bands(self) -> None:
        """Set up frequency bands for analysis."""
        logger.debug("Setting up frequency bands.")
        self.freqs = np.fft.rfftfreq(AUDIO_BLOCKSIZE, 1.0 / AUDIO_SAMPLERATE)
        self.n_bins = len(self.freqs)
        
        self.band_bin_indices = []
        self.band_labels = []

        # Custom band for 20-49 Hz
        bass_min = 20
        bass_max = 49
        bass_idx = np.where(
            (self.freqs >= bass_min) &
            (self.freqs < bass_max)
        )[0]
        if len(bass_idx) > 0:
            self.band_bin_indices.append(bass_idx)
            self.band_labels.append(self._format_freq_label(bass_min, bass_max))

        # Remaining bands from 50 Hz to AUDIBLE_MAX
        remaining_bands_start_freq = 50
        num_remaining_bands = NUM_BANDS - len(self.band_bin_indices) # Adjust NUM_BANDS for the custom band
        
        if num_remaining_bands > 0:
            band_edges = np.geomspace(remaining_bands_start_freq, AUDIBLE_MAX, num_remaining_bands + 1)
            
            for i in range(num_remaining_bands):
                idx = np.where(
                    (self.freqs >= band_edges[i]) &
                    (self.freqs < band_edges[i+1])
                )[0]
                
                if i == num_remaining_bands - 1:
                    idx = np.where(
                        (self.freqs >= band_edges[i]) &
                        (self.freqs <= band_edges[i+1])
                    )[0]
                
                if len(idx) > 0:
                    self.band_bin_indices.append(idx)
                    low = int(self.freqs[idx[0]])
                    high = int(self.freqs[idx[-1]])
                    self.band_labels.append(self._format_freq_label(low, high))
        logger.debug(f"Configured {len(self.band_bin_indices)} frequency bands.")
    
    @staticmethod
    def _format_freq_label(low: int, high: int) -> str:
        """Format frequency range label, abbreviating and wrapping if necessary, with rounding to nearest 0 or 5."""
        def round_to_nearest_0_or_5(n):
            return int(5 * round(n / 5))

        low_rounded = round_to_nearest_0_or_5(low)
        high_rounded = round_to_nearest_0_or_5(high)

        def format_single_freq(f):
            if f >= 1000:
                return f"{f/1000:.1f}k"
            return f"{f:.0f}"
        
        low_str = format_single_freq(low_rounded)
        high_str = format_single_freq(high_rounded)
        
        label = f"{low_str}-{high_str}"
        if "k" in low_str or "k" in high_str or len(label) > 6: # Heuristic for wrapping
            return f"{low_str}\n{high_str} Hz"
        return f"{label} Hz"
    
    def start_capture(self) -> None:
        """Start audio capture."""
        if not self.capturing:
            os.makedirs(OUTPUT_DIR, exist_ok=True)
            now = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
            self.capture_filename = os.path.join(OUTPUT_DIR, f"audio_{now}.wav")
            self.audio_frames = []
            self.capturing = True
            logger.info(f"Starting audio capture to {os.path.abspath(self.capture_filename)}")
        else:
            logger.debug("Attempted to start capture, but already capturing.")
            
    def stop_capture(self) -> Optional[str]:
        """Stop audio capture and save the file."""
        if not self.capturing:
            logger.debug("Attempted to stop capture, but not currently capturing.")
            return None
            
        self.capturing = False
        if not self.audio_frames:
            logger.warning("Audio capture stopped, but no frames were recorded.")
            return None
            
        try:
            with wave.open(self.capture_filename, 'wb') as wf:
                wf.setnchannels(AUDIO_CHANNELS)
                wf.setsampwidth(2)
                wf.setframerate(AUDIO_SAMPLERATE)
                audio_np = np.concatenate(self.audio_frames)
                audio_int16 = np.clip(audio_np * 32767, -32768, 32767).astype(np.int16)
                wf.writeframes(audio_int16.tobytes())
            logger.info(f"Audio capture saved to: {os.path.abspath(self.capture_filename)}")
            return self.capture_filename
        except Exception as e:
            logger.error(f"Error saving audio file {self.capture_filename}: {e}", exc_info=True)
            return None
        finally:
            self.audio_frames = []
            
    def audio_callback(self, indata: np.ndarray, frames: int, time: any, status: any) -> None:
        """Process incoming audio data."""
        if status:
            logger.warning(f"Audio callback status: {status}")

        audio = indata[:, 0]
        
        if self.capturing:
            self.audio_frames.append(audio.copy())
            logger.debug(f"Captured {frames} frames of audio.")

        # Perform audio processing
        window = np.hanning(len(audio))
        fft = np.abs(np.fft.rfft(audio * window))
        scale_factor = len(audio) / 16.0
        power = (fft / scale_factor) ** 2
        
        band_values = np.zeros(self.NUM_ACTUAL_BANDS)
        
        for i, idx in enumerate(self.band_bin_indices):
            if len(idx) > 0:
                band_power = np.sum(power[idx])
                
                db_val = -100
                norm_val = 0
                
                if band_power > 1e-10:
                    db_val = 10 * np.log10(band_power)
                    # Map -60 dB to 0% and 0 dB to 100%
                    norm_val = (db_val + 60) / 60
                    norm_val = np.clip(norm_val, 0, 1)
                
                # Apply smoothing: fast decay, moderate attack
                if hasattr(self, 'prev_band_values'):
                    if norm_val > self.prev_band_values[i]:
                        # Attack (increase) is moderately smoothed
                        norm_val = 0.5 * self.prev_band_values[i] + 0.5 * norm_val
                    else:
                        # Decay (decrease) is much faster
                        norm_val = 0.1 * self.prev_band_values[i] + 0.9 * norm_val

                band_values[i] = np.clip(norm_val, 0, 1)
        
        # Overall smoothing (optional, can be removed if per-band smoothing is sufficient)
        if hasattr(self, 'prev_band_values'):
            smoothing = 0.7 # This smoothing is applied after per-band smoothing
            band_values = smoothing * self.prev_band_values + (1 - smoothing) * band_values
        
        self.prev_band_values = band_values.copy()

        if self.callback:
            self.callback(band_values)
            logger.debug(f"Processed audio block, calling callback with band values (first 5): {band_values[:5]}")
            
    def start_stream(self) -> None:
        """Start the audio input stream."""
        try:
            self.stream = sd.InputStream(
                channels=AUDIO_CHANNELS,
                samplerate=AUDIO_SAMPLERATE,
                blocksize=AUDIO_BLOCKSIZE,
                callback=self.audio_callback,
                dtype='float32',
                device=None
            )
            self.stream.start()
            logger.info("Audio stream started.")
        except sd.PortAudioError as e:
            logger.error(f"Error starting audio stream: {e}", exc_info=True)
            raise
            
    def stop_stream(self) -> None:
        """Stop the audio input stream."""
        if hasattr(self, 'stream') and self.stream.stopped == False:
            self.stream.stop()
            self.stream.close()
            logger.info("Audio stream stopped and closed.")
        else:
            logger.debug("Attempted to stop stream, but no active stream found.")
