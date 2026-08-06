import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib
from sklearn.metrics import (
    roc_curve, auc, precision_recall_curve, average_precision_score,
    confusion_matrix, accuracy_score, f1_score, precision_score, recall_score
)

# Apply styling similar to the original generate_graphs.py
matplotlib.rcParams['font.family'] = 'DejaVu Sans'
matplotlib.rcParams['axes.linewidth'] = 1.2
FIG_DIR = 'figures_fusion'
os.makedirs(FIG_DIR, exist_ok=True)

def generate_fusion_graphs(pgcf_csv="pgcf_predictions.csv", agcf_csv="agcf_predictions.csv"):
    if not os.path.exists(pgcf_csv) or not os.path.exists(agcf_csv):
        print(f"Error: Need both {pgcf_csv} and {agcf_csv} to generate graphs.")
        return
        
    df_pgcf = pd.read_csv(pgcf_csv)
    df_agcf = pd.read_csv(agcf_csv)
    
    # Merge
    df_merged = pd.merge(df_pgcf, df_agcf, on=["clip_id", "label"], suffixes=('_pgcf', '_agcf'))
    
    if len(df_merged) == 0:
        print("No matching clip_ids found.")
        return
        
    y_true = df_merged['label'].values
    p_video = df_merged['p_fake_pgcf'].values
    p_audio = df_merged['p_fake_agcf'].values
    
    # Define models
    models_data = {
        'PGCF (Video)': {
            'probs': p_video,
            'preds': (p_video > 0.5).astype(int),
            'color': '#FF6B6B'
        },
        'AGCF (Audio)': {
            'probs': p_audio,
            'preds': (p_audio > 0.5).astype(int),
            'color': '#45B7D1'
        },
        'Late Fusion (Soft)': {
            'probs': p_video * p_audio,
            'preds': ((p_video * p_audio) > 0.25).astype(int),
            'color': '#96CEB4'
        },
        'Late Fusion (Hard AND)': {
            'probs': p_video * p_audio, # For ROC, proxy
            'preds': ((p_video > 0.5) & (p_audio > 0.5)).astype(int),
            'color': '#FFEEAD'
        }
    }
    
    print("Generating graphs...")
    
    # ============================================================
    # 1. ROC CURVES (Excluding Hard AND for curves as it's discrete)
    # ============================================================
    curve_models = ['PGCF (Video)', 'AGCF (Audio)', 'Late Fusion (Soft)']
    
    fig, ax = plt.subplots(figsize=(8, 7))
    for name in curve_models:
        data = models_data[name]
        fpr, tpr, _ = roc_curve(y_true, data['probs'])
        roc_auc = auc(fpr, tpr)
        ax.plot(fpr, tpr, color=data['color'], lw=2.5, label=f'{name} (AUC = {roc_auc:.4f})')
        
    ax.plot([0, 1], [0, 1], 'k--', lw=1, alpha=0.5)
    ax.set_xlabel('False Positive Rate', fontsize=13)
    ax.set_ylabel('True Positive Rate', fontsize=13)
    ax.set_title('ROC Curves — Fusion Comparison', fontsize=15, fontweight='bold')
    ax.legend(fontsize=12, loc='lower right')
    ax.grid(alpha=0.3); ax.set_xlim([0, 1]); ax.set_ylim([0, 1.02])
    plt.tight_layout()
    plt.savefig(os.path.join(FIG_DIR, 'fusion_roc_curves.png'), dpi=200, bbox_inches='tight')
    print("Done: ROC Curves saved")
    
    # ============================================================
    # 2. PRECISION-RECALL CURVES
    # ============================================================
    fig, ax = plt.subplots(figsize=(8, 7))
    for name in curve_models:
        data = models_data[name]
        precision, recall, _ = precision_recall_curve(y_true, data['probs'])
        ap = average_precision_score(y_true, data['probs'])
        ax.plot(recall, precision, color=data['color'], lw=2.5, label=f'{name} (AP = {ap:.4f})')
        
    ax.set_xlabel('Recall', fontsize=13)
    ax.set_ylabel('Precision', fontsize=13)
    ax.set_title('Precision–Recall Curves — Fusion Comparison', fontsize=15, fontweight='bold')
    ax.legend(fontsize=12, loc='lower left')
    ax.grid(alpha=0.3); ax.set_xlim([0, 1]); ax.set_ylim([0, 1.02])
    plt.tight_layout()
    plt.savefig(os.path.join(FIG_DIR, 'fusion_pr_curves.png'), dpi=200, bbox_inches='tight')
    print("Done: Precision-Recall Curves saved")
    
    # ============================================================
    # 3. CONFUSION MATRICES
    # ============================================================
    fig, axes = plt.subplots(2, 2, figsize=(11, 10))
    axes = axes.flatten()
    
    for i, name in enumerate(models_data.keys()):
        ax = axes[i]
        data = models_data[name]
        cm = confusion_matrix(y_true, data['preds'])
        im = ax.imshow(cm, cmap='Blues', interpolation='nearest')
        ax.set_title(f'{name}', fontsize=14, fontweight='bold')
        ax.set_xlabel('Predicted', fontsize=12)
        ax.set_ylabel('Actual', fontsize=12)
        ax.set_xticks([0, 1]); ax.set_yticks([0, 1])
        ax.set_xticklabels(['Real', 'Fake']); ax.set_yticklabels(['Real', 'Fake'])
        
        for row in range(2):
            for col in range(2):
                color = 'white' if cm[row, col] > cm.max() * 0.5 else 'black'
                ax.text(col, row, f'{cm[row,col]}', ha='center', va='center', fontsize=18, fontweight='bold', color=color)
                
    fig.suptitle('Confusion Matrices — Fusion Strategies', fontsize=16, fontweight='bold', y=1.02)
    plt.tight_layout()
    plt.savefig(os.path.join(FIG_DIR, 'fusion_confusion_matrices.png'), dpi=200, bbox_inches='tight')
    print("Done: Confusion Matrices saved")
    
    # ============================================================
    # 4. BAR CHART COMPARISON
    # ============================================================
    metrics_names = ['Accuracy', 'Precision', 'Recall', 'F1-Score', 'AUC-ROC']
    model_names = list(models_data.keys())
    
    fig, ax = plt.subplots(figsize=(11, 7))
    y_positions = np.arange(len(metrics_names))
    bar_height = 0.20
    
    for i, name in enumerate(model_names):
        data = models_data[name]
        preds = data['preds']
        probs = data['probs']
        
        metrics = [
            accuracy_score(y_true, preds),
            precision_score(y_true, preds, zero_division=0),
            recall_score(y_true, preds, zero_division=0),
            f1_score(y_true, preds, zero_division=0),
            auc(*roc_curve(y_true, probs)[:2]) if name != 'Late Fusion (Hard AND)' else 0.0 # Don't plot AUC for Hard AND
        ]
        
        # Calculate offset for grouped bars
        offset = (i - len(model_names)/2 + 0.5) * bar_height
        
        ax.barh(y_positions + offset, metrics, bar_height, 
                label=name, color=data['color'], alpha=0.9, edgecolor='white')
        
        # Add labels on bars
        for j, val in enumerate(metrics):
            if val > 0: # Skip AUC for Hard AND
                ax.text(val + 0.01, y_positions[j] + offset, f'{val:.3f}', 
                        va='center', fontsize=9, fontweight='bold')
                
    ax.set_yticks(y_positions)
    ax.set_yticklabels(metrics_names, fontsize=12)
    ax.set_xlabel('Score', fontsize=13)
    ax.set_title('Comprehensive Metrics Comparison', fontsize=15, fontweight='bold')
    ax.legend(fontsize=11, loc='upper left', bbox_to_anchor=(1, 1))
    ax.grid(axis='x', alpha=0.3)
    ax.set_xlim([0, 1.1])
    plt.tight_layout()
    plt.savefig(os.path.join(FIG_DIR, 'fusion_metrics_comparison.png'), dpi=200, bbox_inches='tight')
    print("Done: Metrics Comparison saved")

if __name__ == "__main__":
    generate_fusion_graphs()
