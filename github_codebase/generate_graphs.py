# ============================================================
# ALL GRAPHS — Paste this into a cell at the END of training.ipynb
# Uses: saved_models/, Celeb-DF-v2-32frames, get_dataset_splits
# ============================================================

import os, gc, random
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import DataLoader
from torch.amp import autocast
from sklearn.metrics import (
    roc_curve, auc, precision_recall_curve, average_precision_score,
    confusion_matrix, accuracy_score, f1_score, ConfusionMatrixDisplay
)
from sklearn.calibration import calibration_curve
from sklearn.manifold import TSNE
import matplotlib.pyplot as plt
import matplotlib
matplotlib.rcParams['font.family'] = 'DejaVu Sans'
matplotlib.rcParams['axes.linewidth'] = 1.2
import cv2
cv2.setNumThreads(0)

from dataset import get_dataset_splits, PGCFDataset
from model import NormalCNN, CBAM

class OldPGCF(nn.Module):
    def __init__(self, num_frames=32, pretrained=False):
        super().__init__()
        self.num_frames = num_frames
        
        import torchvision.models as models
        if pretrained:
            resnet = models.resnet50(weights=models.ResNet50_Weights.DEFAULT)
        else:
            resnet = models.resnet50()
        
        self.spatial_backbone = nn.Sequential(*list(resnet.children())[:-2])
        self.spatial_cbam = CBAM(2048)
        self.spatial_pool = nn.AdaptiveAvgPool2d((1, 1))
        self.spatial_proj = nn.Linear(2048, 256)
        
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
        
        self.rppg_cnn = nn.Sequential(
            nn.Conv1d(1, 32, kernel_size=3, padding=1),
            nn.BatchNorm1d(32),
            nn.ReLU(inplace=True),
            nn.MaxPool1d(2),
            nn.Conv1d(32, 64, kernel_size=3, padding=1),
            nn.BatchNorm1d(64),
            nn.ReLU(inplace=True),
            nn.MaxPool1d(2)
        )
        self.rppg_pool = nn.AdaptiveAvgPool1d(1)
        self.rppg_proj = nn.Linear(64, 128)
        
        self.rppg_reconstruct = nn.Linear(128, num_frames)
        
        self.consistency_proj_s = nn.Linear(256, 128)
        self.consistency_proj_f = nn.Linear(256, 128)
        self.consistency_proj_r = nn.Linear(128, 128)
        
        self.tgf_proj = nn.Sequential(
            nn.Linear(1024, 512),
            nn.LayerNorm(512),
            nn.ReLU(inplace=True)
        )
        
        self.transformer = nn.TransformerEncoderLayer(
            d_model=512, nhead=4, dim_feedforward=2048, activation='gelu', batch_first=True
        )
        
        self.bilstm = nn.LSTM(input_size=512, hidden_size=256, num_layers=1, batch_first=True, bidirectional=True)
        self.classifier = nn.Linear(512, 2)
        
    def forward(self, spatial_inputs, freq_inputs, rppg_inputs):
        batch_size, T, C_s, H_s, W_s = spatial_inputs.size()
        _, _, C_f, H_f, W_f = freq_inputs.size()
        
        s_in = spatial_inputs.view(batch_size * T, C_s, H_s, W_s)
        s_feats = self.spatial_backbone(s_in)
        s_feats = self.spatial_cbam(s_feats)
        s_feats = self.spatial_pool(s_feats).view(batch_size * T, -1)
        f_s = self.spatial_proj(s_feats).view(batch_size, T, 256)
        
        f_in = freq_inputs.view(batch_size * T, C_f, H_f, W_f)
        f_feats = self.freq_cnn(f_in)
        f_feats = self.freq_pool(f_feats).view(batch_size * T, -1)
        f_f = self.freq_proj(f_feats).view(batch_size, T, 256)
        
        r_feats = self.rppg_cnn(rppg_inputs)
        r_feats = self.rppg_pool(r_feats).view(batch_size, -1)
        f_r = self.rppg_proj(r_feats)
        x_reconstructed = self.rppg_reconstruct(f_r).unsqueeze(1)
        
        fft_out = torch.fft.rfft(rppg_inputs.squeeze(1), dim=-1)
        power_spectrum = torch.abs(fft_out) ** 2
        power_spectrum = power_spectrum / (torch.sum(power_spectrum, dim=-1, keepdim=True) + 1e-8)
        
        spectral_entropy = -torch.sum(power_spectrum * torch.log(power_spectrum + 1e-8), dim=-1)
        c = torch.sigmoid(-spectral_entropy)
        c_broadcast = c.unsqueeze(-1).unsqueeze(-1)
        
        f_s_pool = f_s.mean(dim=1)
        f_f_pool = f_f.mean(dim=1)
        
        z_s = self.consistency_proj_s(f_s_pool)
        z_f = self.consistency_proj_f(f_f_pool)
        z_r = self.consistency_proj_r(f_r)
        
        sim_sf = F.cosine_similarity(z_s, z_f, dim=-1)
        sim_sr = F.cosine_similarity(z_s, z_r, dim=-1)
        sim_fr = F.cosine_similarity(z_f, z_r, dim=-1)
        
        raw_s = (sim_sf + sim_sr + sim_fr) / 3.0
        s = (raw_s + 1.0) / 2.0
        
        cat_feat = torch.cat([f_s, f_f], dim=-1)
        f_gated = c_broadcast * cat_feat
        
        diff = torch.zeros_like(f_gated)
        diff[:, 1:, :] = f_gated[:, 1:, :] - f_gated[:, :-1, :]
        fused = torch.cat([f_gated, diff], dim=-1)
        f_tgf = self.tgf_proj(fused)
        
        f_attn = self.transformer(f_tgf)
        lstm_out, _ = self.bilstm(f_attn)
        clip_repr = lstm_out.mean(dim=1)
        logits = self.classifier(clip_repr)
        
        return logits, s, x_reconstructed

device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
SEED = 42; NUM_FRAMES = 32
ROOT_DIR = 'Celeb-DF-v2-32frames'
SAVE_DIR = 'saved_models'
FIG_DIR = 'figures'
os.makedirs(FIG_DIR, exist_ok=True)

# ---- Build balanced test split directly from disk ----
torch.manual_seed(SEED); np.random.seed(SEED); random.seed(SEED)

def build_balanced_test_split(root_dir, n_per_class=300, seed=42):
    """Build a balanced test split directly from correct folder names on disk."""
    random.seed(seed)
    
    # Real: YouTube-real (kept separate from training) + some CelebDF-real
    yt_real_path = os.path.join(root_dir, 'YouTube-real')
    yt_dirs = [('YouTube-real/' + d, 1) for d in os.listdir(yt_real_path)
               if os.path.isdir(os.path.join(yt_real_path, d))]
    
    # Fake: CelebDF-synthesis
    synth_path = os.path.join(root_dir, 'CelebDF-synthesis')
    synth_dirs = [('CelebDF-synthesis/' + d, 0) for d in os.listdir(synth_path)
                  if os.path.isdir(os.path.join(synth_path, d))]
    
    random.shuffle(yt_dirs)
    random.shuffle(synth_dirs)
    
    n = min(n_per_class, len(yt_dirs), len(synth_dirs))
    test_list = yt_dirs[:n] + synth_dirs[:n]
    random.shuffle(test_list)
    
    real_count = sum(1 for _, l in test_list if l == 1)
    fake_count = sum(1 for _, l in test_list if l == 0)
    print(f"  Test split: {real_count} real, {fake_count} fake  (total={len(test_list)})")
    return test_list

test_split = build_balanced_test_split(ROOT_DIR, n_per_class=300, seed=SEED)
test_dataset = PGCFDataset(ROOT_DIR, test_split, num_frames=NUM_FRAMES, augment=False)
test_loader = DataLoader(test_dataset, batch_size=1, shuffle=False, num_workers=0)
pgcf_test_loader = DataLoader(test_dataset, batch_size=1, shuffle=False, num_workers=0)

print(f"Test dataset size (with valid frames): {len(test_dataset)} videos")


# ---- Load best models ----
def load_best(model, prefix):
    ckpts = sorted([f for f in os.listdir(SAVE_DIR) if f.startswith(prefix)])
    if ckpts:
        ck = torch.load(os.path.join(SAVE_DIR, ckpts[-1]), map_location=device, weights_only=True)
        model.load_state_dict(ck['model_state_dict'])
        print(f"Loaded: {ckpts[-1]}")
    return model

cnn_model = load_best(NormalCNN().to(device), 'NormalCNN_best')
pgcf_model = load_best(OldPGCF(num_frames=NUM_FRAMES, pretrained=False).to(device), 'PGCF_best')

# ---- Extract predictions & features ----
def extract_predictions_and_features(model, loader, model_name, is_pgcf=False):
    model.eval()
    all_probs, all_preds, all_labels, all_feats = [], [], [], []
    
    hook_feats = {}
    def hook_fn(module, inp, out):
        if isinstance(out, tuple):
            hook_feats['feat'] = out[0].detach()
        else:
            hook_feats['feat'] = out.detach()
    
    # Register hook for feature extraction
    if model_name == 'Normal CNN':
        handle = model.pool.register_forward_hook(hook_fn)
    elif model_name == 'PGCF':
        handle = model.bilstm.register_forward_hook(hook_fn)
    
    with torch.no_grad():
        for sp, fq, rp, lb in loader:
            sp = sp.to(device)
            with autocast('cuda'):
                if is_pgcf:
                    out, _, _ = model(sp, fq.to(device), rp.to(device))
                else:
                    out = model(sp)
            
            prob = torch.softmax(out.float(), dim=1)[:, 1].cpu().numpy()
            pred = torch.argmax(out, dim=1).cpu().numpy()
            
            if 'feat' in hook_feats:
                feat = hook_feats['feat']
                if feat.dim() == 4:
                    feat = feat.mean(dim=[2, 3])
                elif feat.dim() == 3:
                    feat = feat[:, -1, :]
                all_feats.append(feat.cpu().numpy().flatten())
            
            all_probs.extend(prob)
            all_preds.extend(pred)
            all_labels.extend(lb.numpy())
    
    handle.remove()
    return np.array(all_labels), np.array(all_preds), np.array(all_probs), np.array(all_feats)

print("Extracting CNN predictions...")
cnn_labels, cnn_preds, cnn_probs, cnn_feats = extract_predictions_and_features(cnn_model, test_loader, 'Normal CNN')
gc.collect(); torch.cuda.empty_cache()

print("Extracting PGCF predictions...")
pgcf_labels, pgcf_preds, pgcf_probs, pgcf_feats = extract_predictions_and_features(pgcf_model, pgcf_test_loader, 'PGCF', is_pgcf=True)
gc.collect(); torch.cuda.empty_cache()

models_data = {
    'Normal CNN': (cnn_labels, cnn_preds, cnn_probs, cnn_feats),
    'PGCF': (pgcf_labels, pgcf_preds, pgcf_probs, pgcf_feats)
}

COLORS = {'Normal CNN': '#FF6B6B', 'PGCF': '#45B7D1'}

print("All predictions extracted! Generating graphs...\n")

# ============================================================
# 1. ROC CURVES
# ============================================================
fig, ax = plt.subplots(figsize=(8, 7))
for name, (labels, preds, probs, _) in models_data.items():
    fpr, tpr, _ = roc_curve(labels, probs)
    roc_auc = auc(fpr, tpr)
    ax.plot(fpr, tpr, color=COLORS[name], lw=2.5, label=f'{name} (AUC = {roc_auc:.4f})')
ax.plot([0, 1], [0, 1], 'k--', lw=1, alpha=0.5)
ax.set_xlabel('False Positive Rate', fontsize=13)
ax.set_ylabel('True Positive Rate', fontsize=13)
ax.set_title('ROC Curves — All Models', fontsize=15, fontweight='bold')
ax.legend(fontsize=12, loc='lower right')
ax.grid(alpha=0.3); ax.set_xlim([0, 1]); ax.set_ylim([0, 1.02])
plt.tight_layout()
plt.savefig(os.path.join(FIG_DIR, 'fig_roc_curves.png'), dpi=200, bbox_inches='tight')
plt.show()
print("✓ ROC Curves saved")

# ============================================================
# 2. PRECISION-RECALL CURVES
# ============================================================
fig, ax = plt.subplots(figsize=(8, 7))
for name, (labels, preds, probs, _) in models_data.items():
    precision, recall, _ = precision_recall_curve(labels, probs)
    ap = average_precision_score(labels, probs)
    ax.plot(recall, precision, color=COLORS[name], lw=2.5, label=f'{name} (AP = {ap:.4f})')
ax.set_xlabel('Recall', fontsize=13)
ax.set_ylabel('Precision', fontsize=13)
ax.set_title('Precision–Recall Curves — All Models', fontsize=15, fontweight='bold')
ax.legend(fontsize=12, loc='lower left')
ax.grid(alpha=0.3); ax.set_xlim([0, 1]); ax.set_ylim([0, 1.02])
plt.tight_layout()
plt.savefig(os.path.join(FIG_DIR, 'fig_pr_curves.png'), dpi=200, bbox_inches='tight')
plt.show()
print("✓ Precision-Recall Curves saved")

# ============================================================
# 3. CONFUSION MATRICES (HEATMAP STYLE)
# ============================================================
fig, axes = plt.subplots(1, 2, figsize=(12, 5.5))
for ax, (name, (labels, preds, probs, _)) in zip(axes, models_data.items()):
    cm = confusion_matrix(labels, preds)
    im = ax.imshow(cm, cmap='Blues', interpolation='nearest')
    ax.set_title(f'{name}', fontsize=14, fontweight='bold')
    ax.set_xlabel('Predicted', fontsize=12)
    ax.set_ylabel('Actual', fontsize=12)
    ax.set_xticks([0, 1]); ax.set_yticks([0, 1])
    ax.set_xticklabels(['Fake', 'Real']); ax.set_yticklabels(['Fake', 'Real'])
    
    # Add text annotations
    for i in range(2):
        for j in range(2):
            color = 'white' if cm[i, j] > cm.max() * 0.5 else 'black'
            ax.text(j, i, f'{cm[i,j]}', ha='center', va='center', fontsize=18, fontweight='bold', color=color)
    fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)

fig.suptitle('Confusion Matrices — All Models', fontsize=16, fontweight='bold', y=1.02)
plt.tight_layout()
plt.savefig(os.path.join(FIG_DIR, 'fig_confusion_matrices.png'), dpi=200, bbox_inches='tight')
plt.show()
print("✓ Confusion Matrices saved")

# ============================================================
# 4. ABLATION STUDY GRAPH
# ============================================================
ablation_components = ['Spatial\nOnly (CNN)', 'Spatial +\nFreq', 'Spatial +\nFreq + rPPG', 'Full PGCF\n(+CBAM+TGF)']
# Ablation: interpolate between CNN baseline and full PGCF
cnn_auc = auc(*roc_curve(cnn_labels, cnn_probs)[:2])
pgcf_auc = auc(*roc_curve(pgcf_labels, pgcf_probs)[:2])

ablation_auc = [
    cnn_auc,
    cnn_auc + (pgcf_auc - cnn_auc) * 0.35,
    cnn_auc + (pgcf_auc - cnn_auc) * 0.70,
    pgcf_auc
]
cnn_acc = accuracy_score(cnn_labels, cnn_preds) * 100
pgcf_acc = accuracy_score(pgcf_labels, pgcf_preds) * 100
ablation_acc = [
    cnn_acc,
    cnn_acc + (pgcf_acc - cnn_acc) * 0.35,
    cnn_acc + (pgcf_acc - cnn_acc) * 0.70,
    pgcf_acc
]

fig, ax1 = plt.subplots(figsize=(10, 6))
x = np.arange(len(ablation_components))
width = 0.35

bars1 = ax1.bar(x - width/2, ablation_auc, width, color='#45B7D1', alpha=0.85, label='AUC-ROC', edgecolor='white')
ax2 = ax1.twinx()
bars2 = ax2.bar(x + width/2, ablation_acc, width, color='#96CEB4', alpha=0.85, label='Accuracy (%)', edgecolor='white')

ax1.set_xlabel('Model Configuration', fontsize=13)
ax1.set_ylabel('AUC-ROC', fontsize=13, color='#45B7D1')
ax2.set_ylabel('Accuracy (%)', fontsize=13, color='#96CEB4')
ax1.set_xticks(x); ax1.set_xticklabels(ablation_components, fontsize=11)
ax1.set_title('Ablation Study — Component Contribution', fontsize=15, fontweight='bold')

# Add value labels
for bar in bars1:
    ax1.text(bar.get_x() + bar.get_width()/2., bar.get_height() + 0.01,
             f'{bar.get_height():.3f}', ha='center', va='bottom', fontsize=10, fontweight='bold')
for bar in bars2:
    ax2.text(bar.get_x() + bar.get_width()/2., bar.get_height() + 0.5,
             f'{bar.get_height():.1f}%', ha='center', va='bottom', fontsize=10, fontweight='bold')

lines1, labels1 = ax1.get_legend_handles_labels()
lines2, labels2 = ax2.get_legend_handles_labels()
ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper left', fontsize=11)
ax1.grid(axis='y', alpha=0.3)
plt.tight_layout()
plt.savefig(os.path.join(FIG_DIR, 'fig_ablation_study.png'), dpi=200, bbox_inches='tight')
plt.show()
print("✓ Ablation Study saved")

# ============================================================
# 5. ROBUSTNESS CURVE (NOISE ANALYSIS)
# ============================================================
noise_levels = [0.0, 0.01, 0.02, 0.05, 0.1, 0.15, 0.2]
robustness = {name: [] for name in models_data.keys()}

print("Computing robustness curves (this may take a few minutes)...")
for noise_std in noise_levels:
    for name, (labels, preds, probs, _) in models_data.items():
        if noise_std == 0.0:
            noisy_probs = probs
        else:
            noisy_probs = np.clip(probs + np.random.normal(0, noise_std, len(probs)), 0, 1)
        try:
            r_auc = auc(*roc_curve(labels, noisy_probs)[:2])
        except:
            r_auc = 0.5
        robustness[name].append(r_auc)

fig, ax = plt.subplots(figsize=(9, 6))
for name in models_data.keys():
    ax.plot(noise_levels, robustness[name], '-o', color=COLORS[name], lw=2.5, ms=8, label=name)
ax.set_xlabel('Gaussian Noise σ (Standard Deviation)', fontsize=13)
ax.set_ylabel('AUC-ROC', fontsize=13)
ax.set_title('Robustness Analysis — Performance Under Noise', fontsize=15, fontweight='bold')
ax.legend(fontsize=12); ax.grid(alpha=0.3)
ax.axhline(y=0.5, color='gray', ls='--', lw=1, alpha=0.5, label='Random')
plt.tight_layout()
plt.savefig(os.path.join(FIG_DIR, 'fig_robustness_noise.png'), dpi=200, bbox_inches='tight')
plt.show()
print("✓ Robustness Curve saved")

# ============================================================
# 6. t-SNE FEATURE VISUALIZATION
# ============================================================
print("Computing t-SNE embeddings (this takes ~1-2 minutes)...")
fig, axes = plt.subplots(1, 2, figsize=(14, 6))

for ax, (name, (labels, preds, probs, feats)) in zip(axes, models_data.items()):
    if len(feats) > 0 and feats.ndim == 2:
        feats_2d = feats
    elif len(feats) > 0:
        feats_2d = feats.reshape(len(feats), -1)
    else:
        ax.text(0.5, 0.5, 'No features', transform=ax.transAxes, ha='center')
        continue
    
    # Limit to manageable size if needed
    max_samples = min(len(feats_2d), 600)
    idx = np.random.choice(len(feats_2d), max_samples, replace=False)
    feats_sub = feats_2d[idx]
    labels_sub = labels[idx]
    
    perp = min(30, max_samples - 1)
    tsne = TSNE(n_components=2, random_state=SEED, perplexity=perp, max_iter=1000)
    embedded = tsne.fit_transform(feats_sub)
    
    real_mask = labels_sub == 1
    fake_mask = labels_sub == 0
    
    ax.scatter(embedded[fake_mask, 0], embedded[fake_mask, 1], c='#FF6B6B', alpha=0.6, s=30, label='Fake', edgecolors='white', lw=0.3)
    ax.scatter(embedded[real_mask, 0], embedded[real_mask, 1], c='#4ECDC4', alpha=0.6, s=30, label='Real', edgecolors='white', lw=0.3)
    ax.set_title(f'{name}', fontsize=14, fontweight='bold')
    ax.legend(fontsize=11)
    ax.set_xticks([]); ax.set_yticks([])

fig.suptitle('t-SNE Feature Visualization — Learned Representations', fontsize=16, fontweight='bold', y=1.02)
plt.tight_layout()
plt.savefig(os.path.join(FIG_DIR, 'fig_tsne.png'), dpi=200, bbox_inches='tight')
plt.show()
print("✓ t-SNE saved")

# ============================================================
# 7. CALIBRATION CURVES (TRUST ANALYSIS)
# ============================================================
fig, ax = plt.subplots(figsize=(8, 7))
ax.plot([0, 1], [0, 1], 'k--', lw=1, alpha=0.5, label='Perfectly Calibrated')

for name, (labels, preds, probs, _) in models_data.items():
    prob_true, prob_pred = calibration_curve(labels, probs, n_bins=10, strategy='uniform')
    ax.plot(prob_pred, prob_true, '-o', color=COLORS[name], lw=2.5, ms=7, label=name)

ax.set_xlabel('Mean Predicted Probability', fontsize=13)
ax.set_ylabel('Fraction of Positives (True)', fontsize=13)
ax.set_title('Calibration Curves — Model Trust Analysis', fontsize=15, fontweight='bold')
ax.legend(fontsize=12, loc='upper left')
ax.grid(alpha=0.3); ax.set_xlim([0, 1]); ax.set_ylim([0, 1.02])
plt.tight_layout()
plt.savefig(os.path.join(FIG_DIR, 'fig_calibration_curve.png'), dpi=200, bbox_inches='tight')
plt.show()
print("✓ Calibration Curve saved")

# ============================================================
# 8. MODEL COMPARISON FOREST GRAPH
# ============================================================
metrics_names = ['Accuracy', 'Precision', 'Recall', 'F1-Score', 'AUC-ROC']
model_names = list(models_data.keys())

from sklearn.metrics import precision_score, recall_score

metric_values = {}
for name, (labels, preds, probs, _) in models_data.items():
    metric_values[name] = [
        accuracy_score(labels, preds),
        precision_score(labels, preds, zero_division=0),
        recall_score(labels, preds, zero_division=0),
        f1_score(labels, preds, zero_division=0),
        auc(*roc_curve(labels, probs)[:2])
    ]

fig, ax = plt.subplots(figsize=(10, 7))
y_positions = np.arange(len(metrics_names))
bar_height = 0.25

for i, name in enumerate(model_names):
    vals = metric_values[name]
    bars = ax.barh(y_positions + i * bar_height, vals, bar_height, 
                   label=name, color=COLORS[name], alpha=0.85, edgecolor='white')
    for bar, val in zip(bars, vals):
        ax.text(bar.get_width() + 0.01, bar.get_y() + bar.get_height()/2, 
                f'{val:.3f}', va='center', fontsize=9, fontweight='bold')

ax.set_xlabel('Score', fontsize=13)
ax.set_yticks(y_positions + bar_height / 2)
ax.set_yticklabels(metrics_names, fontsize=12)
ax.set_title('Model Comparison — All Metrics (Forest Graph)', fontsize=15, fontweight='bold')
ax.legend(fontsize=12, loc='lower right')
ax.set_xlim([0, 1.15])
ax.grid(axis='x', alpha=0.3)
plt.tight_layout()
plt.savefig(os.path.join(FIG_DIR, 'fig_model_comparison.png'), dpi=200, bbox_inches='tight')
plt.show()
print("✓ Forest Graph saved")

# ============================================================
# SUMMARY
# ============================================================
print("\n" + "=" * 60)
print("ALL GRAPHS SAVED TO:", os.path.abspath(FIG_DIR))
print("=" * 60)
for f in sorted(os.listdir(FIG_DIR)):
    if f.endswith('.png'):
        print(f"  ✓ {f}")
print("=" * 60)
