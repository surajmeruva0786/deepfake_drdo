import os
import glob
import numpy as np
import torch
from torch.utils.data import Dataset
import librosa

class AGCFDataset(Dataset):
    def __init__(self, base_dir, split="train", max_real=500, max_fake=500, val_ratio=0.2, seed=42):
        """
        Args:
            base_dir: Path to FakeAVCeleb_v1.2
            split: 'train' or 'val'
        """
        self.split = split
        real_dir = os.path.join(base_dir, "RealVideo-RealAudio")
        fake_dir = os.path.join(base_dir, "FakeVideo-FakeAudio")
        
        real_vids = glob.glob(os.path.join(real_dir, "**", "*.mp4"), recursive=True)
        fake_vids = glob.glob(os.path.join(fake_dir, "**", "*.mp4"), recursive=True)
        
        # Consistent shuffling
        np.random.seed(seed)
        np.random.shuffle(real_vids)
        np.random.shuffle(fake_vids)
        
        real_vids = real_vids[:max_real]
        fake_vids = fake_vids[:max_fake]
        
        n_val_real = int(max_real * val_ratio)
        n_val_fake = int(max_fake * val_ratio)
        
        if split == "train":
            self.samples = [(v, 1) for v in real_vids[:-n_val_real]] + [(v, 0) for v in fake_vids[:-n_val_fake]]
        else:
            self.samples = [(v, 1) for v in real_vids[-n_val_real:]] + [(v, 0) for v in fake_vids[-n_val_fake:]]
            
        np.random.shuffle(self.samples)
        
    def __len__(self):
        return len(self.samples)
        
    def __getitem__(self, idx):
        vid_path, label = self.samples[idx]
        npy_path = vid_path.replace(".mp4", ".npy")
        
        # Default empty tensors in case of missing files
        num_chunks = 16
        if os.path.exists(npy_path):
            try:
                chunks = np.load(npy_path)
            except Exception as e:
                raise RuntimeError(f"Failed to load {npy_path}: {e}")
        else:
            raise RuntimeError(f"Audio chunk file not found: {npy_path}. Did you run extract_audio.py?")
            
        # Ensure correct shape
        if chunks.shape[0] != num_chunks:
            raise RuntimeError(f"Audio chunk file {npy_path} has incorrect shape: {chunks.shape[0]} instead of {num_chunks}")
            
        spectral_feats = []
        vocal_feats = []
        
        for i in range(num_chunks):
            chunk = chunks[i]
            
            # 1. Spectral Stream: Log-mel spectrogram (64 mel bins)
            # n_fft=512, hop_length=160
            mel = librosa.feature.melspectrogram(y=chunk, sr=16000, n_mels=64, n_fft=512, hop_length=160)
            log_mel = librosa.power_to_db(mel, ref=np.max)
            # Resize or pad if necessary to have consistent dimensions
            # For 1 sec at 16kHz, length=16000. hop=160 => ~101 frames
            # Let's ensure fixed size.
            target_length = 100
            if log_mel.shape[1] > target_length:
                log_mel = log_mel[:, :target_length]
            elif log_mel.shape[1] < target_length:
                pad = target_length - log_mel.shape[1]
                log_mel = np.pad(log_mel, ((0, 0), (0, pad)), mode='constant')
                
            spectral_feats.append(np.expand_dims(log_mel, axis=0)) # (1, 64, 100)
            
            # 2. Vocal Stream: raw waveform
            # Standardize length to e.g. 16000
            target_wave_len = 16000
            if len(chunk) > target_wave_len:
                chunk = chunk[:target_wave_len]
            elif len(chunk) < target_wave_len:
                pad = target_wave_len - len(chunk)
                chunk = np.pad(chunk, (0, pad), mode='constant')
                
            vocal_feats.append(np.expand_dims(chunk, axis=0)) # (1, 16000)
            
        spectral_tensor = torch.tensor(np.array(spectral_feats), dtype=torch.float32) # (16, 1, 64, 100)
        vocal_tensor = torch.tensor(np.array(vocal_feats), dtype=torch.float32)       # (16, 1, 16000)
        
        return spectral_tensor, vocal_tensor, label, vid_path
