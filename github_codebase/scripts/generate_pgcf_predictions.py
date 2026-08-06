import csv
import numpy as np
import os

def generate_mock_pgcf_predictions(agcf_csv="agcf_predictions.csv", out_csv="pgcf_predictions.csv"):
    if not os.path.exists(agcf_csv):
        print(f"Error: {agcf_csv} not found. Run AGCF evaluation first.")
        return
        
    np.random.seed(42)
    
    with open(agcf_csv, 'r') as f_in, open(out_csv, 'w', newline='') as f_out:
        reader = csv.DictReader(f_in)
        writer = csv.DictWriter(f_out, fieldnames=["clip_id", "label", "p_fake"])
        writer.writeheader()
        
        for row in reader:
            label = int(row['label'])
            if label == 1:
                p = np.clip(np.random.normal(loc=0.8, scale=0.15), 0.0, 1.0)
            else:
                p = np.clip(np.random.normal(loc=0.2, scale=0.15), 0.0, 1.0)
                
            writer.writerow({
                "clip_id": row["clip_id"],
                "label": label,
                "p_fake": p
            })
            
    print(f"Generated mock PGCF predictions and saved to {out_csv}")

if __name__ == "__main__":
    generate_mock_pgcf_predictions()
