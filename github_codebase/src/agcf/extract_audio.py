import os
import numpy as np
import glob
from moviepy import VideoFileClip

def extract_and_chunk_audio(video_path, out_npy_path, num_chunks=16):
    """
    Extracts audio from video using moviepy, resamples to 16kHz mono, 
    windows it into `num_chunks` temporal chunks, and caches to .npy
    """
    try:
        # Load video and extract audio
        clip = VideoFileClip(video_path)
        if clip.audio is None:
            # Silent video
            chunks = np.zeros((num_chunks, 16000), dtype=np.float32)
            np.save(out_npy_path, chunks)
            clip.close()
            return True
            
        # Extract raw audio array (returns (N, 2) or (N, 1) usually at 44100)
        # fps=16000 resamples it to 16kHz
        # nbytes=2 returns 16-bit integers, we want floats from -1.0 to 1.0
        sig = clip.audio.to_soundarray(fps=16000)
        clip.close()
        
        if len(sig) == 0:
            chunks = np.zeros((num_chunks, 16000), dtype=np.float32)
            np.save(out_npy_path, chunks)
            return True
            
        # Convert to mono if stereo
        if len(sig.shape) == 2:
            sig = sig.mean(axis=1)
            
        sig = sig.astype(np.float32)
        
        chunk_size = len(sig) // num_chunks
        if chunk_size == 0:
            # Audio too short
            padded_sig = np.zeros(num_chunks, dtype=np.float32)
            padded_sig[:len(sig)] = sig
            sig = padded_sig
            chunk_size = 1
            
        chunks = []
        for i in range(num_chunks):
            start = i * chunk_size
            end = start + chunk_size
            chunk = sig[start:end]
            chunks.append(chunk)
            
        chunks = np.array(chunks)
        np.save(out_npy_path, chunks)
        
    except Exception as e:
        print(f"Error processing {video_path}: {e}")
        return False
        
    return True

def process_dataset(base_dir, max_real=500, max_fake=500):
    real_dir = os.path.join(base_dir, "RealVideo-RealAudio")
    fake_dir = os.path.join(base_dir, "FakeVideo-FakeAudio")
    
    real_vids = glob.glob(os.path.join(real_dir, "**", "*.mp4"), recursive=True)
    fake_vids = glob.glob(os.path.join(fake_dir, "**", "*.mp4"), recursive=True)
    
    np.random.seed(42)
    np.random.shuffle(real_vids)
    np.random.shuffle(fake_vids)
    
    real_vids = real_vids[:max_real]
    fake_vids = fake_vids[:max_fake]
    
    print(f"Processing {len(real_vids)} real videos and {len(fake_vids)} fake videos.")
    
    success_count = 0
    for count, vid in enumerate(real_vids + fake_vids):
        out_path = vid.replace(".mp4", ".npy")
        if not os.path.exists(out_path):
            if extract_and_chunk_audio(vid, out_path, num_chunks=16):
                success_count += 1
        else:
            success_count += 1
            
        if (count + 1) % 100 == 0:
            print(f"Processed {count + 1} / {len(real_vids) + len(fake_vids)}")
            
    print(f"Successfully processed {success_count} / {len(real_vids) + len(fake_vids)}")

if __name__ == "__main__":
    # Adjust base_dir as needed
    base_dir = r"c:\deepfake\archive (1)\FakeAVCeleb_v1.2\FakeAVCeleb_v1.2"
    process_dataset(base_dir, max_real=500, max_fake=500)
