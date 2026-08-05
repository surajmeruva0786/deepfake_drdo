# Physiology-Guided Consistency Framework (PGCF) Architecture

The Physiology-Guided Consistency Framework (PGCF) is the core video-based baseline model used in this pipeline. It is a highly sophisticated multi-stream neural network designed to detect visual deepfakes by examining three distinct visual representations of a video simultaneously: Spatial, Frequency, and Physiological (rPPG).

## High-Level Architecture Overview

The PGCF model takes a sequence of video frames and processes them through five distinct phases:

### 1. Spatial Stream (Visual Artifacts)
- **Input**: Raw RGB Video Frames `(B, T, 3, H, W)`.
- **Network**: Pre-trained ResNet-50 backbone.
- **Attention**: Convolutional Block Attention Module (CBAM) is applied after the ResNet to force the network to focus heavily on manipulated facial regions and ignore background noise.
- **Function**: Extracts high-level spatial features, catching visible blending boundaries, weird eye textures, and skin warping.
- **Output**: Projected to a 256-dimensional feature vector per frame.

### 2. Frequency Stream (Compression & Generative Artifacts)
- **Input**: 4-Channel Frequency Maps (RGB + DCT Energy Map).
- **Network**: A custom 3-layer 2D Convolutional Neural Network.
- **Function**: Deepfake generators (like GANs or Diffusion models) often leave invisible high-frequency "checkerboard" artifacts or frequency anomalies. This stream acts as a frequency-domain detector.
- **Output**: Projected to a 256-dimensional feature vector per frame.

### 3. rPPG Stream (Physiological Liveness)
- **Input**: 1D Remote Photoplethysmography (CHROM) signal. This is a measure of the micro-color changes in the skin caused by the human heartbeat (blood volume pulse).
- **Network**: A custom 1D-CNN.
- **Function**: Authentic videos contain a natural, rhythmic human heartbeat signature. Deepfakes (especially FaceSwaps) often destroy this biological signal, resulting in chaotic or synthetic heart rates.
- **Output**: Projected to a 128-dimensional feature vector representing the subject's physiology.
- *Note*: This stream also includes a reconstruction decoder to ensure the network actually learns the physiological signal properly.

### 4. PGCMC (Physiology-Guided Cross-Modal Consistency)
This is the "Brain" of the fusion process. It determines how much to trust the physiological signal:
- **rPPG Gating Confidence ($c$)**: Computes the Spectral Entropy of the heartbeat signal. If the entropy is high (chaotic), the network determines the heartbeat is synthetic or degraded.
- **Cross-Modal Consistency ($s$)**: Computes the pairwise Cosine Similarities between the Spatial, Frequency, and rPPG features. It checks if the visual features actually "align" with the physiological features.
- **Gated Fusion**: The Spatial and Frequency streams are concatenated together, and their final weighting is dynamically adjusted based on the physiological confidence scores ($c$ and $s$).

### 5. Temporal Modeling
Deepfakes often flicker or jitter from frame to frame. The fused features are passed through a massive temporal engine:
1. **Temporal Gradient Fusion (TGF)**: Calculates the exact mathematical difference between consecutive frames to track motion inconsistencies.
2. **Temporal Self-Attention (Transformer)**: A Transformer Encoder looks at the entire sequence of frames to find the most "fake-looking" moments.
3. **BiLSTM (Bidirectional LSTM)**: Processes the video forwards and backwards to model smooth temporal continuity.

### 6. Classification
- The temporal features are average-pooled across the entire video sequence into a single representation.
- A final Fully Connected classifier outputs the prediction logits (Real vs. Fake).

---

## Why this Architecture Works
Unlike standard CNNs that just look for blurry faces, the PGCF model verifies biological liveness. Even if a deepfake looks visually perfect (fooling the Spatial stream), it will likely fail to reproduce a consistent human heartbeat (failing the rPPG stream). Furthermore, if the visual face doesn't match the heartbeat biologically, the PGCMC Consistency check will flag the video as a forgery.
