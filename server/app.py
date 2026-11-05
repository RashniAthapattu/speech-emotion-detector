"""Small web server: receives a voice recording and returns the detected emotion.

Run it on your own computer:
    cd server
    pip install -r requirements.txt
    python app.py
"""
import os
import tempfile

import numpy as np
from flask import Flask, jsonify, request

MODEL_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "model")
MAX_UPLOAD_BYTES = 5 * 1024 * 1024  # 5 MB is plenty for a few seconds of speech
MIN_SECONDS = 0.5


def detect_format(data):
    """Return "wav" or "mp4" (which covers .m4a) from the first bytes of the upload, else None.

    Only these two formats are accepted. Letting ffmpeg guess the format would also let it
    open playlist-style files that point to other files or web addresses.
    """
    if data[:4] == b"RIFF" and data[8:12] == b"WAVE":
        return "wav"
    if data[4:8] == b"ftyp":
        return "mp4"
    return None


def load_audio_bytes(data, sample_rate, max_seconds):
    """Decode an uploaded recording (m4a or wav) into a mono float32 signal.

    Decoding m4a uses ffmpeg through pydub, so ffmpeg must be installed.
    """
    from pydub import AudioSegment

    audio_format = detect_format(data)
    if audio_format is None:
        raise ValueError("unsupported audio format")

    # a private temporary file per request, so two requests can never mix up
    with tempfile.NamedTemporaryFile(suffix="." + audio_format) as tmp:
        tmp.write(data)
        tmp.flush()
        segment = AudioSegment.from_file(tmp.name, format=audio_format)
    segment = segment.set_frame_rate(sample_rate).set_channels(1)
    samples = np.array(segment.get_array_of_samples(), dtype=np.float32)
    samples /= float(1 << (8 * segment.sample_width - 1))
    return samples[: int(sample_rate * max_seconds)]


def create_app(model=None):
    app = Flask(__name__)
    app.config["MAX_CONTENT_LENGTH"] = MAX_UPLOAD_BYTES

    if model is None:
        from emotion_model import EmotionModel

        model = EmotionModel.load(MODEL_DIR)

    @app.get("/health")
    def health():
        return jsonify(status="ok")

    @app.post("/detect_emotion")
    def detect_emotion():
        upload = request.files.get("audio")
        if upload is None:
            return jsonify(error="Send the recording in a form field called 'audio'."), 400
        try:
            audio = load_audio_bytes(upload.read(), model.sample_rate, model.max_seconds)
        except Exception:
            app.logger.exception("could not decode the uploaded audio")
            return jsonify(error="Could not read the audio file."), 400
        if len(audio) < model.sample_rate * MIN_SECONDS:
            return jsonify(error="The recording is too short."), 400
        return jsonify(model.predict(audio))

    @app.errorhandler(413)
    def too_large(_):
        return jsonify(error="The recording is too large."), 413

    return app


if __name__ == "__main__":
    # Debug mode is off: it would let anyone who can reach the server run code on it.
    # The default address only accepts connections from this computer. To use a phone,
    # set HOST=0.0.0.0 and only do it on a network you trust.
    create_app().run(host=os.environ.get("HOST", "127.0.0.1"),
                     port=int(os.environ.get("PORT", "5000")))
