import pytest
import tkinter as tk
from unittest.mock import MagicMock, patch
from audio_monitor.visualizer import Visualizer
from audio_monitor.constants import WINDOW_WIDTH, WINDOW_HEIGHT, PADDING, NUM_BANDS

@pytest.fixture
def mock_gui_elements():
    root = tk.Tk()
    root.withdraw() # Hide the main window
    colors = {
        'bg': '#1E1E1E',
        'text': '#FFFFFF',
        'grid': '#333333',
        'bar_colors': {'low': '#3C4FE0', 'mid': '#00C853', 'high': '#FFD600', 'peak': '#FF4444'}
    }
    fonts = {
        'small': ('Helvetica', 10)
    }
    band_labels = [f"{i*100}-{(i+1)*100} Hz" for i in range(NUM_BANDS)]
    yield root, colors, fonts, band_labels
    root.destroy()

@pytest.fixture
def visualizer(mock_gui_elements):
    root, colors, fonts, band_labels = mock_gui_elements
    viz = Visualizer(root, colors, fonts, NUM_BANDS, band_labels)
    viz.create_canvas(root, WINDOW_WIDTH, WINDOW_HEIGHT, 50) # 50 is a dummy button_height
    return viz

def test_visualizer_initialization(visualizer):
    assert visualizer.root is not None
    assert visualizer.canvas is not None
    assert visualizer.num_bands == NUM_BANDS
    assert len(visualizer.band_labels) == NUM_BANDS

def test_setup_frequency_bars(visualizer):
    visualizer.setup_frequency_bars()
    assert len(visualizer.bars) == NUM_BANDS
    assert len(visualizer.labels) == NUM_BANDS
    # Check if bars are created at the bottom of the canvas initially
    for bar in visualizer.bars:
        coords = visualizer.canvas.coords(bar)
        assert coords[1] == visualizer.bar_area_bottom # y0
        assert coords[3] == visualizer.bar_area_bottom # y1

def test_setup_grid(visualizer):
    visualizer.setup_grid()
    assert len(visualizer.grid_lines) > 0
    assert len(visualizer.grid_labels) > 0

def test_update_frequency_bars(visualizer):
    visualizer.setup_frequency_bars()
    band_values = [0.5] * NUM_BANDS # Simulate 50% fill for all bars
    visualizer.update_frequency_bars(band_values)

    for i, bar in enumerate(visualizer.bars):
        coords = visualizer.canvas.coords(bar)
        # Calculate expected height for 50% fill
        expected_height = int((0.5 * 100 / 100.0) * visualizer.viz_dimensions['height'])
        assert coords[3] == visualizer.viz_dimensions['bottom'] # y1 should be at the bottom
        assert coords[1] == visualizer.viz_dimensions['bottom'] - expected_height # y0 should be at bottom - height

def test_on_window_resize(visualizer, mock_gui_elements):
    root, _, _, _ = mock_gui_elements
    visualizer.setup_frequency_bars()
    visualizer.setup_grid()

    initial_width = visualizer.canvas_width
    initial_height = visualizer.canvas_height

    # Simulate a resize event
    new_width = initial_width + 100
    new_height = initial_height + 50
    event = MagicMock(width=new_width, height=new_height, widget=root)
    
    mock_button_frame = MagicMock()
    mock_button_frame.place = MagicMock()

    visualizer.on_window_resize(event, {'minimized': False, 'width': initial_width, 'height': initial_height}, mock_button_frame, [0.1]*NUM_BANDS)

    assert visualizer.canvas_width == new_width
    assert visualizer.canvas_height == new_height - visualizer.BUTTON_FRAME_HEIGHT # Canvas height is total - button height
    mock_button_frame.place.assert_called_once()

    # Check if grid lines and labels are recreated
    assert len(visualizer.grid_lines) > 0
    assert len(visualizer.grid_labels) > 0

    # Check if bar coordinates are updated (simple check for now)
    for bar in visualizer.bars:
        coords = visualizer.canvas.coords(bar)
        assert coords[0] >= PADDING # x0 should be within padding
        assert coords[2] <= new_width - PADDING # x1 should be within padding

@patch('audio_monitor.visualizer.logger')
def test_visualizer_logging(mock_logger, visualizer):
    visualizer.setup_frequency_bars()
    mock_logger.debug.assert_called() # Check if debug messages are called
    mock_logger.info.assert_not_called() # Should not call info for setup_frequency_bars
