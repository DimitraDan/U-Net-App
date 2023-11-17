import numpy as np
import torch
import torch.nn.functional as F
from tqdm import tqdm

from base.iou_score import multiclass_dice_coeff, dice_coeff


@torch.inference_mode()
def evaluate(net, dataloader, device, amp):
    """
    Evaluate a neural network model on a validation dataset and collect analysis data.

    Parameters:
    - net: The neural network model to evaluate.
    - dataloader: The data loader for the validation dataset.
    - device: The device (e.g., CPU or GPU) to run inference on.
    - amp: A flag indicating whether to use automatic mixed precision for faster training (if supported).

    Returns:
    - images: A list of input images.
    - masks: A list of true masks.
    - pred_mask_images: A list of predicted masks as numpy arrays.
    - dice_scores: A list of Dice scores for each batch.
    - average_dice_score: The average Dice score across all batches.
    """

    net.eval()
    num_val_batches = len(dataloader)
    dice_scores = []
    images = []
    masks = []
    pred_mask_images = []

    with torch.autocast(device.type if device.type != 'mps' else 'cpu', enabled=amp):
        for batch_idx, batch in enumerate(
                tqdm(dataloader, total=num_val_batches, desc='Validation round', unit='batch', leave=False)):
            image, mask_true = batch['image'], batch['mask']
            image = image.to(device=device, dtype=torch.float32)
            images.append(image)  # Append the input image

            mask_true = mask_true.to(device=device, dtype=torch.long)
            masks.append(mask_true)  # Append the true mask

            mask_pred = net(image)

            if net.n_classes == 1:
                assert mask_true.min() >= 0 and mask_true.max() <= 1, 'True mask values should be in [0, 1]'
                mask_pred = (F.sigmoid(mask_pred) > 0.5).float()
                dice = dice_coeff(mask_pred, mask_true, reduce_batch_first=False)
                dice_scores.append(dice.item())  # Append the Dice score as a float
            else:
                assert mask_true.min() >= 0 and mask_true.max() < net.n_classes, 'True mask indices should be in [0, n_classes]'
                mask_true = F.one_hot(mask_true.to(torch.int64), net.n_classes).permute(0, 3, 1, 2).float()
                mask_pred = F.one_hot(mask_pred.argmax(dim=1), net.n_classes).permute(0, 3, 1, 2).float()
                dice = multiclass_dice_coeff(mask_pred[:, 1:], mask_true[:, 1:], reduce_batch_first=False)
                dice_scores.append(dice.item())  # Append the Dice score as a float

            pred_mask_images.append(mask_pred)
    net.train()

    average_dice_score = sum(dice_scores) / max(len(dice_scores), 1)  # Calculate the average Dice score
    return images, masks, pred_mask_images, dice_scores, average_dice_score
