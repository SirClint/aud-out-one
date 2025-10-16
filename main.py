"""Main entry point for the audio monitor application."""
import tkinter as tk
import argparse
from audio_monitor import EqualizerGUI
from audio_monitor.logger_config import setup_logging, DEFAULT_LOG_LEVEL, LOG_LEVEL_MAP

def main():
    """Initialize and run the application."""
    parser = argparse.ArgumentParser(description="Audio Output Monitor Application")
    parser.add_argument(
        "--test-timeout", 
        type=int, 
        help="Automatically exit the application after N seconds for testing purposes."
    )
    parser.add_argument(
        "--log-level",
        type=str,
        default=DEFAULT_LOG_LEVEL,
        choices=list(LOG_LEVEL_MAP.keys()),
        help=f"Set the logging level (e.g., DEBUG, WARNING). Default: {DEFAULT_LOG_LEVEL}"
    )
    args = parser.parse_args()

    logger = setup_logging(args.log_level)
    logger.info(f"Application starting with log level: {args.log_level}")

    root = tk.Tk()
    monitor = EqualizerGUI(root, test_timeout=args.test_timeout)
    
    def on_close():
        """Handle window closing."""
        logger.info("Application closing.")
        monitor.stop()
        root.destroy()
        
    root.protocol('WM_DELETE_WINDOW', on_close)
    root.mainloop()

if __name__ == '__main__':
    main()