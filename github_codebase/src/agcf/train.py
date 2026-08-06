import os
import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from src.agcf.dataset import AGCFDataset
from src.agcf.model import AGCF
from torch.cuda.amp import autocast, GradScaler
import numpy as np

def train_agcf(base_dir, epochs=20, batch_size=2, accum_steps=4, lr=1e-4, weight_decay=1e-4):
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    
    # max_real=500, max_fake=500 -> 400 train, 100 val per class
    train_dataset = AGCFDataset(base_dir, split="train", max_real=500, max_fake=500, val_ratio=0.2)
    val_dataset = AGCFDataset(base_dir, split="val", max_real=500, max_fake=500, val_ratio=0.2)
    
    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True, num_workers=2)
    val_loader = DataLoader(val_dataset, batch_size=batch_size, shuffle=False, num_workers=2)
    
    model = AGCF(num_frames=16).to(device)
    
    # Differential learning rate: backbone-equivalent vs new-module
    # In AGCF, everything is "new", but we can split by CNN vs Temporal
    # Or just use 1e-4 for feature extractors, 5e-4 for temporal.
    cnn_params = list(model.spectral_cnn.parameters()) + list(model.spectral_proj.parameters()) + \
                 list(model.vocal_cnn.parameters()) + list(model.vocal_proj_1.parameters()) + \
                 list(model.vocal_proj_2.parameters())
    
    temp_params = list(model.tgf_proj.parameters()) + list(model.transformer.parameters()) + \
                  list(model.bilstm.parameters()) + list(model.classifier.parameters())
                  
    optimizer = torch.optim.AdamW([
        {'params': cnn_params, 'lr': lr},
        {'params': temp_params, 'lr': 5e-4}
    ], weight_decay=weight_decay)
    
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=epochs, eta_min=1e-6)
    criterion = nn.CrossEntropyLoss()
    scaler = GradScaler()
    
    os.makedirs("saved_models", exist_ok=True)
    best_val_acc = 0.0
    
    print(f"Starting training on {device} with VRAM headroom for larger batch size if needed.")
    
    for epoch in range(epochs):
        model.train()
        train_loss = 0.0
        correct = 0
        total = 0
        
        optimizer.zero_grad()
        
        for i, (spectral, vocal, labels, paths) in enumerate(train_loader):
            spectral, vocal, labels = spectral.to(device), vocal.to(device), labels.to(device)
            
            with autocast():
                logits = model(spectral, vocal)
                loss = criterion(logits, labels)
                loss = loss / accum_steps
                
            scaler.scale(loss).backward()
            
            if (i + 1) % accum_steps == 0 or (i + 1) == len(train_loader):
                scaler.step(optimizer)
                scaler.update()
                optimizer.zero_grad()
                
            train_loss += loss.item() * accum_steps
            _, predicted = torch.max(logits.data, 1)
            total += labels.size(0)
            correct += (predicted == labels).sum().item()
            
        scheduler.step()
        train_acc = 100 * correct / total
        
        # Validation
        model.eval()
        val_loss = 0.0
        val_correct = 0
        val_total = 0
        
        with torch.no_grad():
            for spectral, vocal, labels, paths in val_loader:
                spectral, vocal, labels = spectral.to(device), vocal.to(device), labels.to(device)
                with autocast():
                    logits = model(spectral, vocal)
                    loss = criterion(logits, labels)
                
                val_loss += loss.item()
                _, predicted = torch.max(logits.data, 1)
                val_total += labels.size(0)
                val_correct += (predicted == labels).sum().item()
                
        val_acc = 100 * val_correct / val_total
        
        print(f"Epoch [{epoch+1}/{epochs}] "
              f"Train Loss: {train_loss/len(train_loader):.4f}, Train Acc: {train_acc:.2f}% | "
              f"Val Loss: {val_loss/len(val_loader):.4f}, Val Acc: {val_acc:.2f}%")
              
        if val_acc > best_val_acc:
            best_val_acc = val_acc
            torch.save(model.state_dict(), "saved_models/agcf_best.pth")
            print("  [*] Saved best model")

if __name__ == '__main__':
    base_dir = r"c:\deepfake\archive (1)\FakeAVCeleb_v1.2\FakeAVCeleb_v1.2"
    train_agcf(base_dir)
