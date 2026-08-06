import torch
import torch.nn as nn

class PGCFLoss(nn.Module):
    def __init__(self, alpha=0.3, beta=0.1):
        super().__init__()
        self.alpha = alpha
        self.beta = beta
        self.cls_criterion = nn.CrossEntropyLoss()
        self.rppg_criterion = nn.MSELoss()
        
    def forward(self, logits, labels, consistency_scores, rppg_reconstructed, rppg_ground_truth):
        """
        Computes multi-task PGCF loss: L = L_cls + alpha * L_consist + beta * L_rppg
        
        Args:
            logits (torch.Tensor): Classification logits of shape (B, 2)
            labels (torch.Tensor): Ground truth labels of shape (B,)
            consistency_scores (torch.Tensor): PGCMC consistency scores s of shape (B,)
            rppg_reconstructed (torch.Tensor): Reconstructed CHROM signal of shape (B, 1, T)
            rppg_ground_truth (torch.Tensor): Ground truth CHROM signal of shape (B, 1, T)
            
        Returns:
            total_loss (torch.Tensor): The combined loss scalar.
            loss_components (dict): Dictionary containing separate losses for logging/plotting.
        """
        # 1. Classification Loss (Cross Entropy)
        loss_cls = self.cls_criterion(logits, labels)
        
        # 2. Consistency Loss: Penalizes low consistency for real, high consistency for fake
        labels_float = labels.float()
        loss_consist = torch.mean(labels_float * (1.0 - consistency_scores) + (1.0 - labels_float) * consistency_scores)
        
        # 3. rPPG Reconstruction Loss (MSE)
        loss_rppg = self.rppg_criterion(rppg_reconstructed, rppg_ground_truth)
        
        # Total Loss
        total_loss = loss_cls + self.alpha * loss_consist + self.beta * loss_rppg
        
        loss_components = {
            "loss_total": total_loss.item(),
            "loss_cls": loss_cls.item(),
            "loss_consist": loss_consist.item(),
            "loss_rppg": loss_rppg.item()
        }
        
        return total_loss, loss_components
