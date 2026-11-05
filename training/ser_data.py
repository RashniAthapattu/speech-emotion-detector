"""Dataset helpers: read emotion and speaker from file names, and split by speaker."""
import os

import numpy as np
import pandas as pd

EMOTIONS = ["angry", "calm", "disgust", "fear", "happy", "neutral", "sad", "surprise"]
EMOTION_TO_ID = {e: i for i, e in enumerate(EMOTIONS)}

RAVDESS_CODES = {"01": "neutral", "02": "calm", "03": "happy", "04": "sad",
                 "05": "angry", "06": "fear", "07": "disgust", "08": "surprise"}
CREMA_CODES = {"ANG": "angry", "DIS": "disgust", "FEA": "fear",
               "HAP": "happy", "NEU": "neutral", "SAD": "sad"}
TESS_CODES = {"angry": "angry", "disgust": "disgust", "fear": "fear", "happy": "happy",
              "neutral": "neutral", "sad": "sad", "ps": "surprise"}
SAVEE_CODES = {"a": "angry", "d": "disgust", "f": "fear", "h": "happy",
               "n": "neutral", "sa": "sad", "su": "surprise"}


def parse_file(dataset, path):
    """Return (emotion, speaker) for one file, or None if the name is not recognised."""
    stem = os.path.splitext(os.path.basename(path))[0]
    if dataset == "ravdess":            # 03-01-05-01-02-01-12.wav (emotion = 3rd, actor = last)
        parts = stem.split("-")
        if len(parts) != 7 or parts[2] not in RAVDESS_CODES:
            return None
        return RAVDESS_CODES[parts[2]], "ravdess_" + parts[6]
    if dataset == "crema":              # 1001_DFA_ANG_XX.wav
        parts = stem.split("_")
        if len(parts) < 3 or parts[2] not in CREMA_CODES:
            return None
        return CREMA_CODES[parts[2]], "crema_" + parts[0]
    if dataset == "tess":               # OAF_back_angry.wav
        parts = stem.split("_")
        label = parts[-1].lower()
        if label not in TESS_CODES:
            return None
        return TESS_CODES[label], "tess_" + parts[0].upper()
    if dataset == "savee":              # DC_sa01.wav
        if "_" not in stem:
            return None
        speaker, rest = stem.split("_", 1)
        label = rest.rstrip("0123456789")
        if label not in SAVEE_CODES:
            return None
        return SAVEE_CODES[label], "savee_" + speaker.upper()
    return None


def build_dataframe(paths):
    """paths: {dataset name: folder}. Returns a table with path, dataset, emotion, speaker, label."""
    rows = []
    for dataset, root in paths.items():
        for folder, _, files in os.walk(root):
            for f in files:
                if f.lower().endswith(".wav"):
                    parsed = parse_file(dataset, f)
                    if parsed:
                        rows.append({"path": os.path.join(folder, f), "file": f, "dataset": dataset,
                                     "emotion": parsed[0], "speaker": parsed[1]})
    df = pd.DataFrame(rows)
    # some Kaggle downloads contain the same folder twice: keep one copy of each file name
    df = df.drop_duplicates(subset=["dataset", "file"])
    df = df.sort_values(["dataset", "file"]).reset_index(drop=True)
    df["label"] = df["emotion"].map(EMOTION_TO_ID)
    return df


def speaker_split(df, seed=42, fractions=(0.70, 0.15, 0.15), tries=500):
    """Split into train/val/test by speaker, so no speaker appears in two parts.

    Gives the same result every time for the same seed, whatever order the files were read in.
    Tries seeds until every emotion appears in all three parts.
    """
    speakers = sorted(df["speaker"].unique())
    for s in range(seed, seed + tries):
        order = np.random.RandomState(s).permutation(len(speakers))
        n_train = int(round(fractions[0] * len(speakers)))
        n_val = int(round(fractions[1] * len(speakers)))
        groups = [set(speakers[i] for i in order[:n_train]),
                  set(speakers[i] for i in order[n_train:n_train + n_val]),
                  set(speakers[i] for i in order[n_train + n_val:])]
        parts = [df[df["speaker"].isin(g)] for g in groups]
        if all(p["emotion"].nunique() == len(EMOTIONS) for p in parts):
            assert not (groups[0] & groups[1] or groups[0] & groups[2] or groups[1] & groups[2])
            return parts[0], parts[1], parts[2], s
    raise RuntimeError("no split found with every emotion in all three parts")
