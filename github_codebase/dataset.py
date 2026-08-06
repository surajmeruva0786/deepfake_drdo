import os
import random
import cv2
import torch
from torch.utils.data import Dataset
import numpy as np
from utils import compute_dct_map, compute_chrom_signal


def get_combined_dataset_splits(root_dir, val_ratio=0.15, test_ratio=0.15, seed=42):
    """
    Creates balanced train/val/test splits from the Combined-32frames dataset.
    
    Strategy:
      - Gather ALL real folders and ALL fake folders
      - Downsample the larger class to match the smaller class (balance)
      - Split the balanced set into train/val/test
      - Each split is independently balanced (equal real and fake)
    
    Args:
        root_dir: Path to Combined-32frames/
        val_ratio: Fraction for validation
        test_ratio: Fraction for test
        seed: Random seed
        
    Returns:
        train_list, val_list, test_list: Lists of (relative_folder_path, label)
        Label: 1 = real, 0 = fake
    """
    random.seed(seed)
    np.random.seed(seed)
    
    # Define which categories are real and which are fake
    REAL_CATEGORIES = ["CelebDF-real", "YouTube-real", "FF-original"]
    FAKE_CATEGORIES = [
        "CelebDF-synthesis", "FF-Deepfakes", "FF-Face2Face",
        "FF-FaceSwap", "FF-NeuralTextures", "FF-FaceShifter",
        "FF-DeepFakeDetection"
    ]
    
    # Gather all real and fake folder paths
    real_dirs = []
    fake_dirs = []
    
    for cat in REAL_CATEGORIES:
        cat_path = os.path.join(root_dir, cat)
        if os.path.exists(cat_path):
            dirs = [os.path.join(cat, d) for d in os.listdir(cat_path)
                    if os.path.isdir(os.path.join(cat_path, d))]
            real_dirs.extend(dirs)
            
    for cat in FAKE_CATEGORIES:
        cat_path = os.path.join(root_dir, cat)
        if os.path.exists(cat_path):
            dirs = [os.path.join(cat, d) for d in os.listdir(cat_path)
                    if os.path.isdir(os.path.join(cat_path, d))]
            fake_dirs.extend(dirs)
    
    print(f"  Raw counts — Real: {len(real_dirs)}, Fake: {len(fake_dirs)}")
    
    # Shuffle before balancing
    random.shuffle(real_dirs)
    random.shuffle(fake_dirs)
    
    # Balance: downsample the larger class
    min_count = min(len(real_dirs), len(fake_dirs))
    real_dirs = real_dirs[:min_count]
    fake_dirs = fake_dirs[:min_count]
    
    print(f"  Balanced  — Real: {len(real_dirs)}, Fake: {len(fake_dirs)}")
    
    # Split each class independently to maintain balance in each split
    n_val = int(min_count * val_ratio)
    n_test = int(min_count * test_ratio)
    n_train = min_count - n_val - n_test
    
    train_real = real_dirs[:n_train]
    val_real = real_dirs[n_train:n_train + n_val]
    test_real = real_dirs[n_train + n_val:]
    
    train_fake = fake_dirs[:n_train]
    val_fake = fake_dirs[n_train:n_train + n_val]
    test_fake = fake_dirs[n_train + n_val:]
    
    # Build labeled lists
    train_list = [(d, 1) for d in train_real] + [(d, 0) for d in train_fake]
    val_list = [(d, 1) for d in val_real] + [(d, 0) for d in val_fake]
    test_list = [(d, 1) for d in test_real] + [(d, 0) for d in test_fake]
    
    # Shuffle each split
    random.shuffle(train_list)
    random.shuffle(val_list)
    random.shuffle(test_list)
    
    return train_list, val_list, test_list


def get_dataset_splits(root_dir, val_ratio=0.2, seed=42):
    """
    Original Celeb-DF-v2 only splits (kept for backward compatibility).
    
    Train/Val set: 590 Celeb-real + 590 random Celeb-synthesis videos.
    Test set: 300 YouTube-real + 300 random Celeb-synthesis videos (no overlap with train/val).
    
    Returns:
        train_list, val_list, test_list (list of tuples: (relative_folder_path, label))
    """
    random.seed(seed)
    np.random.seed(seed)
    
    # 1. Gather all directories under Celeb-real, YouTube-real, Celeb-synthesis
    real_celeb_dirs = []
    real_yt_dirs = []
    synth_dirs = []
    
    # Celeb-real
    celeb_real_path = os.path.join(root_dir, "Celeb-real")
    if os.path.exists(celeb_real_path):
        real_celeb_dirs = [os.path.join("Celeb-real", d) for d in os.listdir(celeb_real_path) 
                           if os.path.isdir(os.path.join(celeb_real_path, d))]
                           
    # YouTube-real
    yt_real_path = os.path.join(root_dir, "YouTube-real")
    if os.path.exists(yt_real_path):
        real_yt_dirs = [os.path.join("YouTube-real", d) for d in os.listdir(yt_real_path) 
                        if os.path.isdir(os.path.join(yt_real_path, d))]
                        
    # Celeb-synthesis
    synth_path = os.path.join(root_dir, "Celeb-synthesis")
    if os.path.exists(synth_path):
        synth_dirs = [os.path.join("Celeb-synthesis", d) for d in os.listdir(synth_path) 
                      if os.path.isdir(os.path.join(synth_path, d))]
                      
    # Ensure sizes are correct
    # real_celeb_dirs: 590, real_yt_dirs: 300, synth_dirs: 5639
    
    # Sample 590 synthesis videos for train/val
    random.shuffle(synth_dirs)
    train_val_synth = synth_dirs[:590]
    remaining_synth = synth_dirs[590:]
    
    # Sample 300 synthesis videos for testing
    test_synth = remaining_synth[:300]
    
    # 2. Build splits
    # Train / Val split (80% / 20%) of 590 real + 590 synth
    random.shuffle(real_celeb_dirs)
    random.shuffle(train_val_synth)
    
    num_val_real = int(len(real_celeb_dirs) * val_ratio)
    num_val_synth = int(len(train_val_synth) * val_ratio)
    
    val_real = real_celeb_dirs[:num_val_real]
    train_real = real_celeb_dirs[num_val_real:]
    
    val_synth = train_val_synth[:num_val_synth]
    train_synth = train_val_synth[num_val_synth:]
    
    # Build list of tuples: (relative_path, label) where 1 is real, 0 is fake
    train_list = [(d, 1) for d in train_real] + [(d, 0) for d in train_synth]
    val_list = [(d, 1) for d in val_real] + [(d, 0) for d in val_synth]
    
    # Test Split: 300 YouTube-real + 300 test_synth
    # Limit YT real to 300 just in case there are more, and synth to 300
    test_list = [(d, 1) for d in real_yt_dirs[:300]] + [(d, 0) for d in test_synth[:300]]
    
    # Shuffle splits
    random.shuffle(train_list)
    random.shuffle(val_list)
    random.shuffle(test_list)
    
    return train_list, val_list, test_list


def get_precomputed_dataset_splits(tensor_root_dir, val_ratio=0.15, test_ratio=0.15, seed=42):
    """
    Scans the precomputed tensor directory and builds balanced splits of all available .pt files.
    Real labels (1) are assigned to 'CelebDF-real', 'FF-original', 'YouTube-real'.
    Fake labels (0) are assigned to everything else.
    """
    random.seed(seed)
    
    real_vids = []
    fake_vids = []
    
    for cat in os.listdir(tensor_root_dir):
        cat_path = os.path.join(tensor_root_dir, cat)
        if not os.path.isdir(cat_path): continue
        
        is_real = (cat in ['CelebDF-real', 'FF-original', 'YouTube-real'])
        
        for f in os.listdir(cat_path):
            if f.endswith('.pt'):
                vid_name = f[:-3] # remove .pt
                rel_path = f"{cat}/{vid_name}"
                if is_real:
                    real_vids.append(rel_path)
                else:
                    fake_vids.append(rel_path)
                    
    # Balance the dataset (take min of real or fake)
    min_count = min(len(real_vids), len(fake_vids))
    random.shuffle(real_vids)
    random.shuffle(fake_vids)
    
    real_vids = real_vids[:min_count]
    fake_vids = fake_vids[:min_count]
    
    print(f"Precomputed Dataset: {min_count} Real, {min_count} Fake tensors available.")
    
    train_real = real_vids[int(min_count * (val_ratio + test_ratio)):]
    val_real = real_vids[:int(min_count * val_ratio)]
    test_real = real_vids[int(min_count * val_ratio):int(min_count * (val_ratio + test_ratio))]
    
    train_fake = fake_vids[int(min_count * (val_ratio + test_ratio)):]
    val_fake = fake_vids[:int(min_count * val_ratio)]
    test_fake = fake_vids[int(min_count * val_ratio):int(min_count * (val_ratio + test_ratio))]
    
    train_list = [(d, 1) for d in train_real] + [(d, 0) for d in train_fake]
    val_list = [(d, 1) for d in val_real] + [(d, 0) for d in val_fake]
    test_list = [(d, 1) for d in test_real] + [(d, 0) for d in test_fake]
    
    random.shuffle(train_list)
    random.shuffle(val_list)
    random.shuffle(test_list)
    
    return train_list, val_list, test_list



class PGCFDataset(Dataset):
    def __init__(self, root_dir, video_list, num_frames=16, resize=224, augment=False):
        """
        Args:
            root_dir (str): Path to dataset root folder.
            video_list (list): List of tuples (relative_path, label).
            num_frames (int): Number of frames to sample (T). Default is 16.
            resize (int): Spatial dimensions (H, W). Default is 224.
            augment (bool): If True, apply training augmentations.
        """
        self.root_dir = root_dir
        self.video_list = video_list
        self.num_frames = num_frames
        self.resize = resize
        self.augment = augment
        
        # ImageNet normalization parameters
        self.mean_rgb = np.array([0.485, 0.456, 0.406], dtype=np.float32)
        self.std_rgb = np.array([0.229, 0.224, 0.225], dtype=np.float32)
        
    def __len__(self):
        return len(self.video_list)
        
    def __getitem__(self, idx):
        rel_path, label = self.video_list[idx]
        folder_path = os.path.join(self.root_dir, rel_path)
        
        # Discover all available frame files (expected to have 32)
        all_frames = sorted([f for f in os.listdir(folder_path) if f.endswith(".jpg")])
        total_avail = len(all_frames)
        
        if total_avail == 0:
            raise FileNotFoundError(f"No frame files found in {folder_path}")
            
        # Sample T=num_frames evenly spaced indices
        target_indices = np.linspace(0, total_avail - 1, self.num_frames, dtype=int).tolist()
        sampled_frame_files = [all_frames[i] for i in target_indices]
        
        frames_bgr = []
        for file in sampled_frame_files:
            file_path = os.path.join(folder_path, file)
            img = cv2.imread(file_path)
            if img is None:
                # If reading failed, generate a blank placeholder frame
                img = np.zeros((256, 256, 3), dtype=np.uint8)
            frames_bgr.append(img)
            
        # 1. Compute CHROM rPPG signal (needs original BGR frames)
        chrom_signal = compute_chrom_signal(frames_bgr)  # Shape (T,)
        
        # 2. Decide augmentation parameters ONCE for all frames (consistency)
        do_flip = self.augment and random.random() > 0.5
        do_bright = self.augment and random.random() > 0.5
        bright_factor = random.uniform(0.8, 1.2) if do_bright else 1.0
        do_blur = self.augment and random.random() > 0.5
        blur_ksize = random.choice([3, 5]) if do_blur else 0
        do_rotate = False  # Disabled: too slow (warpAffine per frame)
        rot_angle = 0
        do_jpeg = False  # Disabled: too slow (encode+decode per frame)
        jpeg_quality = 95
        do_cutout = self.augment and random.random() > 0.5
        cut_x = random.randint(0, 180) if do_cutout else 0
        cut_y = random.randint(0, 180) if do_cutout else 0
        cut_s = random.randint(20, 44) if do_cutout else 0
        
        # 3. Process frames for Spatial and Frequency streams
        spatial_list = []
        freq_list = []
        
        for frame in frames_bgr:
            # Resize image to target height and width
            frame_resized = cv2.resize(frame, (self.resize, self.resize), interpolation=cv2.INTER_AREA)
            
            # Apply consistent augmentations
            if do_rotate:
                center = (self.resize // 2, self.resize // 2)
                M = cv2.getRotationMatrix2D(center, rot_angle, 1.0)
                frame_resized = cv2.warpAffine(frame_resized, M, (self.resize, self.resize))
            
            if do_flip:
                frame_resized = cv2.flip(frame_resized, 1)
            
            if do_bright:
                frame_resized = np.clip(frame_resized * bright_factor, 0, 255).astype(np.uint8)
            
            if do_blur:
                frame_resized = cv2.GaussianBlur(frame_resized, (blur_ksize, blur_ksize), 0)
            
            if do_jpeg:
                _, enc = cv2.imencode('.jpg', frame_resized, [cv2.IMWRITE_JPEG_QUALITY, jpeg_quality])
                frame_resized = cv2.imdecode(enc, cv2.IMREAD_COLOR)
            
            if do_cutout:
                frame_resized[cut_y:cut_y+cut_s, cut_x:cut_x+cut_s, :] = 128
            
            # Calculate DCT energy map
            dct_map = compute_dct_map(frame_resized)  # Shape (H, W), values in [0, 1]
            
            # Convert BGR to RGB for spatial stream
            frame_rgb = cv2.cvtColor(frame_resized, cv2.COLOR_BGR2RGB)
            
            # Normalize Spatial RGB (values in [0, 1] then normalized)
            spatial_norm = (frame_rgb.astype(np.float32) / 255.0 - self.mean_rgb) / self.std_rgb
            # HWC -> CHW
            spatial_norm = np.transpose(spatial_norm, (2, 0, 1))
            spatial_list.append(spatial_norm)
            
            # Frequency Stream Input: 4-channels (RGB + DCT energy map)
            # Normalize RGB for frequency stream similarly
            freq_norm_rgb = frame_rgb.astype(np.float32) / 255.0
            dct_expanded = np.expand_dims(dct_map, axis=2)  # Shape (H, W, 1)
            freq_4ch = np.concatenate([freq_norm_rgb, dct_expanded], axis=2) # Shape (H, W, 4)
            # HWC -> CHW
            freq_4ch = np.transpose(freq_4ch, (2, 0, 1))
            freq_list.append(freq_4ch)
            
        # Convert lists to PyTorch tensors
        spatial_tensor = torch.tensor(np.array(spatial_list), dtype=torch.float32)  # (T, 3, H, W)
        freq_tensor = torch.tensor(np.array(freq_list), dtype=torch.float32)        # (T, 4, H, W)
        rppg_tensor = torch.tensor(chrom_signal, dtype=torch.float32).unsqueeze(0) # (1, T)
        
        return spatial_tensor, freq_tensor, rppg_tensor, torch.tensor(label, dtype=torch.long)


class PrecomputedTensorDataset(Dataset):
    def __init__(self, root_dir, video_list, augment=False):
        """
        Loads pre-computed tensors from .pt files to skip cv2 and numpy operations.
        
        Args:
            root_dir (str): Path to dataset tensor root folder (e.g., Combined-32frames-tensors)
            video_list (list): List of tuples (relative_path, label). 
                               Example: ('CelebDF-real/video1', 1) -> loads 'CelebDF-real/video1.pt'
            augment (bool): Whether to apply spatial augmentations (like flip, cutout) 
                            on the loaded tensors directly.
        """
        self.root_dir = root_dir
        self.video_list = video_list
        self.augment = augment
        
    def __len__(self):
        return len(self.video_list)
        
    def __getitem__(self, idx):
        rel_path, label = self.video_list[idx]
        pt_path = os.path.join(self.root_dir, f"{rel_path}.pt")
        
        if not os.path.exists(pt_path):
            raise FileNotFoundError(f"Precomputed tensor not found: {pt_path}")
            
        # Load the dictionary containing {'spatial', 'freq', 'rppg'}
        tensors = torch.load(pt_path, map_location='cpu', weights_only=True)
        spatial_tensor = tensors['spatial']
        freq_tensor = tensors['freq']
        rppg_tensor = tensors['rppg']
        
        if self.augment:
            # Apply light tensor-based augmentations
            do_flip = random.random() > 0.5
            do_cutout = random.random() > 0.5
            
            if do_flip:
                # Flip width dimension (index 3 for shape T,C,H,W)
                spatial_tensor = torch.flip(spatial_tensor, dims=[3])
                freq_tensor = torch.flip(freq_tensor, dims=[3])
                
            if do_cutout:
                _, _, H, W = spatial_tensor.shape
                cut_s = random.randint(20, 44)
                cut_x = random.randint(0, W - cut_s)
                cut_y = random.randint(0, H - cut_s)
                
                # Apply gray patch (0 for normalized tensor)
                spatial_tensor[:, :, cut_y:cut_y+cut_s, cut_x:cut_x+cut_s] = 0.0
                freq_tensor[:, :3, cut_y:cut_y+cut_s, cut_x:cut_x+cut_s] = 0.0
                
        return spatial_tensor, freq_tensor, rppg_tensor, torch.tensor(label, dtype=torch.long)
