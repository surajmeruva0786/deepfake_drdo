import pandas as pd
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
from src.fusion.and_gate import fuse_predictions
import os

def evaluate_predictions(y_true, y_pred, name="Model"):
    acc = accuracy_score(y_true, y_pred)
    prec = precision_score(y_true, y_pred)
    rec = recall_score(y_true, y_pred)
    f1 = f1_score(y_true, y_pred)
    return {"Model": name, "Accuracy": acc, "Precision": prec, "Recall": rec, "F1": f1}

def compare_eval(pgcf_csv="pgcf_predictions.csv", agcf_csv="agcf_predictions.csv"):
    if not os.path.exists(pgcf_csv) or not os.path.exists(agcf_csv):
        print(f"Error: Need both {pgcf_csv} and {agcf_csv} to compare.")
        return
        
    df_pgcf = pd.read_csv(pgcf_csv)
    df_agcf = pd.read_csv(agcf_csv)
    
    # Merge on clip_id to ensure aligned predictions
    df_merged = pd.merge(df_pgcf, df_agcf, on=["clip_id", "label"], suffixes=('_pgcf', '_agcf'))
    
    if len(df_merged) == 0:
        print("No matching clip_ids found between the two prediction files.")
        return
        
    y_true = df_merged['label'].values
    p_video = df_merged['p_fake_pgcf'].values
    p_audio = df_merged['p_fake_agcf'].values
    
    # 1. PGCF alone
    y_pred_pgcf = (p_video > 0.5).astype(int)
    metrics_pgcf = evaluate_predictions(y_true, y_pred_pgcf, "PGCF (Video Only)")
    
    # 2. AGCF alone
    y_pred_agcf = (p_audio > 0.5).astype(int)
    metrics_agcf = evaluate_predictions(y_true, y_pred_agcf, "AGCF (Audio Only)")
    
    # 3. AND-fused (hard)
    _, y_pred_fused_hard = fuse_predictions(p_video, p_audio, mode="hard")
    metrics_fused_hard = evaluate_predictions(y_true, y_pred_fused_hard, "Late Fusion (Hard AND)")
    
    # 4. Soft-fused (product t-norm)
    _, y_pred_fused_soft = fuse_predictions(p_video, p_audio, mode="soft")
    metrics_fused_soft = evaluate_predictions(y_true, y_pred_fused_soft, "Late Fusion (Soft Product)")
    
    results = pd.DataFrame([metrics_pgcf, metrics_agcf, metrics_fused_hard, metrics_fused_soft])
    
    print("\n=== Three-Way Comparison Table ===")
    print(results.to_string(index=False))
    
    results.to_csv("fusion_comparison_results.csv", index=False)
    print("\nSaved comparison results to fusion_comparison_results.csv")

if __name__ == "__main__":
    # Can be run manually if CSVs are present
    compare_eval()
