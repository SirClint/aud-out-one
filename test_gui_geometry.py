import tkinter as tk
import os
import configparser
import pytest
from unittest.mock import MagicMock, patch
from audio_monitor.gui import EqualizerGUI
from audio_monitor.constants import CONFIG_FILE, WINDOW_WIDTH, WINDOW_HEIGHT

def parse_geometry(geometry_string):
    """Parses a Tkinter geometry string (WxH+X+Y) into a tuple (W, H, X, Y)."""
    parts = geometry_string.split('+')
    size = parts[0].split('x')
    width = int(size[0])
    height = int(size[1])
    x = int(parts[1])
    y = int(parts[2])
    return width, height, x, y

@pytest.fixture
def clean_config_file():
    """
    Ensures a clean config file before and after tests.
    """
    config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), CONFIG_FILE)
    if os.path.exists(config_path):
        os.remove(config_path)
    yield
    if os.path.exists(config_path):
        os.remove(config_path)

def test_window_geometry_save_load(clean_config_file):
    """
    Tests if the window geometry is correctly saved and loaded.
    """
    config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), CONFIG_FILE)

    # 1. Test saving geometry
    root1 = tk.Tk()
    root1.withdraw() # Hide the window
    gui1 = EqualizerGUI(root1)
    
    test_geometry = "800x600+100+50"
    
    # Mock winfo_geometry to return the test_geometry when _save_window_geometry is called
    with patch.object(root1, 'winfo_geometry', return_value=test_geometry):
        gui1._save_window_geometry() # Directly call save method
    root1.destroy()

    assert os.path.exists(config_path)
    
    config = configparser.ConfigParser()
    config.read(config_path)
    assert 'Window' in config
    assert 'geometry' in config['Window']
    assert config['Window']['geometry'] == test_geometry

    # 2. Test loading geometry
    root2 = tk.Tk()
    root2.withdraw() # Hide the window
    
    # Mock root2.geometry to check if it's called with the correct value
    root2.geometry = MagicMock()
    
    gui2 = EqualizerGUI(root2)
    
    # The geometry should be loaded from the config file by the GUI's init process
    # and root2.geometry should be called with the saved geometry
    root2.geometry.assert_called_once_with(test_geometry)
    
    root2.destroy()

def test_window_geometry_default_if_no_config(clean_config_file):
    """
    Tests if default geometry is used when no config file exists.
    """
    config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), CONFIG_FILE)
    assert not os.path.exists(config_path) # Ensure no config file exists

    root = tk.Tk()
    root.withdraw() # Hide the window
    
    # Mock root.geometry to check if it's called with the default value
    root.geometry = MagicMock()
    
    gui = EqualizerGUI(root)
    
    # The geometry should be set to the default one
    default_geometry_pattern = f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}"
    
    # Check if root.geometry was called with a string starting with the default pattern
    root.geometry.assert_called_once()
    called_geometry = root.geometry.call_args[0][0]
    assert called_geometry.startswith(default_geometry_pattern)
    
    root.destroy()
