# Plan to Achieve 0.95 AUC — PGCF Deepfake Detection

## Current Status
- **Model:** PGCF (3-stream: Spatial + Frequency + rPPG)
- **Current AUC:** ~0.70-0.80 (estimated from training logs)
- **Target AUC:** 0.95
- **Constraint:** Architecture cannot be changed

---

## Change 1: Two-Phase Training Strategy (Freeze → Unfreeze)

**File:** `training.ipynb`

**Problem:** All layers train simultaneously. The randomly initialized layers (frequency CNN, rPPG CNN, fusion modules) produce garbage gradients that corrupt the pretrained ResNet50 backbone early on.

**Fix:**
- **Phase 1 (8 epochs):** Freeze `spatial_backbone` entirely. Train only new layers with `lr=1e-3`. This lets the fusion/temporal modules learn meaningful features first.
- **Phase 2 (12 epochs):** Unfreeze everything. Use `lr=1e-5` for backbone, `lr=5e-4` for rest. Fine-tune the whole model together.

**Expected impact:** +5-8% accuracy

---

## Change 2: Learning Rate Scheduler

**File:** `training.ipynb`

**Problem:** Constant learning rate overshoots good minima and causes oscillation in later epochs.

**Fix:** Add `CosineAnnealingWarmRestarts` scheduler:
```python
scheduler = torch.optim.lr_scheduler.CosineAnnealingWarmRestarts(optimizer, T_0=5, T_mult=2)
```
Call `scheduler.step()` after each epoch.

**Expected impact:** +2-3% accuracy, smoother convergence

---

## Change 3: Heavier Data Augmentation

**File:** `dataset.py` (inside `__getitem__`)

**Problem:** Current augmentation is only random flip + brightness. The model memorizes training faces instead of learning forgery artifacts.

**Fix — add these augmentations during training:**
```python
# Random rotation (±15 degrees)
if random.random() > 0.5:
    angle = random.uniform(-15, 15)
    M = cv2.getRotationMatrix2D((112, 112), angle, 1.0)
    frame_resized = cv2.warpAffine(frame_resized, M, (224, 224))

# Random Gaussian blur
if random.random() > 0.5:
    ksize = random.choice([3, 5])
    frame_resized = cv2.GaussianBlur(frame_resized, (ksize, ksize), 0)

# Random JPEG compression (simulates real-world quality loss)
if random.random() > 0.5:
    quality = random.randint(30, 95)
    _, enc = cv2.imencode('.jpg', frame_resized, [cv2.IMWRITE_JPEG_QUALITY, quality])
    frame_resized = cv2.imdecode(enc, cv2.IMREAD_COLOR)

# Color jitter (saturation + contrast)
if random.random() > 0.5:
    hsv = cv2.cvtColor(frame_resized, cv2.COLOR_BGR2HSV).astype(np.float32)
    hsv[:, :, 1] *= random.uniform(0.7, 1.3)  # saturation
    hsv = np.clip(hsv, 0, 255).astype(np.uint8)
    frame_resized = cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)

# Random erasing (cutout) — applied on tensor after normalization
if random.random() > 0.5:
    x, y = random.randint(0, 180), random.randint(0, 180)
    s = random.randint(20, 44)
    frame_resized[y:y+s, x:x+s, :] = 128  # gray patch
```

**IMPORTANT:** Apply the SAME augmentation to ALL frames in the same video clip (spatial consistency).

**Expected impact:** +3-5% accuracy, much better generalization

---

## Change 4: Loss Schedule (Warm-up Auxiliary Losses)

**File:** `training.ipynb`

**Problem:** The consistency and rPPG losses add noise early in training when those streams haven't learned anything yet.

**Fix:** Gradually ramp up alpha and beta:
```python
# At start of each epoch:
warmup_epochs = 5
if epoch <= warmup_epochs:
    current_alpha = 0.3 * (epoch / warmup_epochs)  # 0.0 → 0.3
    current_beta  = 0.1 * (epoch / warmup_epochs)   # 0.0 → 0.1
else:
    current_alpha = 0.3
    current_beta  = 0.1

loss_fn.alpha = current_alpha
loss_fn.beta = current_beta
```

**Expected impact:** +2-3% accuracy in early convergence

---

## Change 5: Label Smoothing

**File:** `training.ipynb` (for baseline models) and `loss.py` (for PGCF)

**Problem:** Hard labels (0 or 1) cause overconfident predictions. The model becomes brittle.

**Fix:**
```python
# For baselines:
criterion = nn.CrossEntropyLoss(label_smoothing=0.1)

# For PGCF in loss.py:
self.cls_criterion = nn.CrossEntropyLoss(label_smoothing=0.1)
```

**Expected impact:** +1-2% AUC (smoother probability outputs)

---

## Change 6: More Training Epochs + Early Stopping

**File:** `training.ipynb`

**Problem:** 5 epochs is far too few. The model hasn't converged.

**Fix:**
- **Phase 1:** 8 epochs (frozen backbone)
- **Phase 2:** 12 epochs (all unfrozen)
- **Total:** 20 epochs
- **Early stopping:** patience=5 (stop if val AUC doesn't improve for 5 epochs)

```python
patience = 5
no_improve_count = 0

# After each epoch:
if val_acc > best_val_acc:
    best_val_acc = val_acc
    no_improve_count = 0
    save_model(...)
else:
    no_improve_count += 1
    if no_improve_count >= patience:
        print("Early stopping!")
        break
```

**Expected impact:** Ensures full convergence without wasting time

---

## Change 7: Gradient Clipping

**File:** `training.ipynb`

**Problem:** Multi-task loss (CLS + Consistency + rPPG) can cause gradient spikes, destabilizing training.

**Fix:** Add gradient clipping before optimizer step:
```python
scaler.unscale_(optimizer)
torch.nn.utils.clip_grad_norm_(model_pgcf.parameters(), max_norm=1.0)
scaler.step(optimizer)
```

**Expected impact:** Prevents training instability, smoother loss curves

---

## Change 8: Test-Time Augmentation (TTA)

**File:** `training.ipynb` (evaluation cells)

**Problem:** Single-pass evaluation is noisy. Some borderline videos get misclassified.

**Fix:** During evaluation, run each video twice (original + horizontally flipped), average the predictions:
```python
# Original prediction
logits1 = model(spatial, freq, rppg)

# Flipped prediction
spatial_flip = torch.flip(spatial, dims=[-1])  # horizontal flip
freq_flip = torch.flip(freq, dims=[-1])
logits2 = model(spatial_flip, freq_flip, rppg)

# Average
final_logits = (logits1 + logits2) / 2
```

**Expected impact:** +1-2% AUC for free (no retraining needed)

---

## Change 9: Weighted Loss for Consistency

**File:** `loss.py`

**Problem:** Consistency loss treats all samples equally. But hard examples (well-made deepfakes) need more attention.

**Fix:** Add focal-style weighting:
```python
# Replace line 32 in loss.py:
# Old:
loss_consist = torch.mean(labels_float * (1 - s) + (1 - labels_float) * s)

# New — focal weighting:
raw = labels_float * (1 - s) + (1 - labels_float) * s
weights = (raw ** 2)  # harder samples get more weight
loss_consist = torch.mean(weights * raw)
```

**Expected impact:** +1-2% on hard cases

---

## Summary: Expected Cumulative Impact

| Change | Expected AUC Improvement |
|--------|--------------------------|
| 1. Freeze → Unfreeze training | +5-8% |
| 2. LR Scheduler | +2-3% |
| 3. Heavy augmentation | +3-5% |
| 4. Loss warmup schedule | +2-3% |
| 5. Label smoothing | +1-2% |
| 6. 20 epochs + early stopping | convergence |
| 7. Gradient clipping | stability |
| 8. Test-time augmentation | +1-2% |
| 9. Focal consistency loss | +1-2% |
| **Total estimated** | **+15-25% → Target: 0.93-0.97 AUC** |

> Note: These gains are not perfectly additive. Realistic expectation with all changes combined: **0.90-0.95 AUC**.

---

## Files to Modify

| File | Changes |
|------|---------|
| `dataset.py` | Add augmentation (rotation, blur, JPEG, color jitter, cutout) |
| `loss.py` | Add label smoothing + focal consistency weighting |
| `training.ipynb` | Freeze/unfreeze, LR scheduler, loss warmup, gradient clipping, early stopping, 20 epochs, TTA evaluation |

---

## Execution Order
1. Update `dataset.py` with augmentations
2. Update `loss.py` with label smoothing + focal weighting
3. Regenerate `training.ipynb` with all training improvements
4. Restart kernel → Run all cells
5. Total training time estimate: ~3-4 hours on RTX 4050
