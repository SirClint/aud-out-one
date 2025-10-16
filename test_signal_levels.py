"""Test signal levels and frequency response."""
import numpy as np
from audio_monitor.audio_processor import AudioProcessor
from audio_monitor.gui import EqualizerGUI
from audio_monitor.constants import AUDIO_BLOCKSIZE, AUDIO_SAMPLERATE
import tkinter as tk

def generate_test_signal(frequencies, amplitudes=None, duration_seconds=1.0):
    """Generate a test signal with specified frequencies and amplitudes.
    
    Args:
        frequencies: List of frequencies in Hz
        amplitudes: List of amplitudes (0-1), or None for all 1.0
        duration_seconds: Duration of the signal
        
    Returns:
        numpy array of audio samples
    """
    if amplitudes is None:
        amplitudes = [1.0] * len(frequencies)
    
    t = np.linspace(0, duration_seconds, int(AUDIO_SAMPLERATE * duration_seconds))
    signal = np.zeros_like(t)
    
    for freq, amp in zip(frequencies, amplitudes):
        signal += amp * np.sin(2 * np.pi * freq * t)
    
    # Normalize to prevent clipping
    signal /= max(1.0, np.max(np.abs(signal)))
    return signal

def test_signal_levels():
    """Test signal level processing with various amplitudes."""
    print("\nTesting signal levels...")
    print("-" * 60)
    
    # Create a dummy root window for the GUI
    root = tk.Tk()
    root.withdraw()
    gui = EqualizerGUI(root)
    
    test_cases = [
        {
            'name': "Silence",
            'signal': np.zeros(AUDIO_BLOCKSIZE),
            'expected_max': 0.0
        },
        {
            'name': "Very quiet sine (-60 dB)",
            'signal': generate_test_signal([1000], [0.001])[:AUDIO_BLOCKSIZE],
            'expected_max': 0.2
        },
        {
            'name': "Quiet sine (-40 dB)",
            'signal': generate_test_signal([1000], [0.01])[:AUDIO_BLOCKSIZE],
            'expected_max': 0.6
        },
        {
            'name': "Medium sine (-20 dB)",
            'signal': generate_test_signal([1000], [0.1])[:AUDIO_BLOCKSIZE],
            'expected_max': 0.8
        },
        {
            'name': "Full scale sine (0 dB)",
            'signal': generate_test_signal([1000], [1.0])[:AUDIO_BLOCKSIZE],
            'expected_max': 1.0
        }
    ]
    
    all_passed = True
    for test in test_cases:
        print(f"\nTest case: {test['name']}")
        gui.process_audio(test['signal'])
        
        # Get maximum band value
        max_level = max(gui.band_values)
        print(f"Maximum band value: {max_level:.3f}")
        print(f"Expected maximum: {test['expected_max']:.3f}")
        
        # Check if the level is within acceptable range
        tolerance = 0.1
        if abs(max_level - test['expected_max']) > tolerance:
            print(f"FAIL: Level {max_level:.3f} outside expected range "
                  f"[{test['expected_max']-tolerance:.3f}, "
                  f"{test['expected_max']+tolerance:.3f}]")
            all_passed = False
        else:
            print("PASS")
    
    return all_passed

def test_frequency_response():
    """Test frequency response across the spectrum."""
    print("\nTesting frequency response...")
    print("-" * 60)
    
    # Create a dummy root window for the GUI
    root = tk.Tk()
    root.withdraw()
    gui = EqualizerGUI(root)
    
    # Test frequencies across the spectrum
    test_frequencies = [
        50,     # Low bass
        100,    # Bass
        500,    # Low mids
        1000,   # Mids
        5000,   # High mids
        10000,  # Highs
        15000   # Very high
    ]
    
    all_passed = True
    for freq in test_frequencies:
        print(f"\nTesting {freq} Hz")
        # Generate a test tone at -20 dB
        signal = generate_test_signal([freq], [0.1])[:AUDIO_BLOCKSIZE]
        gui.process_audio(signal)
        
        # Find the band that should contain this frequency
        max_band = np.argmax(gui.band_values)
        max_level = gui.band_values[max_band]
        
        print(f"Peak band: {max_band}")
        print(f"Level: {max_level:.3f}")
        
        # Check if the level is reasonable
        if max_level < 0.1:
            print(f"FAIL: Level too low ({max_level:.3f})")
            all_passed = False
        elif max_level > 0.95:
            print(f"FAIL: Level too high ({max_level:.3f})")
            all_passed = False
        else:
            print("PASS")
            
        # Check adjacent bands
        adjacent_max = max(
            gui.band_values[max(0, max_band-1):min(len(gui.band_values), max_band+2)]
        )
        if adjacent_max > max_level * 1.5:
            print(f"FAIL: Adjacent band too high ({adjacent_max:.3f})")
            all_passed = False
    
    return all_passed

if __name__ == "__main__":
    print("Running signal processing tests...")
    levels_passed = test_signal_levels()
    freq_passed = test_frequency_response()
    
    print("\nTest Summary:")
    print("-" * 60)
    print(f"Signal Levels Test: {'PASS' if levels_passed else 'FAIL'}")
    print(f"Frequency Response Test: {'PASS' if freq_passed else 'FAIL'}")
    
    if not (levels_passed and freq_passed):
        exit(1)