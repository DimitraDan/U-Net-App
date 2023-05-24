import torch
import torch.nn.functional as F
from tqdm import tqdm
import logging
from base.iou_score import multiclass_iou_coeff, iou_coeff
from base.data_loading import BasicDataset, CarvanaDataset
from torch.utils.data import DataLoader, random_split, Dataset

dir_img = "media/image/evaluate"
dir_mask = "media/mask/evaluate"

@torch.inference_mode()
def evaluate(net, dataloader, device, amp):
    net.eval()
    num_val_batches = len(dataloader)
    iou_score = 0
    # iterate over the validation set
    with torch.autocast(device.type if device.type != 'mps' else 'cpu', enabled=amp):
        for batch in tqdm(dataloader, total=num_val_batches, desc='Validation round', unit='batch', leave=False):
            image, mask_true = batch['image'], batch['mask']
            # move images and labels to correct device and type
            image = image.to(device=device, dtype=torch.float32, memory_format=torch.channels_last)
            mask_true = mask_true.to(device=device, dtype=torch.long)

            # predict the mask
            mask_pred = net(image)

            if net.n_classes == 1:
                assert mask_true.min() >= 0 and mask_true.max() <= 1, 'True mask indices should be in [0, 1]'
                mask_pred = (F.sigmoid(mask_pred) > 0.5).float()
                # compute the Dice score
                iou_score += iou_coeff(mask_pred, mask_true, reduce_batch_first=False)
            else:
                assert mask_true.min() >= 0 and mask_true.max() < net.n_classes, 'True mask indices should be in [0, n_classes]'
                # convert to one-hot format
                mask_true = F.one_hot(mask_true, net.n_classes).permute(0, 3, 1, 2).float()
                mask_pred = F.one_hot(mask_pred.argmax(dim=1), net.n_classes).permute(0, 3, 1, 2).float()
                # compute the iou score, ignoring background
                iou_score += multiclass_iou_coeff(mask_pred[:, 1:], mask_true[:, 1:], reduce_batch_first=False)

    net.train()
    return iou_score / max(num_val_batches, 1)


def evaluating():
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    logging.info(f'Using device {device}')

    model = torch.hub.load('milesial/Pytorch-UNet', 'unet_carvana', pretrained=False, scale=0.5)
    model.to(device=device)
    state_dict = torch.load("base/checkpoint_epoch1.pth", map_location=device)
    del state_dict['mask_values']

    model.load_state_dict(state_dict)
    try:
        dataset = CarvanaDataset(dir_img, dir_mask, 0.5)
    except (AssertionError, RuntimeError, IndexError):
        dataset = BasicDataset(dir_img, dir_mask, 0.5)
        
    val_loader = DataLoader(dataset, shuffle=False, drop_last=True)
    return evaluate(model, val_loader, device, False)