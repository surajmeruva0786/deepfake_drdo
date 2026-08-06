import os
import sys

# Limit resource usage in multi-processing to prevent paging/virtual memory exhaustion
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["VECLIB_MAXIMUM_THREADS"] = "1"
os.environ["NUMEXPR_NUM_THREADS"] = "1"

import argparse
import concurrent.futures
import numpy as np

# We import cv2 and tqdm inside main/worker to allow the script to be run/validated
# even before the pip install finishes, and to support clean imports in subprocesses.

def parse_args():
    parser = argparse.ArgumentParser(description="Preprocess Celeb-DF-v2 videos into 32 frames.")
    parser.add_argument("--input_dir", type=str, default="Celeb-DF-v2",
                        help="Path to Celeb-DF-v2 root directory.")
    parser.add_argument("--output_dir", type=str, default="Celeb-DF-v2-32frames",
                        help="Directory to save preprocessed frames.")
    parser.add_argument("--num_frames", type=int, default=32,
                        help="Number of frames to extract per video (default: 32).")
    parser.add_argument("--mode", type=str, choices=["frames", "faces"], default="frames",
                        help="Extraction mode: 'frames' for full frame, 'faces' for face crops.")
    parser.add_argument("--resize", type=str, default="256",
                        help="Output image size (width and height). Use 'none' to keep original size.")
    parser.add_argument("--workers", type=int, default=4,
                        help="Number of parallel worker processes.")
    parser.add_argument("--limit", type=int, default=None,
                        help="Limit the number of videos processed (useful for testing).")
    return parser.parse_args()

def process_single_video(task_info):
    import cv2
    cv2.setNumThreads(0)
    
    video_path, out_folder, mode, num_frames, resize_size = task_info
    
    try:
        # Create output folder
        os.makedirs(out_folder, exist_ok=True)
        
        # Check if already processed
        # If all expected frame files exist, we can skip processing to allow resuming
        expected_files = [os.path.join(out_folder, f"frame_{i:02d}.jpg") for i in range(num_frames)]
        if all(os.path.exists(f) for f in expected_files):
            return True, "Already processed"
            
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            return False, f"Error: Could not open video {video_path}"
            
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        # Fallback if frame count metadata is missing or incorrect
        if total_frames <= 0:
            # Scan frames sequentially to get total frames
            total_frames = 0
            while True:
                ret, _ = cap.read()
                if not ret:
                    break
                total_frames += 1
            # Reopen video
            cap.release()
            cap = cv2.VideoCapture(video_path)
            
        if total_frames <= 0:
            cap.release()
            return False, f"Error: Video {video_path} has 0 frames"
            
        # Determine which frame indices to extract
        if total_frames >= num_frames:
            target_indices = np.linspace(0, total_frames - 1, num_frames, dtype=int).tolist()
        else:
            target_indices = [int(i * total_frames / num_frames) for i in range(num_frames)]
            
        # Extract frames sequentially
        extracted_frames = []
        frame_idx = 0
        while len(extracted_frames) < len(target_indices):
            ret, frame = cap.read()
            if not ret:
                break
            # Save frame multiple times if index is repeated
            count_to_save = target_indices.count(frame_idx)
            for _ in range(count_to_save):
                extracted_frames.append(frame.copy())
            frame_idx += 1
            
        cap.release()
        
        if not extracted_frames:
            return False, f"Error: No frames decoded from {video_path}"
            
        # Pad if we couldn't decode enough frames
        while len(extracted_frames) < num_frames:
            extracted_frames.append(extracted_frames[-1].copy())
            
        # Crop or adjust size
        last_face_box = None
        face_cascade = None
        
        if mode == "faces":
            face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
            
        for idx, frame in enumerate(extracted_frames):
            h_img, w_img = frame.shape[:2]
            crop = frame
            
            if mode == "faces":
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))
                
                if len(faces) > 0:
                    # Select the largest face by area
                    x, y, w, h = max(faces, key=lambda rect: rect[2] * rect[3])
                    # Add margin around the face (30% padding)
                    margin_x = int(w * 0.3)
                    margin_y = int(h * 0.3)
                    x1 = max(0, x - margin_x)
                    y1 = max(0, y - margin_y)
                    x2 = min(w_img, x + w + margin_x)
                    y2 = min(h_img, y + h + margin_y)
                    crop = frame[y1:y2, x1:x2]
                    last_face_box = (x1, y1, x2, y2)
                elif last_face_box is not None:
                    # Use last known face position
                    x1, y1, x2, y2 = last_face_box
                    crop = frame[y1:y2, x1:x2]
                else:
                    # Fallback: center crop square
                    sz = min(h_img, w_img)
                    x1 = (w_img - sz) // 2
                    y1 = (h_img - sz) // 2
                    crop = frame[y1:y1+sz, x1:x1+sz]
                    
            # Resize if requested
            if resize_size is not None:
                crop = cv2.resize(crop, (resize_size, resize_size), interpolation=cv2.INTER_AREA)
                
            # Save frame
            out_file = os.path.join(out_folder, f"frame_{idx:02d}.jpg")
            cv2.imwrite(out_file, crop, [cv2.IMWRITE_JPEG_QUALITY, 95])
            
        return True, "Success"
        
    except Exception as e:
        return False, str(e)

def main():
    args = parse_args()
    
    # Try importing cv2 and tqdm to ensure they are installed
    try:
        import cv2
        cv2.setNumThreads(0)
        from tqdm import tqdm
    except ImportError:
        print("Required libraries missing. Installing opencv-python and tqdm...")
        import subprocess
        subprocess.check_call([sys.executable, "-m", "pip", "install", "opencv-python", "tqdm"])
        import cv2
        cv2.setNumThreads(0)
        from tqdm import tqdm

    # Resolve paths
    input_dir = os.path.abspath(args.input_dir)
    output_dir = os.path.abspath(args.output_dir)
    
    if not os.path.exists(input_dir):
        print(f"Error: Input directory '{input_dir}' does not exist.")
        sys.exit(1)
        
    print(f"Input Directory: {input_dir}")
    print(f"Output Directory: {output_dir}")
    print(f"Number of frames: {args.num_frames}")
    print(f"Mode: {args.mode}")
    
    resize_size = None
    if args.resize.lower() != "none":
        try:
            resize_size = int(args.resize)
            print(f"Resize target: {resize_size}x{resize_size}")
        except ValueError:
            print(f"Error: Invalid resize value '{args.resize}'. Must be integer or 'none'.")
            sys.exit(1)
    else:
        print("Resize target: Keeping original resolution")
        
    # Discover all video files recursively under Celeb-DF-v2 subdirectories
    subdirs = ["Celeb-real", "Celeb-synthesis", "YouTube-real"]
    video_tasks = []
    
    for subdir in subdirs:
        subdir_path = os.path.join(input_dir, subdir)
        if not os.path.exists(subdir_path):
            continue
            
        for root, _, files in os.walk(subdir_path):
            for file in files:
                if file.endswith(".mp4"):
                    video_path = os.path.join(root, file)
                    # Relative path within dataset root, without extension
                    rel_dir = os.path.relpath(video_path, input_dir)
                    rel_name_no_ext = os.path.splitext(rel_dir)[0]
                    # Target folder path
                    out_folder = os.path.join(output_dir, rel_name_no_ext)
                    video_tasks.append((video_path, out_folder, args.mode, args.num_frames, resize_size))
                    
    total_videos = len(video_tasks)
    print(f"Discovered {total_videos} videos in total.")
    
    if args.limit:
        video_tasks = video_tasks[:args.limit]
        print(f"Limiting execution to the first {len(video_tasks)} videos.")
        
    if not video_tasks:
        print("No videos found to process.")
        sys.exit(0)
        
    # Start multiprocessing pool
    print(f"Starting processing using {args.workers} workers...")
    
    success_count = 0
    failure_count = 0
    failures = []
    
    with concurrent.futures.ProcessPoolExecutor(max_workers=args.workers) as executor:
        # Submit tasks
        futures = {executor.submit(process_single_video, task): task for task in video_tasks}
        
        # Track progress with tqdm
        with tqdm(total=len(video_tasks), desc="Processing videos") as pbar:
            for future in concurrent.futures.as_completed(futures):
                task = futures[future]
                video_path = task[0]
                try:
                    success, msg = future.result()
                    if success:
                        success_count += 1
                    else:
                        failure_count += 1
                        failures.append((video_path, msg))
                except Exception as exc:
                    failure_count += 1
                    failures.append((video_path, str(exc)))
                pbar.update(1)
                
    print(f"\nPreprocessing Complete!")
    print(f"Successfully processed: {success_count}/{len(video_tasks)}")
    if failure_count > 0:
        print(f"Failed to process: {failure_count}/{len(video_tasks)}")
        print("\nFirst 10 Failures:")
        for v, m in failures[:10]:
            print(f"- {v}: {m}")
            
if __name__ == "__main__":
    main()
