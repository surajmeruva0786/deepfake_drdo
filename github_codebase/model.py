import torch
import torch.nn as nn
import torch.nn.functional as F
import torchvision.models as models

# ==========================================
# 1. CBAM (Convolutional Block Attention Module)
# ==========================================

class ChannelAttention(nn.Module):
    def __init__(self, in_planes, ratio=16):
        super().__init__()
        self.avg_pool = nn.AdaptiveAvgPool2d(1)
        self.max_pool = nn.AdaptiveMaxPool2d(1)
        
        # Share MLP weights
        self.fc = nn.Sequential(
            nn.Linear(in_planes, in_planes // ratio, bias=False),
            nn.ReLU(inplace=True),
            nn.Linear(in_planes // ratio, in_planes, bias=False)
        )
        self.sigmoid = nn.Sigmoid()
        
    def forward(self, x):
        avg_out = self.fc(self.ca_avg_pooling(x))
        max_out = self.fc(self.ca_max_pooling(x))
        out = avg_out + max_out
        return self.sigmoid(out).unsqueeze(-1).unsqueeze(-1)
        
    def ca_avg_pooling(self, x):
        return self.avg_pool(x).squeeze(-1).squeeze(-1)
        
    def ca_max_pooling(self, x):
        return self.max_pool(x).squeeze(-1).squeeze(-1)


class SpatialAttention(nn.Module):
    def __init__(self, kernel_size=7):
        super().__init__()
        self.conv = nn.Conv2d(2, 1, kernel_size, padding=kernel_size//2, bias=False)
        self.sigmoid = nn.Sigmoid()
        
    def forward(self, x):
        avg_out = torch.mean(x, dim=1, keepdim=True)
        max_out, _ = torch.max(x, dim=1, keepdim=True)
        x_cat = torch.cat([avg_out, max_out], dim=1)
        out = self.conv(x_cat)
        return self.sigmoid(out)


class CBAM(nn.Module):
    def __init__(self, channels, reduction=16):
        super().__init__()
        self.ca = ChannelAttention(channels, reduction)
        self.sa = SpatialAttention()
        
    def forward(self, x):
        x = self.ca(x) * x
        x = self.sa(x) * x
        return x


# ==========================================
# 2. Normal CNN Baseline Model
# ==========================================

class NormalCNN(nn.Module):
    def __init__(self):
        super().__init__()
        # Processes individual frame images of shape (3, 224, 224)
        self.conv = nn.Sequential(
            nn.Conv2d(3, 16, kernel_size=3, padding=1),
            nn.BatchNorm2d(16),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(2),  # -> 112
            
            nn.Conv2d(16, 32, kernel_size=3, padding=1),
            nn.BatchNorm2d(32),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(2),  # -> 56
            
            nn.Conv2d(32, 64, kernel_size=3, padding=1),
            nn.BatchNorm2d(64),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(2),  # -> 28
            
            nn.Conv2d(64, 128, kernel_size=3, padding=1),
            nn.BatchNorm2d(128),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(2),  # -> 14
        )
        self.pool = nn.AdaptiveAvgPool2d((1, 1))
        self.fc = nn.Sequential(
            nn.Linear(128, 128),
            nn.ReLU(inplace=True),
            nn.Dropout(0.5),
            nn.Linear(128, 2)
        )
        
    def forward(self, x):
        # Input shape: (B, T, 3, H, W)
        batch_size, T, C, H, W = x.size()
        x = x.view(batch_size * T, C, H, W)
        
        feats = self.conv(x)
        feats = self.pool(feats).view(batch_size * T, -1)
        logits = self.fc(feats)
        
        # Reshape to (B, T, 2)
        logits = logits.view(batch_size, T, 2)
        
        # Video level classification: average logits over frame sequence T
        video_logits = logits.mean(dim=1)
        return video_logits


# ==========================================
# 3. ResNet50 Baseline Model
# ==========================================

class ResNet50Baseline(nn.Module):
    def __init__(self, pretrained=True):
        super().__init__()
        if pretrained:
            self.resnet = models.resnet50(weights=models.ResNet50_Weights.DEFAULT)
        else:
            self.resnet = models.resnet50()
            
        in_features = self.resnet.fc.in_features
        self.resnet.fc = nn.Linear(in_features, 2)
        
    def forward(self, x):
        # Input shape: (B, T, 3, H, W)
        batch_size, T, C, H, W = x.size()
        x = x.view(batch_size * T, C, H, W)
        
        logits = self.resnet(x) # (B * T, 2)
        
        # Reshape to (B, T, 2)
        logits = logits.view(batch_size, T, 2)
        
        # Video level classification: average logits over frame sequence T
        video_logits = logits.mean(dim=1)
        return video_logits


# ==========================================
# 4. PGCF (Physiology-Guided Consistency Framework)
# ==========================================

class PGCF(nn.Module):
    def __init__(self, num_frames=16, pretrained=True):
        super().__init__()
        self.num_frames = num_frames
        
        # A. Spatial Stream: ResNet50 + CBAM -> 256 projection
        if pretrained:
            resnet = models.resnet50(weights=models.ResNet50_Weights.DEFAULT)
        else:
            resnet = models.resnet50()
        
        # Feature extractor up to layer4
        self.spatial_backbone = nn.Sequential(*list(resnet.children())[:-2])  # outputs (2048, H/32, W/32)
        self.spatial_cbam = CBAM(2048)
        self.spatial_pool = nn.AdaptiveAvgPool2d((1, 1))
        self.spatial_proj = nn.Linear(2048, 256)
        
        # B. Frequency Stream: 3-Layer CNN -> 256 projection
        self.freq_cnn = nn.Sequential(
            nn.Conv2d(4, 32, kernel_size=3, padding=1),
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
        self.freq_pool = nn.AdaptiveAvgPool2d((1, 1))
        self.freq_proj = nn.Linear(64, 256)
        
        # C. rPPG Stream: 1D-CNN -> 128 projection
        self.rppg_cnn = nn.Sequential(
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
        self.rppg_pool = nn.AdaptiveAvgPool1d(1)
        self.rppg_proj = nn.Linear(128, 128)
        
        # Decoder for rPPG signal reconstruction loss (L_rPPG)
        self.rppg_reconstruct = nn.Sequential(
            nn.Linear(128, 256),
            nn.ReLU(inplace=True),
            nn.Linear(256, num_frames)
        )
        
        # PGCMC Cross-Modal Consistency Projectors to compute similarity s
        self.consistency_proj_s = nn.Linear(256, 128)
        self.consistency_proj_f = nn.Linear(256, 128)
        self.consistency_proj_r = nn.Linear(128, 128)
        
        # D. Temporal Modeling
        # TGF (Temporal Gradient Fusion): linear difference projection
        self.tgf_proj = nn.Sequential(
            nn.Linear(1024, 512),
            nn.LayerNorm(512),
            nn.ReLU(inplace=True)
        )
        
        # Temporal Self-Attention: Transformer Encoder Layer
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
        
    def forward(self, spatial_inputs, freq_inputs, rppg_inputs):
        """
        Args:
            spatial_inputs: (B, T, 3, H, W)
            freq_inputs: (B, T, 4, H, W) (RGB + DCT energy map)
            rppg_inputs: (B, 1, T) (CHROM signal)
        """
        batch_size, T, C_s, H_s, W_s = spatial_inputs.size()
        _, _, C_f, H_f, W_f = freq_inputs.size()
        
        # 1. Spatial Stream Features (f_s)
        s_in = spatial_inputs.view(batch_size * T, C_s, H_s, W_s)
        s_feats = self.spatial_backbone(s_in)
        s_feats = self.spatial_cbam(s_feats)
        s_feats = self.spatial_pool(s_feats).view(batch_size * T, -1)
        f_s = self.spatial_proj(s_feats).view(batch_size, T, 256) # (B, T, 256)
        
        # 2. Frequency Stream Features (f_f)
        f_in = freq_inputs.view(batch_size * T, C_f, H_f, W_f)
        f_feats = self.freq_cnn(f_in)
        f_feats = self.freq_pool(f_feats).view(batch_size * T, -1)
        f_f = self.freq_proj(f_feats).view(batch_size, T, 256) # (B, T, 256)
        
        # 3. rPPG Stream Features (f_r) and Reconstruction (x'_r)
        r_feats = self.rppg_cnn(rppg_inputs)
        r_feats = self.rppg_pool(r_feats).view(batch_size, -1)
        f_r = self.rppg_proj(r_feats) # (B, 128)
        x_reconstructed = self.rppg_reconstruct(f_r).unsqueeze(1) # (B, 1, T)
        
        # 4. PGCMC Gating and Cross-Modal Consistency Module
        # A. rPPG Gating Confidence c
        # Normalized FFT power spectrum
        fft_out = torch.fft.rfft(rppg_inputs.squeeze(1), dim=-1)
        power_spectrum = torch.abs(fft_out) ** 2
        power_spectrum = power_spectrum / (torch.sum(power_spectrum, dim=-1, keepdim=True) + 1e-8)
        
        # Spectral Entropy
        spectral_entropy = -torch.sum(power_spectrum * torch.log(power_spectrum + 1e-8), dim=-1)
        c = torch.sigmoid(-spectral_entropy)  # shape (B,)
        c_broadcast = c.unsqueeze(-1).unsqueeze(-1)  # shape (B, 1, 1)
        
        # B. Cross-Modal Consistency score s
        # Pool spatial and frequency features over time to compute clip-level representation
        f_s_pool = f_s.mean(dim=1)  # (B, 256)
        f_f_pool = f_f.mean(dim=1)  # (B, 256)
        
        # Project to common 128-dimensional space
        z_s = self.consistency_proj_s(f_s_pool)  # (B, 128)
        z_f = self.consistency_proj_f(f_f_pool)  # (B, 128)
        z_r = self.consistency_proj_r(f_r)       # (B, 128)
        
        # Pairwise Cosine Similarities
        sim_sf = F.cosine_similarity(z_s, z_f, dim=-1)  # (B,)
        sim_sr = F.cosine_similarity(z_s, z_r, dim=-1)  # (B,)
        sim_fr = F.cosine_similarity(z_f, z_r, dim=-1)  # (B,)
        
        # Average consistency score s, mapped from [-1, 1] to [0, 1]
        raw_s = (sim_sf + sim_sr + sim_fr) / 3.0
        s = (raw_s + 1.0) / 2.0  # shape (B,)
        
        # C. Gated Fusion
        cat_feat = torch.cat([f_s, f_f], dim=-1)  # (B, T, 512)
        f_gated = c_broadcast * cat_feat         # (B, T, 512)
        
        # 5. Temporal Modeling
        # A. TGF (Temporal Gradient Fusion)
        diff = torch.zeros_like(f_gated)
        diff[:, 1:, :] = f_gated[:, 1:, :] - f_gated[:, :-1, :]
        fused = torch.cat([f_gated, diff], dim=-1)  # (B, T, 1024)
        f_tgf = self.tgf_proj(fused)                # (B, T, 512)
        
        # B. Temporal Self-Attention
        f_attn = self.transformer(f_tgf)             # (B, T, 512)
        
        # C. BiLSTM
        lstm_out, _ = self.bilstm(f_attn)           # (B, T, 512)
        
        # Average pool over time sequence to obtain clip-level representation
        clip_repr = lstm_out.mean(dim=1)            # (B, 512)
        
        # 6. Classification Output
        logits = self.classifier(clip_repr)         # (B, 2)
        
        return logits, s, x_reconstructed
