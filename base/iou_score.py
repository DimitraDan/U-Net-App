import torch
from torch import Tensor


def iou_coeff(input: Tensor, target: Tensor, reduce_batch_first: bool = False):
    # Average of iou coefficient for all batches, or for a single mask
    assert input.size() == target.size()
    assert input.dim() == 3 or not reduce_batch_first

    sum_dim = (-1, -2) if input.dim() == 2 or not reduce_batch_first else (-1, -2, -3)

    inter = (input * target).sum(dim=sum_dim)

    sets_sum = input.sum(dim=sum_dim) + target.sum(dim=sum_dim)
    sets_sum = torch.where(sets_sum == 0, inter, sets_sum)

    union = sets_sum - inter

    iou = inter / union
    return iou.mean()


def multiclass_iou_coeff(input: Tensor, target: Tensor, reduce_batch_first: bool = False, epsilon: float = 1e-6):
    # Average of iou coefficient for all classes
    return iou_coeff(input.flatten(0, 1), target.flatten(0, 1), reduce_batch_first)


def iou_loss(input: Tensor, target: Tensor, multiclass: bool = False):
    fn = multiclass_iou_coeff if multiclass else iou_coeff
    return 1 - fn(input, target, reduce_batch_first=True)


def dice_coeff(input: Tensor, target: Tensor, reduce_batch_first: bool = False, epsilon: float = 1e-6):
    """
    Calculate the Dice coefficient.

    Parameters:
    - input (Tensor): Predicted binary mask.
    - target (Tensor): Ground truth binary mask.
    - reduce_batch_first (bool): If True, compute the Dice coefficient for each batch and then average.
    - epsilon (float): Smoothing factor to prevent division by zero.

    Returns:
    - Tensor: The Dice coefficient.
    """

    # Check input and target shapes
    assert input.size() == target.size()
    assert input.dim() == 3 or not reduce_batch_first

    # Define dimensions to sum over
    sum_dim = (-1, -2) if input.dim() == 2 or not reduce_batch_first else (-1, -2, -3)

    # Calculate intersection and union
    inter = 2 * (input * target).sum(dim=sum_dim)
    sets_sum = input.sum(dim=sum_dim) + target.sum(dim=sum_dim)
    sets_sum = torch.where(sets_sum == 0, inter, sets_sum)

    # Calculate Dice coefficient
    dice = (inter + epsilon) / (sets_sum + epsilon)
    return dice.mean()


def multiclass_dice_coeff(input: Tensor, target: Tensor, reduce_batch_first: bool = False, epsilon: float = 1e-6):
    """
    Calculate the Dice coefficient for multiclass segmentation.

    Parameters:
    - input (Tensor): Predicted multiclass mask.
    - target (Tensor): Ground truth multiclass mask.
    - reduce_batch_first (bool): If True, compute the Dice coefficient for each batch and then average.
    - epsilon (float): Smoothing factor to prevent division by zero.

    Returns:
    - Tensor: The Dice coefficient for multiclass segmentation.
    """

    return dice_coeff(input.flatten(0, 1), target.flatten(0, 1), reduce_batch_first, epsilon)


def dice_loss(input: Tensor, target: Tensor, multiclass: bool = False):
    """
    Calculate the Dice loss.

    Parameters:
    - input (Tensor): Predicted mask.
    - target (Tensor): Ground truth mask.
    - multiclass (bool): If True, compute multiclass Dice loss.

    Returns:
    - Tensor: The Dice loss.
    """

    fn = multiclass_dice_coeff if multiclass else dice_coeff
    return 1 - fn(input, target, reduce_batch_first=True)
