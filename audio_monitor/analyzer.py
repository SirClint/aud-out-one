"""Audio analysis functionality using YAMNet."""
from typing import Dict, Tuple, List
import os
import urllib.request
import csv
import numpy as np
import soundfile as sf
import tensorflow as tf
import tensorflow_hub as hub
import librosa
from .constants import YAMNET_MODEL_URL, YAMNET_CLASS_MAP_URL, YAMNET_DETECTION_THRESHOLD
from .logger_config import logger

class AudioAnalyzer:
    """Handles audio analysis using YAMNet model."""
    
    def __init__(self):
        """Initialize the audio analyzer."""
        self.class_map_path = os.path.join(os.path.expanduser('~'), '.yamnet_class_map.csv')
        logger.debug(f"AudioAnalyzer initialized. Class map path: {self.class_map_path}")
        self._ensure_resources()
        self.class_names = self._load_class_names()
        self.model = hub.load(YAMNET_MODEL_URL)
        logger.info("YAMNet model loaded successfully.")
        
    def _ensure_resources(self) -> None:
        """Ensure required resources are available."""
        if not os.path.exists(self.class_map_path):
            logger.info("Downloading YAMNet class map...")
            urllib.request.urlretrieve(YAMNET_CLASS_MAP_URL, self.class_map_path)
            logger.info("YAMNet class map downloaded.")
            
    def _load_class_names(self) -> List[str]:
        """Load class names from the class map file.
        
        Returns:
            List of class names
        """
        class_names = []
        try:
            with open(self.class_map_path, 'r') as f:
                reader = csv.reader(f)
                next(reader)  # Skip header
                for row in reader:
                    class_names.append(row[2])
            logger.debug(f"Loaded {len(class_names)} class names.")
        except Exception as e:
            logger.error(f"Error loading class names from {self.class_map_path}: {e}", exc_info=True)
        return class_names
        
    def _load_and_process_audio(self, file_path: str) -> Tuple[np.ndarray, int]:
        """Load and process audio file for analysis.
        
        Args:
            file_path: Path to the audio file
            
        Returns:
            Tuple of processed audio data and sample rate
        """
        logger.debug(f"Loading and processing audio file: {file_path}")
        wav, sr = sf.read(file_path)
        if len(wav.shape) > 1:
            wav = np.mean(wav, axis=1)
            logger.debug("Converted stereo audio to mono.")
        if sr != 16000:
            original_sr = sr
            wav = librosa.resample(wav, orig_sr=sr, target_sr=16000)
            sr = 16000
            logger.debug(f"Resampled audio from {original_sr} Hz to {sr} Hz.")
        return wav, sr
        
    def _calculate_class_score(self, mean_scores: np.ndarray, keywords: List[str]) -> float:
        """Calculate score for a class based on keywords.
        
        Args:
            mean_scores: Mean scores from YAMNet
            keywords: Keywords to match against class names
            
        Returns:
            Maximum score for matching classes
        """
        idxs = [i for i, name in enumerate(self.class_names)
                if any(kw in name.lower() for kw in keywords)]
        score = float(np.max(mean_scores[idxs])) if idxs else 0.0
        logger.debug(f"Calculated score for keywords {keywords}: {score:.2f}")
        return score
        
    def analyze_file(self, file_path: str) -> Dict[str, Dict[str, float]]:
        """Analyze audio file for instrument detection.
        
        Args:
            file_path: Path to the audio file
            
        Returns:
            Dictionary containing analysis results
        """
        logger.info(f"Starting analysis for file: {file_path}")
        if not os.path.exists(file_path):
            logger.error(f"Audio file not found: {file_path}")
            raise FileNotFoundError(f"Audio file not found: {file_path}")
            
        wav, _ = self._load_and_process_audio(file_path)
        scores, _, _ = self.model(wav)
        scores_np = scores.numpy()
        mean_scores = np.mean(scores_np, axis=0)
        
        instruments = {
            'piano': ['piano'],
            'vocals': ['singing', 'vocal', 'choir', 'voice'],
            'guitar': ['guitar'],
            'bass': ['bass guitar', 'electric bass', 'acoustic bass'],
            'drums': ['drum', 'snare', 'kick drum', 'cymbal', 'percussion']
        }
        
        results = {}
        for instrument, keywords in instruments.items():
            score = self._calculate_class_score(mean_scores, keywords)
            results[instrument] = {
                'score': score,
                'detected': score > YAMNET_DETECTION_THRESHOLD
            }
            logger.debug(f"Instrument '{instrument}' detected: {results[instrument]['detected']} (score: {score:.2f})")
            
        logger.info(f"Analysis complete for file: {file_path}")
        return results