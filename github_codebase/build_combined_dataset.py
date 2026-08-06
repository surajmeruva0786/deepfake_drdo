"""
Preprocess FaceForensics++ C23 videos into 32-frame folders,
then create a combined balanced dataset with Celeb-DF-v2.

Output structure:
  Combined-32frames/
    CelebDF-real/          (590 folders from Celeb-real)
    CelebDF-synthesis/     (5639 folders from Celeb-synthesis)
    YouTube-real/          (300 folders from YouTube-real)
    FF-original/           (1000 folders from FF++ original)
    FF-Deepfakes/          (1000 folders)
    FF-Face2Face/          (1000 folders)
    FF-FaceSwap/           (1000 folders)
    FF-NeuralTextures/     (1000 folders)
    FF-FaceShifter/        (1000 folders)
    FF-DeepFakeDetection/  (1000 folders)
"""

import os
import cv2
import shutil
import sys
from pathlib import Path

# Prevent OpenCV from spawning too many threads
cv2.setNumThreads(0)

# ============ CONFIGURATION ============
FF_ROOT = r"c:\deepfake\archive\FaceForensics++_C23"
CELEB_32FRAMES = r"c:\deepfake\Celeb-DF-v2-32frames"
OUTPUT_ROOT = r"c:\deepfake\Combined-32frames"
NUM_FRAMES = 32

# FF++ categories to process
FF_CATEGORIES = [
    ("original", "FF-original"),
    ("Deepfakes", "FF-Deepfakes"),
    ("Face2Face", "FF-Face2Face"),
    ("FaceSwap", "FF-FaceSwap"),
    ("NeuralTextures", "FF-NeuralTextures"),
    ("FaceShifter", "FF-FaceShifter"),
    ("DeepFakeDetection", "FF-DeepFakeDetection"),
]

# Celeb-DF categories to copy (already 32 frames)
CELEB_CATEGORIES = [
    ("Celeb-real", "CelebDF-real"),
    ("Celeb-synthesis", "CelebDF-synthesis"),
    ("YouTube-real", "YouTube-real"),
]


def extract_32_frames(video_path, output_folder):
    """Extract 32 evenly spaced frames from a video and save as JPGs."""
    os.makedirs(output_folder, exist_ok=True)
    
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"  WARNING: Cannot open {video_path}")
        return False
    
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    if total_frames < NUM_FRAMES:
        # If video has fewer frames, take all and duplicate last
        indices = list(range(total_frames))
        while len(indices) < NUM_FRAMES:
            indices.append(total_frames - 1)
    else:
        # Evenly spaced indices
        step = total_frames / NUM_FRAMES
        indices = [int(i * step) for i in range(NUM_FRAMES)]
    
    saved_count = 0
    for frame_idx, target_frame in enumerate(indices):
        cap.set(cv2.CAP_PROP_POS_FRAMES, target_frame)
        ret, frame = cap.read()
        if ret:
            out_path = os.path.join(output_folder, f"frame_{frame_idx:04d}.jpg")
            cv2.imwrite(out_path, frame, [cv2.IMWRITE_JPEG_QUALITY, 95])
            saved_count += 1
        else:
            # If read fails, duplicate previous frame or create blank
            if frame_idx > 0:
                prev_path = os.path.join(output_folder, f"frame_{frame_idx-1:04d}.jpg")
                out_path = os.path.join(output_folder, f"frame_{frame_idx:04d}.jpg")
                if os.path.exists(prev_path):
                    shutil.copy2(prev_path, out_path)
                    saved_count += 1
    
    cap.release()
    return saved_count == NUM_FRAMES


def process_ff_category(src_name, dst_name):
    """Process all videos in a FF++ category into 32-frame folders."""
    src_dir = os.path.join(FF_ROOT, src_name)
    dst_dir = os.path.join(OUTPUT_ROOT, dst_name)
    os.makedirs(dst_dir, exist_ok=True)
    
    videos = sorted([f for f in os.listdir(src_dir) if f.endswith('.mp4')])
    total = len(videos)
    
    print(f"\nProcessing FF++ {src_name} -> {dst_name} ({total} videos)")
    print("-" * 50)
    
    success = 0
    for i, video_file in enumerate(videos):
        video_name = Path(video_file).stem  # e.g., "000_003"
        video_path = os.path.join(src_dir, video_file)
        out_folder = os.path.join(dst_dir, video_name)
        
        # Skip if already processed
        if os.path.exists(out_folder) and len(os.listdir(out_folder)) >= NUM_FRAMES:
            success += 1
            if (i + 1) % 100 == 0:
                print(f"  [{i+1}/{total}] Skipped (exists): {video_name}")
            continue
        
        ok = extract_32_frames(video_path, out_folder)
        if ok:
            success += 1
        
        if (i + 1) % 100 == 0:
            print(f"  [{i+1}/{total}] Processed. Success so far: {success}")
    
    print(f"  Done: {success}/{total} videos successfully processed.")
    return success


def copy_celeb_category(src_name, dst_name):
    """Copy already-processed Celeb-DF-v2 32-frame folders to combined dataset."""
    src_dir = os.path.join(CELEB_32FRAMES, src_name)
    dst_dir = os.path.join(OUTPUT_ROOT, dst_name)
    
    if not os.path.exists(src_dir):
        print(f"  WARNING: {src_dir} does not exist!")
        return 0
    
    folders = [d for d in os.listdir(src_dir) if os.path.isdir(os.path.join(src_dir, d))]
    total = len(folders)
    
    print(f"\nCopying Celeb-DF {src_name} -> {dst_name} ({total} folders)")
    print("-" * 50)
    
    # Use symlinks on Windows (junction) to save disk space, fall back to copy
    os.makedirs(dst_dir, exist_ok=True)
    
    copied = 0
    for i, folder in enumerate(folders):
        src_path = os.path.join(src_dir, folder)
        dst_path = os.path.join(dst_dir, folder)
        
        if os.path.exists(dst_path):
            copied += 1
            continue
        
        try:
            # Use directory junction (no admin needed on Windows)
            os.symlink(os.path.abspath(src_path), dst_path, target_is_directory=True)
            copied += 1
        except (OSError, NotImplementedError):
            # Fall back to copying
            shutil.copytree(src_path, dst_path)
            copied += 1
        
        if (i + 1) % 200 == 0:
            print(f"  [{i+1}/{total}] Linked/copied.")
    
    print(f"  Done: {copied}/{total} folders.")
    return copied


if __name__ == "__main__":
    print("=" * 60)
    print("COMBINED DATASET BUILDER")
    print(f"Output: {OUTPUT_ROOT}")
    print("=" * 60)
    
    os.makedirs(OUTPUT_ROOT, exist_ok=True)
    
    # Step 1: Copy Celeb-DF-v2 (already preprocessed)
    print("\n>>> STEP 1: Link Celeb-DF-v2 32-frame folders")
    for src, dst in CELEB_CATEGORIES:
        copy_celeb_category(src, dst)
    
    # Step 2: Process FF++ videos into 32 frames
    print("\n>>> STEP 2: Extract 32 frames from FaceForensics++ C23 videos")
    for src, dst in FF_CATEGORIES:
        process_ff_category(src, dst)
    
    # Step 3: Print final summary
    print("\n" + "=" * 60)
    print("FINAL DATASET SUMMARY")
    print("=" * 60)
    
    total_real = 0
    total_fake = 0
    
    for category in os.listdir(OUTPUT_ROOT):
        cat_path = os.path.join(OUTPUT_ROOT, category)
        if os.path.isdir(cat_path):
            count = len([d for d in os.listdir(cat_path) if os.path.isdir(os.path.join(cat_path, d))])
            label = "REAL" if "real" in category.lower() or "original" in category.lower() else "FAKE"
            if label == "REAL":
                total_real += count
            else:
                total_fake += count
            print(f"  {category:<25} {count:>5} videos  [{label}]")
    
    print(f"\n  TOTAL REAL: {total_real}")
    print(f"  TOTAL FAKE: {total_fake}")
    print(f"  GRAND TOTAL: {total_real + total_fake}")
    print("=" * 60)
