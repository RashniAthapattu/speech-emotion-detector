"""The emotion classifier: WavLM embeddings plus a small logistic regression.

The classifier is stored as plain numbers (model/probe.npz), not as a pickle file,
so loading it cannot run any code.
"""
import json
import os

import numpy as np


def classify(embedding, probe):
    """Turn one WavLM embedding (768 numbers) into a probability for each emotion.

    Same maths as scikit-learn's LogisticRegression.predict_proba: scale the
    numbers, multiply by the learned weights, add the intercept, apply softmax.
    """
    x = (np.asarray(embedding, dtype=np.float64) - probe["mean"]) / probe["scale"]
    logits = probe["coef"].astype(np.float64) @ x + probe["intercept"]
    logits -= logits.max()
    exp = np.exp(logits)
    return exp / exp.sum()


def to_result(probs, labels):
    best = int(np.argmax(probs))
    return {
        "emotion": labels[best],
        "confidence": round(float(probs[best]), 4),
        "scores": {label: round(float(p), 4) for label, p in zip(labels, probs)},
    }


class EmotionModel:
    def __init__(self, backbone, extractor, probe, labels, config, device="cpu"):
        self.backbone = backbone
        self.extractor = extractor
        self.probe = probe
        self.labels = labels
        self.layer = config["layer"]
        self.sample_rate = config["sample_rate"]
        self.max_seconds = config["max_seconds"]
        self.device = device

    @classmethod
    def load(cls, model_dir):
        """Download WavLM (first run only) and read the classifier from model_dir."""
        import torch  # imported here so the rest of the server can be tested without it
        from transformers import AutoFeatureExtractor, AutoModel

        with open(os.path.join(model_dir, "config.json")) as f:
            config = json.load(f)
        with open(os.path.join(model_dir, "labels.json")) as f:
            labels = json.load(f)
        probe = dict(np.load(os.path.join(model_dir, "probe.npz"), allow_pickle=False))

        device = "cuda" if torch.cuda.is_available() else "cpu"
        extractor = AutoFeatureExtractor.from_pretrained(config["model"])
        backbone = AutoModel.from_pretrained(config["model"]).to(device).eval()
        return cls(backbone, extractor, probe, labels, config, device)

    def predict(self, audio):
        """audio: mono float32 signal at self.sample_rate."""
        import torch

        inputs = self.extractor(audio, sampling_rate=self.sample_rate, return_tensors="pt")
        with torch.no_grad():
            out = self.backbone(inputs["input_values"].to(self.device), output_hidden_states=True)
        embedding = out.hidden_states[self.layer].mean(dim=1).squeeze(0).cpu().numpy()
        return to_result(classify(embedding, self.probe), self.labels)
