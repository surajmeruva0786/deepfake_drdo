import cv2
import numpy as np

def compute_dct_map(image_bgr):
    """
    Computes the 2D DCT energy map of a BGR image.
    Returns:
        dct_energy (np.ndarray): 2D array of the same shape as the input image height/width,
                                 normalized to [0, 1].
    """
    gray = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY)
    gray_f = gray.astype(np.float32) / 255.0
    
    # Compute 2D Discrete Cosine Transform
    dct_coeff = cv2.dct(gray_f)
    
    # Calculate energy (log-scaled absolute magnitude)
    dct_energy = np.log1p(np.abs(dct_coeff))
    
    # Normalize to [0, 1] range
    dct_min = dct_energy.min()
    dct_max = dct_energy.max()
    if dct_max - dct_min > 1e-6:
        dct_energy = (dct_energy - dct_min) / (dct_max - dct_min)
    else:
        dct_energy = np.zeros_like(dct_energy)
        
    return dct_energy

def compute_chrom_signal(frames):
    """
    Computes the CHROM rPPG signal from a list of frames.
    
    Args:
        frames (list of np.ndarray): List of BGR frames (T, H, W, 3).
        
    Returns:
        chrom_signal (np.ndarray): CHROM signal of shape (T,) normalized to zero mean, unit variance.
    """
    # Calculate RGB spatial means for each frame
    rgb_means = []
    for frame in frames:
        b_mean = np.mean(frame[:, :, 0])
        g_mean = np.mean(frame[:, :, 1])
        r_mean = np.mean(frame[:, :, 2])
        rgb_means.append([r_mean, g_mean, b_mean])
        
    rgb_means = np.array(rgb_means)  # Shape (T, 3)
    
    # Avoid division by zero
    eps = 1e-8
    mu_R = np.mean(rgb_means[:, 0]) + eps
    mu_G = np.mean(rgb_means[:, 1]) + eps
    mu_B = np.mean(rgb_means[:, 2]) + eps
    
    Rn = rgb_means[:, 0] / mu_R - 1.0
    Gn = rgb_means[:, 1] / mu_G - 1.0
    Bn = rgb_means[:, 2] / mu_B - 1.0
    
    # Orthogonal chrominance projection signals
    X = 3 * Rn - 2 * Gn
    Y = 1.5 * Rn + Gn - 1.5 * Bn
    
    # CHROM signal: S = X - (std_X / std_Y) * Y
    std_X = np.std(X)
    std_Y = np.std(Y)
    
    if std_Y > 1e-6:
        S = X - (std_X / std_Y) * Y
    else:
        S = X
        
    # Normalize CHROM signal to zero mean and unit variance
    std_S = np.std(S)
    if std_S > 1e-6:
        S = (S - np.mean(S)) / std_S
    else:
        S = S - np.mean(S)
        
    return S
