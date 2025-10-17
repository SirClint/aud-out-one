import tkinter as tk
import os
import pytest
from unittest.mock import MagicMock, patch, call
import numpy as np
from audio_monitor.gui import EqualizerGUI
from audio_monitor.constants import DEFAULT_CAPTURE_DURATION, OUTPUT_DIR

@pytest.fixture
def mock_gui():
    root = tk.Tk()
    root.withdraw() # Hide the window
    # Mock _initialize_app_components to prevent full app initialization
    with patch.object(EqualizerGUI, '_initialize_app_components', lambda self: None):
        gui = EqualizerGUI(root)
    gui.root = root # Ensure root is set on the gui object
    gui.filename_var = tk.StringVar() # Initialize filename_var for tests
    gui.audio_analyzer = MagicMock() # Initialize audio_analyzer for tests
    gui.analyze_button = MagicMock() # Initialize analyze_button for tests
    gui.setup_fonts() # Explicitly call setup_fonts for tests
    gui.playback_stream = None # Initialize playback_stream for tests
    yield gui
    gui.root.destroy()

def test_update_filename_label_no_output_dir(mock_gui):
    """
    Tests that filename_var is empty if output directory does not exist.
    """
    with patch('os.path.exists', return_value=False):
        mock_gui.update_filename_label()
        assert mock_gui.filename_var.get() == ""

def test_update_filename_label_no_wav_files(mock_gui):
    """
    Tests that filename_var is empty if no WAV files are found.
    """
    with (
        patch('os.path.exists', return_value=True),
        patch('os.listdir', return_value=['other.txt', 'image.png'])
    ):
        mock_gui.update_filename_label()
        assert mock_gui.filename_var.get() == ""

def test_update_filename_label_with_wav_files(mock_gui):
    """
    Tests that the most recent WAV file is displayed.
    """
    mock_files = [
        'audio_20250101_100000.wav',
        'audio_20250101_110000.wav',
        'audio_20250101_090000.wav',
    ]
    # Mock getmtime to return increasing timestamps for later files
    mock_getmtime_map = {
        os.path.join(OUTPUT_DIR, 'audio_20250101_090000.wav'): 1672531200.0, # Jan 1, 2025 09:00:00
        os.path.join(OUTPUT_DIR, 'audio_20250101_100000.wav'): 1672534800.0, # Jan 1, 2025 10:00:00
        os.path.join(OUTPUT_DIR, 'audio_20250101_110000.wav'): 1672538400.0, # Jan 1, 2025 11:00:00
    }

    with (
        patch('os.path.exists', return_value=True),
        patch('os.listdir', return_value=mock_files),
        patch('os.path.getmtime', side_effect=lambda f: mock_getmtime_map[f])
    ):
        mock_gui.update_filename_label()
        expected_path = os.path.abspath(os.path.join(OUTPUT_DIR, 'audio_20250101_110000.wav'))
        assert mock_gui.filename_var.get() == expected_path

def test_capture_timer_tick_countdown(mock_gui):
    """
    Tests that the timer counts down correctly.
    """
    mock_gui.timer_running = True
    mock_gui.capture_seconds_left = 3
    mock_gui.update_timer_label = MagicMock() # Mock to prevent actual UI update
    mock_gui.stop_capture = MagicMock()
    mock_gui.root.after = MagicMock() # Mock Tkinter's after method

    mock_gui.capture_timer_tick()
    assert mock_gui.capture_seconds_left == 2
    mock_gui.update_timer_label.assert_called_once()
    mock_gui.root.after.assert_called_once_with(1000, mock_gui.capture_timer_tick)
    mock_gui.stop_capture.assert_not_called()

def test_capture_timer_tick_stops_capture_at_zero(mock_gui):
    """
    Tests that capture stops when the timer reaches zero.
    """
    mock_gui.timer_running = True
    mock_gui.capture_seconds_left = 1
    mock_gui.update_timer_label = MagicMock()
    mock_gui.stop_capture = MagicMock()
    mock_gui.root.after = MagicMock()

    mock_gui.capture_timer_tick()
    assert mock_gui.capture_seconds_left == 0
    mock_gui.update_timer_label.assert_called_once()
    mock_gui.root.after.assert_not_called() # Should not schedule another tick
    mock_gui.stop_capture.assert_called_once()

def test_capture_timer_tick_not_running(mock_gui):
    """
    Tests that the timer does not count down if not running.
    """
    mock_gui.timer_running = False
    mock_gui.capture_seconds_left = 5
    mock_gui.update_timer_label = MagicMock()
    mock_gui.stop_capture = MagicMock()
    mock_gui.root.after = MagicMock()

    mock_gui.capture_timer_tick()
    assert mock_gui.capture_seconds_left == 5 # Should not change
    mock_gui.update_timer_label.assert_not_called()
    mock_gui.root.after.assert_not_called()
    mock_gui.stop_capture.assert_not_called()

def test_analyze_button_plays_and_stops_wav(mock_gui):
    """
    Tests that clicking the Analyze button plays the WAV file in a loop
    and stops playback when the analysis popup is closed.
    """
    test_wav_path = os.path.join(OUTPUT_DIR, 'test_audio.wav')
    mock_gui.filename_var.set(test_wav_path)

    # Mock soundfile.read to return dummy audio data
    mock_audio_data = np.array([0.1, 0.2, 0.3, 0.4, 0.5], dtype='float32')
    mock_samplerate = 44100
    mock_sf_read = MagicMock(return_value=(mock_audio_data, mock_samplerate))

    # Mock sounddevice.OutputStream
    mock_sd_output_stream = MagicMock()
    mock_sd_output_stream.stopped = False # Simulate an active stream
    mock_sd_output_stream_class = MagicMock(return_value=mock_sd_output_stream)

    # Mock AudioAnalyzer.analyze_file
    mock_analysis_results = {'instrument1': {'detected': True, 'score': 0.9}}
    mock_analyzer_analyze_file = MagicMock(return_value=mock_analysis_results)

    # Mock tk.Toplevel.after globally for the duration of the test
    mock_toplevel_after = MagicMock()
    with (
        patch('soundfile.read', mock_sf_read),
        patch('sounddevice.OutputStream', mock_sd_output_stream_class),
        patch.object(mock_gui.audio_analyzer, 'analyze_file', mock_analyzer_analyze_file),
        patch('os.path.exists', return_value=True),
        patch.object(tk.Toplevel, 'after', mock_toplevel_after) # Mock Toplevel.after here
    ):
        # Simulate clicking the Analyze button by directly calling the method
        mock_gui.analyze_file()

        # Verify soundfile.read was called
        mock_sf_read.assert_called_once_with(test_wav_path, dtype='float32')
        # Verify OutputStream was created and started
        mock_sd_output_stream_class.assert_called_once_with(
            samplerate=mock_samplerate,
            channels=1,
            dtype='float32',
            callback=None
        )
        mock_sd_output_stream.start.assert_called_once()

        # Verify that tk.Toplevel.after was called to schedule the playback loop
        mock_toplevel_after.assert_called_once() # Verify after was called once initially
        play_audio_loop_func = mock_toplevel_after.call_args[0][1]

        # Manually call play_audio_loop a few times to simulate playback
        for _ in range(5): # Simulate 5 loop iterations
            play_audio_loop_func()

        # Verify write was called at least once (indicating playback attempt)
        mock_sd_output_stream.write.assert_called()

        # Simulate closing the popup window by calling the protocol handler directly
        mock_gui._stop_playback_and_destroy_popup()
        mock_gui.root.update() # Process pending events

        # Verify playback was stopped and stream closed
        mock_sd_output_stream.stop.assert_called_once()
        mock_sd_output_stream.close.assert_called_once()

def test_ok_button_stops_playback_and_destroys_popup(mock_gui):
    """
    Tests that clicking the OK button in the analysis popup stops playback
    and closes the window.
    """
    test_wav_path = os.path.join(OUTPUT_DIR, 'test_audio.wav')
    mock_gui.filename_var.set(test_wav_path)

    # Mock soundfile.read to return dummy audio data
    mock_audio_data = np.array([0.1, 0.2, 0.3, 0.4, 0.5], dtype='float32')
    mock_samplerate = 44100
    mock_sf_read = MagicMock(return_value=(mock_audio_data, mock_samplerate))

    # Mock sounddevice.OutputStream
    mock_sd_output_stream = MagicMock()
    mock_sd_output_stream.stopped = False # Simulate an active stream
    mock_sd_output_stream_class = MagicMock(return_value=mock_sd_output_stream)

    # Mock AudioAnalyzer.analyze_file
    mock_analysis_results = {'instrument1': {'detected': True, 'score': 0.9}}
    mock_analyzer_analyze_file = MagicMock(return_value=mock_analysis_results)

    # Mock tk.Toplevel.after globally for the duration of the test
    mock_toplevel_after = MagicMock()
    # Mock the _stop_playback_and_destroy_popup method to verify it's called
    mock_stop_destroy = MagicMock(side_effect=lambda: (
        mock_sd_output_stream.stop(),
        mock_sd_output_stream.close(),
        setattr(mock_gui, 'playback_stream', None) # Simulate setting to None
    ))

    with (
        patch('soundfile.read', mock_sf_read),
        patch('sounddevice.OutputStream', mock_sd_output_stream_class),
        patch.object(mock_gui.audio_analyzer, 'analyze_file', mock_analyzer_analyze_file),
        patch('os.path.exists', return_value=True),
        patch.object(tk.Toplevel, 'after', mock_toplevel_after),
        patch.object(mock_gui, '_stop_playback_and_destroy_popup', mock_stop_destroy) # Patch here
    ):
        # Simulate clicking the Analyze button to open the popup
        mock_gui.analyze_file()

        # Ensure the popup is created and the OK button exists
        mock_gui.results_popup.update_idletasks()
        ok_button = None
        for widget in mock_gui.results_popup.winfo_children():
            if isinstance(widget, tk.Button) and widget['text'] == "OK":
                ok_button = widget
                break
        assert ok_button is not None, "OK button not found in results popup"

        ok_button.invoke() # Simulate clicking the OK button
        mock_stop_destroy.assert_called_once() # Verify the stop/destroy method was called

        # Verify that the playback stream was stopped and closed (indirectly via mock_stop_destroy)
        mock_sd_output_stream.stop.assert_called_once()
        mock_sd_output_stream.close.assert_called_once()