# Audio Output Analyzer

This application, `aud-out-one`, is a Python-based audio output analyzer designed to monitor and visualize audio signals. It provides real-time insights into audio levels, frequencies, and other characteristics, making it a useful tool for audio engineers, developers, or anyone needing to analyze audio output.

## Features

*   **Real-time Audio Monitoring:** Continuously captures and processes audio output.
*   **Visualizations:** Displays audio data through various graphical representations (e.g., waveforms, spectrograms).
*   **Signal Level Analysis:** Provides metrics on audio signal strength and potential clipping.
*   **Configurable Settings:** Allows users to adjust parameters like input device, buffer size, and visualization options.
*   **Logging:** Records important events and data for debugging and post-analysis.

## How to Use

### Prerequisites

*   Python 3.x
*   Required Python libraries (install via `pip install -r requirements.txt` - *Note: `requirements.txt` needs to be created/updated*)

### Running the Application

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/clinterrific/aud-out-one.git
    cd aud-out-one
    ```
2.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
3.  **Run the main application:**
    ```bash
    python main.py
    ```

### Command-line Arguments

The application supports the following command-line arguments:

*   `--timeout <seconds>`: Sets a timeout for the application to run (useful for automated testing).
*   `--debug-level <level>`: Sets the debugging level for more verbose output (e.g., `DEBUG`, `INFO`, `WARNING`, `ERROR`).

## Code Structure

The project is organized into the following main directories and files:

*   `main.py`: The entry point of the application, responsible for initializing the audio monitor and GUI.
*   `audio_monitor/`: Contains the core logic for audio processing and analysis.
    *   `__init__.py`: Initializes the `audio_monitor` package.
    *   `analyzer.py`: Handles the analysis of audio data (e.g., frequency analysis, signal level calculations).
    *   `audio_processor.py`: Manages audio input, buffering, and basic processing.
    *   `constants.py`: Defines application-wide constants.
    *   `gui.py`: Implements the graphical user interface using Tkinter.
    *   `logger_config.py`: Configures the application's logging system.
    *   `visualizer.py`: Contains logic for rendering audio visualizations within the GUI.
*   `output/`: Directory where recorded audio files or analysis results might be stored.
*   `test_*.py`: Various test files for different modules of the application.
*   `window_config.ini`: Configuration file for GUI window settings.
*   `GEMINI.md`: Documentation related to Gemini CLI interactions and project context.

## Configuration

The `window_config.ini` file is used to store settings related to the application's GUI window, such as dimensions and initial position.

## Testing

Unit and integration tests are located in the `test_*.py` files in the root directory. To run tests, you would typically use a test runner like `pytest`:

```bash
pytest
```

## Troubleshooting

*   **No Audio Input:** Ensure your audio input device is correctly selected and configured in your operating system settings.
*   **Performance Issues:** Try reducing the buffer size or frame rate if the application is experiencing lag.
*   **Debugging:** Use the `--debug-level DEBUG` argument to get more detailed logs, which can help in identifying issues.
