# Audio-Guided Consistency Framework (AGCF) Architecture

The Audio-Guided Consistency Framework (AGCF) is a specialized deep neural network designed to detect synthetic speech and audio manipulations in deepfake videos. Rather than relying on a single representation of audio, it leverages a **Dual-Stream** approach to capture both frequency-domain anomalies and raw acoustic inconsistencies.

## High-Level Architecture Overview

The model takes a sequence of audio chunks (e.g., 16 chunks per video clip) and processes them through five distinct phases:

### 1. Spectral Stream (Frequency Domain)
- **Input**: Log-Mel Spectrograms (2D arrays representing frequency content over time).
- **Network**: A 3-layer 2D Convolutional Neural Network (CNN).
- **Function**: Extracts high-level spectral features. Deepfake generators often leave unnatural artifact patterns in the high-frequency bands (spectral gaps or blurring) which this stream is designed to catch.
- **Output**: The features are pooled and projected into a **256-dimensional** vector per chunk.

### 2. Vocal Stream (Time Domain)
- **Input**: Raw 1D Audio Waveforms (e.g., 16,000 samples per chunk).
- **Network**: A 1D Convolutional Neural Network (Conv1D).
- **Function**: Extracts fine-grained, frame-level vocal tract features and micro-acoustic details that are lost during spectrogram conversion.
- **Output**: The features are projected into a **256-dimensional** vector per chunk.

### 3. Feature Fusion
- The 256-d Spectral features and 256-d Vocal features are concatenated together.
- This creates a rich, **512-dimensional multi-domain feature representation** for each audio chunk.

### 4. Temporal Modeling
Deepfakes often struggle with temporal consistency (e.g., voice jitter, robotic pacing, or unnatural transitions between phonemes). The AGCF uses three powerful mechanisms to analyze the sequence of chunks over time:

1. **Temporal Gradient Fusion (TGF)**: 
   - Calculates the exact difference between the current chunk and the previous chunk ($Feature_t - Feature_{t-1}$).
   - This explicitly forces the model to look at *how the audio changes over time*, highlighting unnatural jarring transitions.
2. **Temporal Self-Attention (Transformer)**:
   - Uses a Transformer Encoder layer to look at the entire sequence at once. It learns which parts of the audio clip are the most important for making a decision (e.g., focusing heavily on a weirdly pronounced word).
3. **BiLSTM (Bidirectional Long Short-Term Memory)**:
   - Processes the sequence both forwards and backwards to understand the sequential context and pacing of the speech.

### 5. Classification Head
- The temporal features are average-pooled across the entire sequence to create one single **512-dimensional clip-level representation**.
- A final Fully Connected (Linear) classifier evaluates this representation and outputs the final prediction logits (Real vs. Fake).

---

## Why this Architecture Works for Deepfakes
Most traditional audio classifiers only look at spectrograms (like an image classification problem). However, modern AI voice generators (like ElevenLabs or VITS) generate highly realistic spectrograms. By forcing the model to also analyze the raw 1D waveform (Vocal Stream) and tracking how the features shift frame-by-frame (Temporal Gradient Fusion), the AGCF becomes highly sensitive to the microscopic synthetic jitters that modern deepfakes leave behind.
