import numpy as np
import matplotlib.pyplot as plt
from audio_monitor.audio_processor import AudioProcessor
from audio_monitor.constants import AUDIO_BLOCKSIZE, AUDIO_SAMPLERATE

def generate_test_signal(frequencies, duration_seconds=1):
    """Generate a test signal with specified frequencies."""
    t = np.linspace(0, duration_seconds, int(AUDIO_SAMPLERATE * duration_seconds))
    signal = np.zeros_like(t)
    for freq in frequencies:
        signal += np.sin(2 * np.pi * freq * t)
    return signal

def test_frequency_response():
    """Test the frequency response of the audio processor."""
    processor = AudioProcessor()
    
    # Test frequencies (Hz)
    test_freqs = [
        100,    # Low frequency
        1000,   # Mid frequency
        5000,   # Upper mid frequency
        10000,  # High frequency
        15000   # Very high frequency
    ]
    
    print("\nTesting frequency response...")
    print("-" * 50)
    
    # Generate and process test signals for each frequency
    results = []
    for freq in test_freqs:
        # Generate single-frequency test signal
        test_signal = generate_test_signal([freq])
        
        # Process a block of the signal
        signal_block = test_signal[:AUDIO_BLOCKSIZE]
        
        # Apply Hanning window
        signal_block = signal_block * np.hanning(len(signal_block))
        
        # Calculate FFT
        fft = np.abs(np.fft.rfft(signal_block)) / len(signal_block)
        freqs = np.fft.rfftfreq(len(signal_block), 1.0 / AUDIO_SAMPLERATE)
        
        # Find the band containing our test frequency
        target_band = None
        for i, indices in enumerate(processor.band_bin_indices):
            if len(indices) > 0:
                band_freqs = freqs[indices]
                if band_freqs[0] <= freq <= band_freqs[-1]:
                    target_band = i
                    break
        
        if target_band is not None:
            print(f"\nTest frequency: {freq} Hz")
            print(f"Found in band: {processor.band_labels[target_band]}")
            
            # Calculate power in the target band
            band_indices = processor.band_bin_indices[target_band]
            band_power = np.mean(fft[band_indices] ** 2)
            
            if band_power > 0:
                db_val = 10 * np.log10(band_power)
                print(f"Power: {db_val:.1f} dB")
                results.append({
                    'frequency': freq,
                    'band': target_band,
                    'power_db': db_val
                })
            else:
                print("No power detected in band!")
        else:
            print(f"\nWarning: Could not find band for frequency {freq} Hz")
    
    # Plot the results
    if results:
        plt.figure(figsize=(10, 6))
        freqs = [r['frequency'] for r in results]
        powers = [r['power_db'] for r in results]
        plt.semilogx(freqs, powers, 'bo-')
        plt.grid(True)
        plt.xlabel('Frequency (Hz)')
        plt.ylabel('Power (dB)')
        plt.title('Frequency Response Test Results')
        plt.savefig('frequency_response_test.png')
        plt.close()
        
        print("\nFrequency response plot saved as 'frequency_response_test.png'")
    
    return results

def verify_band_distribution():
    """Verify the distribution of frequency bands."""
    processor = AudioProcessor()
    
    print("\nVerifying frequency band distribution...")
    print("-" * 50)
    
    # Print band information
    for i, indices in enumerate(processor.band_bin_indices):
        if len(indices) > 0:
            freqs = processor.freqs[indices]
            print(f"Band {i}: {processor.band_labels[i]}")
            print(f"  Frequency range: {freqs[0]:.1f} Hz - {freqs[-1]:.1f} Hz")
            print(f"  Number of FFT bins: {len(indices)}")
            print()

if __name__ == "__main__":
    print("Running audio processor tests...")
    verify_band_distribution()
    test_frequency_response()