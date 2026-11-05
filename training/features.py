"""Audio features shared by the training notebook and the server.

Both must use exactly this code, otherwise the model sees different
numbers at prediction time than it saw during training.
"""
import librosa
import numpy as np

SAMPLE_RATE = 22050
DURATION = 2.5   # seconds of audio used per clip
OFFSET = 0.6     # skip the first 0.6 s (often silence)
N_FEATURES = 162  # 1 zero crossing + 12 chroma + 20 MFCC + 1 RMS + 128 mel


def load_audio(path):
    """Read an audio file as a mono signal at the common sample rate."""
    audio, _ = librosa.load(path, sr=SAMPLE_RATE, duration=DURATION, offset=OFFSET)
    return audio


def extract_features(audio, sr=SAMPLE_RATE):
    """Turn an audio signal into one vector of 162 numbers."""
    zcr = np.mean(librosa.feature.zero_crossing_rate(y=audio).T, axis=0)
    chroma = np.mean(librosa.feature.chroma_stft(y=audio, sr=sr).T, axis=0)
    mfcc = np.mean(librosa.feature.mfcc(y=audio, sr=sr).T, axis=0)
    rms = np.mean(librosa.feature.rms(y=audio).T, axis=0)
    mel = np.mean(librosa.feature.melspectrogram(y=audio, sr=sr).T, axis=0)
    return np.hstack([zcr, chroma, mfcc, rms, mel]).astype(np.float32)
