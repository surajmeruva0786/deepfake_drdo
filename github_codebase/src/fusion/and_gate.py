import numpy as np

def fuse_predictions(p_video, p_audio, mode="hard"):
    """
    Fuses video and audio predictions.
    Args:
        p_video: np.array of probabilities for FAKE class from PGCF
        p_audio: np.array of probabilities for FAKE class from AGCF
        mode: "hard" (AND gate) or "soft" (product t-norm)
    Returns:
        p_final: fused probability
        y_final: fused discrete prediction (1=FAKE, 0=REAL)
    """
    if mode == "hard":
        # Hard AND gate: FAKE if both > 0.5, else REAL
        pred_video = (p_video > 0.5).astype(int)
        pred_audio = (p_audio > 0.5).astype(int)
        y_final = pred_video & pred_audio
        # for AUC, we can just use the product of probabilities as a proxy
        p_final = p_video * p_audio
    elif mode == "soft":
        # Soft product t-norm
        p_final = p_video * p_audio
        y_final = (p_final > 0.25).astype(int) # threshold could be tuned, 0.5*0.5=0.25
    else:
        raise ValueError(f"Unknown mode: {mode}")
        
    return p_final, y_final
