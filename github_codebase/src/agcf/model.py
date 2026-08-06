import torch
import torch.nn as nn
import torch.nn.functional as F

class AGCF(nn.Module):
    def __init__(self, num_frames=16):
        super().__init__()
        self.num_frames = num_frames
        
        # A. Spectral Stream: 3-Layer 2D CNN -> 256 projection
        # Log-mel spectrogram has 1 channel
        self.spectral_cnn = nn.Sequential(
            nn.Conv2d(1, 32, kernel_size=3, padding=1),
            nn.BatchNorm2d(32),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(2),
            
            nn.Conv2d(32, 64, kernel_size=3, padding=1),
            nn.BatchNorm2d(64),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(2),
            
            nn.Conv2d(64, 64, kernel_size=3, padding=1),
            nn.BatchNorm2d(64),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(2)
        )
        self.spectral_pool = nn.AdaptiveAvgPool2d((1, 1))
        self.spectral_proj = nn.Linear(64, 256)
        
        # B. Vocal Stream: 1D-CNN -> 128 projection -> 256 projection
        self.vocal_cnn = nn.Sequential(
            nn.Conv1d(1, 32, kernel_size=3, padding=1),
            nn.BatchNorm1d(32),
            nn.ReLU(inplace=True),
            
            nn.Conv1d(32, 64, kernel_size=3, padding=1),
            nn.BatchNorm1d(64),
            nn.ReLU(inplace=True),
            nn.MaxPool1d(2),
            
            nn.Conv1d(64, 128, kernel_size=3, padding=1),
            nn.BatchNorm1d(128),
            nn.ReLU(inplace=True),
            nn.MaxPool1d(2)
        )
        self.vocal_pool = nn.AdaptiveAvgPool1d(1)
        self.vocal_proj_1 = nn.Linear(128, 128)
        self.vocal_proj_2 = nn.Linear(128, 256)
        
        # C. Temporal Modeling (Matching PGCF)
        # TGF (Temporal Gradient Fusion): linear difference projection
        self.tgf_proj = nn.Sequential(
            nn.Linear(1024, 512),
            nn.LayerNorm(512),
            nn.ReLU(inplace=True)
        )
        
        # Temporal Self-Attention
        self.transformer = nn.TransformerEncoderLayer(
            d_model=512,
            nhead=4,
            dim_feedforward=2048,
            activation='gelu',
            batch_first=True
        )
        
        # BiLSTM Sequence Encoding
        self.bilstm = nn.LSTM(
            input_size=512,
            hidden_size=256,
            num_layers=1,
            batch_first=True,
            bidirectional=True
        )
        
        # Classifier
        self.classifier = nn.Linear(512, 2)
        
    def forward(self, spectral_inputs, vocal_inputs):
        """
        Args:
            spectral_inputs: (B, T, 1, H, W) (Log-Mel Spectrogram)
            vocal_inputs: (B, T, 1, L) (Raw Waveform)
        """
        batch_size, T, C_s, H_s, W_s = spectral_inputs.size()
        _, _, C_v, L_v = vocal_inputs.size()
        
        # 1. Spectral Stream Features
        s_in = spectral_inputs.view(batch_size * T, C_s, H_s, W_s)
        s_feats = self.spectral_cnn(s_in)
        s_feats = self.spectral_pool(s_feats).view(batch_size * T, -1)
        f_s = self.spectral_proj(s_feats).view(batch_size, T, 256) # (B, T, 256)
        
        # 2. Vocal Stream Features
        v_in = vocal_inputs.view(batch_size * T, C_v, L_v)
        v_feats = self.vocal_cnn(v_in)
        v_feats = self.vocal_pool(v_feats).view(batch_size * T, -1)
        f_v1 = self.vocal_proj_1(v_feats) # (B*T, 128)
        f_v2 = self.vocal_proj_2(f_v1).view(batch_size, T, 256) # (B, T, 256)
        
        # 3. Concatenate streams -> 512-d per-chunk feature
        f_cat = torch.cat([f_s, f_v2], dim=-1)  # (B, T, 512)
        
        # 4. Temporal Modeling
        # A. TGF (Temporal Gradient Fusion)
        diff = torch.zeros_like(f_cat)
        diff[:, 1:, :] = f_cat[:, 1:, :] - f_cat[:, :-1, :]
        fused = torch.cat([f_cat, diff], dim=-1)  # (B, T, 1024)
        f_tgf = self.tgf_proj(fused)                # (B, T, 512)
        
        # B. Temporal Self-Attention
        f_attn = self.transformer(f_tgf)             # (B, T, 512)
        
        # C. BiLSTM
        lstm_out, _ = self.bilstm(f_attn)           # (B, T, 512)
        
        # Average pool over time sequence to obtain clip-level representation
        clip_repr = lstm_out.mean(dim=1)            # (B, 512)
        
        # 5. Classification Output
        logits = self.classifier(clip_repr)         # (B, 2)
        
        return logits
