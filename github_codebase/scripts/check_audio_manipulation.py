import os
import subprocess
import numpy as np
import scipy.io.wavfile as wav
import tempfile
from scipy.spatial.distance import euclidean
import glob

import torchvision.io as io
import torch

def compare_audio(real_video, fake_video):
    try:
        _, real_aframes, info1 = io.read_video(real_video, pts_unit="sec", output_format="TCHW")
        _, fake_aframes, info2 = io.read_video(fake_video, pts_unit="sec", output_format="TCHW")
        
        if real_aframes is None or fake_aframes is None or real_aframes.numel() == 0 or fake_aframes.numel() == 0:
            return 0.0
            
        # Select first channel (mono)
        sig1 = real_aframes[0].float()
        sig2 = fake_aframes[0].float()
        
        # normalize
        sig1 = sig1 / (torch.max(torch.abs(sig1)) + 1e-8)
        sig2 = sig2 / (torch.max(torch.abs(sig2)) + 1e-8)
        
        # compare using simple mse
        min_len = min(len(sig1), len(sig2))
        sig1 = sig1[:min_len]
        sig2 = sig2[:min_len]
        
        mse = torch.mean((sig1 - sig2)**2).item()
        
    except Exception as e:
        print(f"Error reading {real_video} or {fake_video}: {e}")
        return 0.0
        
    return mse

def main():
    # The dataset is in archive(1)
    base_dir = r"c:\deepfake\archive (1)\FakeAVCeleb_v1.2\FakeAVCeleb_v1.2"
    
    real_dir = os.path.join(base_dir, "RealVideo-RealAudio")
    fake_dir = os.path.join(base_dir, "FakeVideo-FakeAudio")
    
    # Let's find a matching ethnic/person folder, e.g. African\id00016
    ethnicities = ["African", "Asian (East)", "Asian (South)", "Caucasian (American)", "Caucasian (European)"]
    
    pairs_tested = 0
    total_mse = 0
    
    for eth in ethnicities:
        real_eth = os.path.join(real_dir, eth)
        fake_eth = os.path.join(fake_dir, eth)
        
        if not os.path.exists(real_eth) or not os.path.exists(fake_eth):
            continue
            
        for gender in ["men", "women"]:
            real_gen = os.path.join(real_eth, gender)
            fake_gen = os.path.join(fake_eth, gender)
            
            if not os.path.exists(real_gen) or not os.path.exists(fake_gen):
                continue
                
            persons = os.listdir(real_gen)
            for p in persons:
                p_real_dir = os.path.join(real_gen, p)
                p_fake_dir = os.path.join(fake_gen, p)
                
                if not os.path.isdir(p_real_dir) or not os.path.isdir(p_fake_dir):
                    continue
                    
                real_vids = glob.glob(os.path.join(p_real_dir, "*.mp4"))
                fake_vids = glob.glob(os.path.join(p_fake_dir, "*.mp4"))
                
                if real_vids and fake_vids:
                    # compare the first video of real and fake
                    mse = compare_audio(real_vids[0], fake_vids[0])
                    total_mse += mse
                    pairs_tested += 1
                    print(f"Compared {p}: MSE = {mse:.6f}")
                    
                if pairs_tested >= 5:
                    break
            if pairs_tested >= 5:
                break
        if pairs_tested >= 5:
            break
            
    if pairs_tested > 0:
        avg_mse = total_mse / pairs_tested
        print(f"Average MSE across {pairs_tested} pairs: {avg_mse:.6f}")
        if avg_mse < 0.01:
            print("WARNING: Real and Fake audio tracks are near-identical (MSE < 0.01).")
            print("AGCF would have no discriminative signal to learn from.")
            print("The dataset needs audio-manipulated fakes before this direction is viable.")
        else:
            print("SUCCESS: Audio tracks show significant differences. Safe to proceed with AGCF training.")
    else:
        print("Could not find matching real/fake pairs to compare.")

if __name__ == "__main__":
    main()
