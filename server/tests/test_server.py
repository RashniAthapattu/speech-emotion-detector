import io
import json
import os
import wave

import numpy as np
import pytest
from sklearn.linear_model import LogisticRegression

from app import create_app
from emotion_model import classify, to_result

LABELS = ["angry", "calm", "disgust", "fear", "happy", "neutral", "sad", "surprise"]
MODEL_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "model")


def wav_bytes(seconds, rate=16000):
    t = np.arange(int(seconds * rate)) / rate
    pcm = (0.3 * np.sin(2 * np.pi * 220 * t) * 32767).astype(np.int16)
    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(rate)
        w.writeframes(pcm.tobytes())
    return buf.getvalue()


class FakeModel:
    sample_rate = 16000
    max_seconds = 6
    heard = None

    def predict(self, audio):
        FakeModel.heard = audio
        return to_result(np.eye(8)[4] * 0.9 + 0.1 / 8, LABELS)


@pytest.fixture
def client():
    return create_app(model=FakeModel()).test_client()


def test_classify_matches_scikit_learn():
    rng = np.random.RandomState(0)
    X = rng.randn(400, 768).astype(np.float32) * 3 + 1
    y = rng.randint(0, 8, 400)
    mean, scale = X.mean(axis=0), X.std(axis=0) + 1e-8
    clf = LogisticRegression(C=0.01, max_iter=500).fit((X - mean) / scale, y)
    probe = {"coef": clf.coef_, "intercept": clf.intercept_, "mean": mean, "scale": scale}
    for row in X[:20]:
        expected = clf.predict_proba(((row - mean) / scale)[None])[0]
        np.testing.assert_allclose(classify(row, probe), expected, atol=1e-6)


def test_shipped_classifier_files_are_consistent():
    with open(os.path.join(MODEL_DIR, "config.json")) as f:
        config = json.load(f)
    with open(os.path.join(MODEL_DIR, "labels.json")) as f:
        labels = json.load(f)
    probe = dict(np.load(os.path.join(MODEL_DIR, "probe.npz"), allow_pickle=False))
    assert labels == LABELS
    assert probe["coef"].shape == (8, 768)
    assert probe["mean"].shape == probe["scale"].shape == (768,)
    probs = classify(np.zeros(768), probe)
    assert probs.shape == (8,) and abs(probs.sum() - 1) < 1e-9
    assert config["layer"] == 6 and config["sample_rate"] == 16000


def test_health(client):
    assert client.get("/health").get_json() == {"status": "ok"}


def test_returns_emotion_for_a_valid_recording(client):
    r = client.post("/detect_emotion", data={"audio": (io.BytesIO(wav_bytes(2)), "r.wav")})
    assert r.status_code == 200
    body = r.get_json()
    assert body["emotion"] == "happy"
    assert 0 < body["confidence"] <= 1
    assert set(body["scores"]) == set(LABELS)


def test_long_recordings_are_cut_to_six_seconds(client):
    client.post("/detect_emotion", data={"audio": (io.BytesIO(wav_bytes(9)), "r.wav")})
    assert len(FakeModel.heard) == 16000 * 6


def test_missing_audio_field_is_a_400(client):
    assert client.post("/detect_emotion", data={}).status_code == 400


def test_unreadable_audio_is_a_400(client):
    r = client.post("/detect_emotion", data={"audio": (io.BytesIO(b"not audio at all"), "r.m4a")})
    assert r.status_code == 400


def test_playlist_style_files_are_refused(client):
    playlist = b"#EXTM3U\n#EXT-X-VERSION:3\n#EXTINF:1,\nfile:///etc/passwd\n"
    r = client.post("/detect_emotion", data={"audio": (io.BytesIO(playlist), "r.m4a")})
    assert r.status_code == 400


def test_detect_format():
    from app import detect_format

    assert detect_format(wav_bytes(1)) == "wav"
    assert detect_format(b"\x00\x00\x00\x18ftypM4A \x00\x00") == "mp4"
    assert detect_format(b"#EXTM3U") is None
    assert detect_format(b"") is None


def test_too_short_recording_is_a_400(client):
    r = client.post("/detect_emotion", data={"audio": (io.BytesIO(wav_bytes(0.2)), "r.wav")})
    assert r.status_code == 400


def test_huge_upload_is_a_413(client):
    r = client.post("/detect_emotion", data={"audio": (io.BytesIO(b"0" * (6 * 1024 * 1024)), "r.wav")})
    assert r.status_code == 413
