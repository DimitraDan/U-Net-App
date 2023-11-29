import numpy as np
import torch
import torch.nn.functional as F
from PIL import Image
from base.data_loading import BasicDataset
from unet.unetModel import UNet


def predict_img(net,
                full_img,
                device,
                scale_factor=1,
                out_threshold=0.5):
    net.eval()
    img = torch.from_numpy(BasicDataset.preprocess(None, full_img, scale_factor, is_mask=False))
    img = img.unsqueeze(0)
    img = img.to(device=device, dtype=torch.float32)

    with torch.no_grad():
        output = net(img).cpu()
        output = F.interpolate(output, (full_img.size[1], full_img.size[0]), mode='bilinear')
        if net.n_classes > 1:
            mask = output.argmax(dim=1)
        else:
            mask = torch.sigmoid(output) > out_threshold

    return mask[0].long().squeeze().numpy()


def mask_to_image(mask: np.ndarray, mask_values):
    if isinstance(mask_values[0], list):
        out = np.zeros((mask.shape[-2], mask.shape[-1], len(mask_values[0])), dtype=np.uint8)
    elif mask_values == [0, 1]:
        out = np.zeros((mask.shape[-2], mask.shape[-1]), dtype=bool)
    else:
        out = np.zeros((mask.shape[-2], mask.shape[-1]), dtype=np.uint8)

    if mask.ndim == 3:
        mask = np.argmax(mask, axis=0)

    for i, v in enumerate(mask_values):
        out[mask == i] = v

    return Image.fromarray(out)


def predict(image, model_path='base/MODEL.pth'):
    net = UNet(n_channels=3, n_classes=2, bilinear=False)
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    net.to(device=device)

    # Load the model state_dict
    state_dict = torch.load(model_path, map_location=device)

    # Check if "mask_values" is present in the state_dict
    if 'mask_values' in state_dict:
        mask_values = state_dict.pop('mask_values')
    else:
        # Provide a default value if "mask_values" is not present
        mask_values = [0, 1]

    # Load the UNet model state_dict
    net.load_state_dict(state_dict)

    # The rest of your code remains unchanged
    mask = predict_img(net=net, full_img=image, scale_factor=0.5, out_threshold=0.5, device=device)

    result = mask_to_image(mask, mask_values)

    return result
