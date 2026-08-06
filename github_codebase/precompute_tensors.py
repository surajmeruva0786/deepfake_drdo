"""
Pre-compute all tensors (spatial, frequency, rPPG) and save as .pt files.
This removes ALL cv2/numpy work from training — just torch.load() per sample.

Output: Combined-32frames-tensors/<category>/<video_name>.pt
Each .pt file contains: {'spatial': (T,3,H,W), 'freq': (T,4,H,W), 'rppg': (1,T)}
"""
import os
import cv2
import numpy as np
import torch
import time
from utils import compute_dct_map, compute_chrom_signal

cv2.setNumThreads(0)

INPUT_ROOT = 'Combined-32frames'
OUTPUT_ROOT = 'Combined-32frames-tensors'
NUM_FRAMES = 32
RESIZE = 224

MEAN_RGB = np.array([0.485, 0.456, 0.406], dtype=np.float32)
STD_RGB = np.array([0.229, 0.224, 0.225], dtype=np.float32)


def process_video_folder(folder_path):
    """Convert a 32-frame folder into pre-computed tensors."""
    all_frames = sorted([f for f in os.listdir(folder_path) if f.endswith('.jpg')])
    total_avail = len(all_frames)
    
    if total_avail == 0:
        return None
    
    # Sample frames
    indices = np.linspace(0, total_avail - 1, NUM_FRAMES, dtype=int).tolist()
    sampled = [all_frames[i] for i in indices]
    
    frames_bgr = []
    for file in sampled:
        img = cv2.imread(os.path.join(folder_path, file))
        if img is None:
            img = np.zeros((256, 256, 3), dtype=np.uint8)
        frames_bgr.append(img)
    
    # CHROM signal
    chrom = compute_chrom_signal(frames_bgr)
    
    spatial_list = []
    freq_list = []
    
    for frame in frames_bgr:
        resized = cv2.resize(frame, (RESIZE, RESIZE), interpolation=cv2.INTER_AREA)
        
        # DCT map
        dct_map = compute_dct_map(resized)
        
        # BGR -> RGB
        rgb = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)
        
        # Spatial: normalized
        spatial = (rgb.astype(np.float32) / 255.0 - MEAN_RGB) / STD_RGB
        spatial = np.transpose(spatial, (2, 0, 1))  # CHW
        spatial_list.append(spatial)
        
        # Frequency: 4-channel (RGB + DCT)
        freq_rgb = rgb.astype(np.float32) / 255.0
        dct_exp = np.expand_dims(dct_map, axis=2)
        freq_4ch = np.concatenate([freq_rgb, dct_exp], axis=2)
        freq_4ch = np.transpose(freq_4ch, (2, 0, 1))  # CHW
        freq_list.append(freq_4ch)
    
    spatial_tensor = torch.tensor(np.array(spatial_list), dtype=torch.float32)
    freq_tensor = torch.tensor(np.array(freq_list), dtype=torch.float32)
    rppg_tensor = torch.tensor(chrom, dtype=torch.float32).unsqueeze(0)
    
    return {'spatial': spatial_tensor, 'freq': freq_tensor, 'rppg': rppg_tensor}


if __name__ == '__main__':
    print('=' * 60)
    print('PRE-COMPUTING TENSORS')
    print(f'Input:  {INPUT_ROOT}')
    print(f'Output: {OUTPUT_ROOT}')
    print('=' * 60)
    
    os.makedirs(OUTPUT_ROOT, exist_ok=True)
    
    categories_to_process = [
        'FF-original'
    ]
    
    total_done = 0
    total_fail = 0
    t_start = time.time()
    
    for cat in categories_to_process:
        cat_in = os.path.join(INPUT_ROOT, cat)
        cat_out = os.path.join(OUTPUT_ROOT, cat)
        os.makedirs(cat_out, exist_ok=True)
        
        videos = sorted([d for d in os.listdir(cat_in) 
                         if os.path.isdir(os.path.join(cat_in, d))])
        
        print(f'\n{cat}: {len(videos)} videos (Processing ALL)')
        cat_done = 0
        
        for i, vid in enumerate(videos):
            out_path = os.path.join(cat_out, f'{vid}.pt')
            
            # Skip if already done
            if os.path.exists(out_path):
                cat_done += 1
                total_done += 1
                continue
            
            folder = os.path.join(cat_in, vid)
            try:
                tensors = process_video_folder(folder)
                if tensors is not None:
                    torch.save(tensors, out_path)
                    cat_done += 1
                    total_done += 1
                else:
                    total_fail += 1
            except Exception as e:
                print(f'  ERROR: {vid} - {e}')
                total_fail += 1
            
            if (cat_done) % 50 == 0 and cat_done > 0:
                elapsed = time.time() - t_start
                rate = total_done / elapsed if elapsed > 0 else 0
                print(f'  Done: {cat_done} | Total: {total_done} | Rate: {rate:.1f} vid/s')
        
        print(f'  Finished {cat}: {cat_done}')
    
    elapsed = time.time() - t_start
    print(f'\n{"=" * 60}')
    print(f'DONE! Processed: {total_done} | Failed: {total_fail} | Time: {elapsed:.0f}s')
    print(f'Output: {os.path.abspath(OUTPUT_ROOT)}')
    print(f'{"=" * 60}')
