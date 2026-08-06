import os
import torch
import torch.nn.functional as F
from torch.utils.data import DataLoader
from src.agcf.dataset import AGCFDataset
from src.agcf.model import AGCF
from sklearn.metrics import accuracy_score, roc_auc_score, f1_score, precision_score, recall_score, confusion_matrix, roc_curve, precision_recall_curve
import pandas as pd
import numpy as np

def evaluate_agcf(base_dir, model_path="saved_models/agcf_best.pth", out_csv="agcf_predictions.csv"):
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    
    val_dataset = AGCFDataset(base_dir, split="val", max_real=500, max_fake=500, val_ratio=0.2)
    val_loader = DataLoader(val_dataset, batch_size=4, shuffle=False, num_workers=2)
    
    model = AGCF(num_frames=16).to(device)
    if os.path.exists(model_path):
        model.load_state_dict(torch.load(model_path, map_location=device))
        print(f"Loaded model from {model_path}")
    else:
        print(f"Model file {model_path} not found. Evaluating with untrained weights.")
        
    model.eval()
    
    all_labels = []
    all_preds = []
    all_probs_fake = []
    all_paths = []
    
    with torch.no_grad():
        for spectral, vocal, labels, paths in val_loader:
            spectral, vocal = spectral.to(device), vocal.to(device)
            logits = model(spectral, vocal)
            probs = F.softmax(logits, dim=1)
            
            # Label 0 is FAKE, Label 1 is REAL
            # p_fake is probability of class 0
            probs_fake = probs[:, 0].cpu().numpy()
            
            _, predicted = torch.max(logits.data, 1)
            
            all_labels.extend(labels.cpu().numpy())
            all_preds.extend(predicted.cpu().numpy())
            all_probs_fake.extend(probs_fake)
            all_paths.extend(paths)
            
    # Calculate metrics
    # For metrics, we usually treat FAKE (0) as positive class in deepfake detection, or REAL (1) as positive.
    # The paper uses Fake as positive class, so we invert labels for sklearn: Fake=1, Real=0
    y_true = np.array([1 if l == 0 else 0 for l in all_labels])
    y_pred = np.array([1 if p == 0 else 0 for p in all_preds])
    y_score = np.array(all_probs_fake)
    
    acc = accuracy_score(y_true, y_pred)
    auc = roc_auc_score(y_true, y_score)
    f1 = f1_score(y_true, y_pred)
    prec = precision_score(y_true, y_pred)
    rec = recall_score(y_true, y_pred)
    cm = confusion_matrix(y_true, y_pred)
    
    print("\n--- AGCF Evaluation Metrics ---")
    print(f"Accuracy:  {acc:.4f}")
    print(f"AUC:       {auc:.4f}")
    print(f"F1 Score:  {f1:.4f}")
    print(f"Precision: {prec:.4f}")
    print(f"Recall:    {rec:.4f}")
    print("Confusion Matrix (Fake=1, Real=0):")
    print(cm)
    
    # Save predictions
    df = pd.DataFrame({
        "clip_id": [os.path.basename(p) for p in all_paths],
        "label": y_true, # 1 for Fake, 0 for Real
        "p_fake": all_probs_fake
    })
    df.to_csv(out_csv, index=False)
    print(f"\nSaved predictions to {out_csv}")
    
    return acc, auc, f1, prec, rec

if __name__ == '__main__':
    base_dir = r"c:\deepfake\archive (1)\FakeAVCeleb_v1.2\FakeAVCeleb_v1.2"
    evaluate_agcf(base_dir)
