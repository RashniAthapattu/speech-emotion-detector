# Speech Emotion Recognition for Alexithymia

A mobile app prototype that records a short voice clip and shows the emotion it detects. It started as my BSc final project at the University of Westminster (Informatics Institute of Technology), 2023, and I later rebuilt the model with a proper evaluation. The idea is to help people with the alexithymia personality trait, who find it hard to recognise the emotions of the people they talk to.

## Results

Test results on **speakers the model has never heard** (8 emotions: angry, calm, disgust, fear, happy, neutral, sad, surprise). Chance level is 12.5%.

| Model | Features | Accuracy | Weighted F1 |
|-------|----------|----------|-------------|
| Random Forest | hand-made audio features | 40.5% | 0.40 |
| CNN (as in the thesis) | hand-made audio features | 37.6% | 0.36 |
| **Logistic regression on WavLM (layer 6)** | pretrained speech model | **78.1%** | **0.79** |

- Four public datasets were combined: RAVDESS, CREMA-D, TESS and SAVEE.
- Speakers are split between training (85), validation (18) and test (19), so no voice in the test set is seen during training.
- The WavLM layer and the classifier settings were chosen on the validation speakers only. The test set was used once.
- Accuracy per dataset on the test speakers: CREMA-D 74%, RAVDESS 68%, TESS 84%.
- The thesis reported 68% for its CNN. That number came from a looser split, and the speaker-independent rerun above is the fair comparison.

Limits: this is a single split of 19 test speakers, so another split could move the result by a few points. Datasets also differ in recording conditions, and acted speech is easier than real conversations. Calm has only 48 test clips, so its score is the least reliable. Confusion matrices and the layer-by-layer chart are in `training/results/`.

## What is in this repository

- `training/`: the notebooks that produced the results, and their output.
  - `train_emotion_cnn.ipynb`: hand-made features (zero crossing rate, chroma, MFCC, RMS, mel spectrogram) with a CNN and a Random Forest.
  - `train_wavlm_probe.ipynb`: features from the pretrained WavLM model with a logistic regression.
  - Both run on Google Colab (T4 GPU) and download the datasets themselves.
- `model/`: the trained WavLM classifier as plain numbers (`probe.npz`, `labels.json`), no pickle file.
- `lib/`: the Flutter app. It records audio, sends it to the server and shows the emotion.
- `server/`: the Flask server. It receives a recording, runs WavLM and the classifier from `model/`, and returns the emotion with a confidence score. It has automated tests (`pytest`).

## Tech stack

| Area | Tools |
|------|-------|
| Model | WavLM (Hugging Face Transformers, PyTorch), scikit-learn, Keras, librosa |
| App | Flutter, Dart, `record`, `http` |
| Server | Python, Flask, pydub (ffmpeg), pytest |

## Run the server

You need Python 3.10 or newer and `ffmpeg` installed (for example `brew install ffmpeg` on a Mac).

```bash
cd server
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

The first start downloads the WavLM model (about 380 MB). The server listens on `http://127.0.0.1:5000`. Try it with a recording:

```bash
curl -F audio=@recording.m4a http://127.0.0.1:5000/detect_emotion
```

It answers with the emotion, a confidence value and a score for each emotion. To use it from a phone, start it with `HOST=0.0.0.0 python app.py`, and only on a network you trust. Run the tests with `pip install -r requirements-dev.txt` and then `pytest`.

## Run the app

Install Flutter, start the server, then run `flutter run --dart-define=API_URL=http://<address of your computer>:5000`. In the Android emulator the default address `http://10.0.2.2:5000` reaches the server on your computer. Android 9 and newer also blocks plain `http://` connections unless the app allows them (`android:usesCleartextTraffic="true"` in the debug manifest), which is not set up yet.

## Known limits

- The Flutter app has not been run since the changes made after the thesis, and it has no automated tests. Only the server is tested.
- The server has no login and uses Flask's built-in development server, so run it only on your own computer. It accepts only `.m4a` and `.wav` uploads, up to 5 MB.
- The server was tested with a mock model and with sample recordings. Running the full WavLM path locally is not yet covered by a test.
- Only Android has the microphone permission set up. iOS would need a microphone usage description added.
- The accuracy figures are for acted emotional speech from four datasets, and real conversations are harder.

## Run the training notebooks

1. Open Google Colab and choose *File > Upload notebook*.
2. Pick a notebook from `training/`, then *Runtime > Change runtime type > T4 GPU*.
3. *Runtime > Run all*. The WavLM notebook takes about 10 to 15 minutes, and the CNN notebook 30 to 60 minutes.
