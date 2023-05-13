import logging
import os
import torch.nn.functional as F
from base.data_loading import BasicDataset, CarvanaDataset
from torch.utils.data import DataLoader, random_split, Dataset
from torch import optim
import torch.nn as nn
from tqdm import tqdm
from base.iou_score import *
from pathlib import Path
import shutil
import wandb
from base.evaluate import evaluate


# Define a callback function that saves the logs to a file
def save_logs_to_file(logs):
    # Get the log directory
    log_dir = wandb.run.dir
    print(log_dir)

    # Create the log file path
    log_file = os.path.join(log_dir, 'MODEL.pth')

    # Open the log file in append mode and write the logs
    with open(log_file, 'a') as f:
        f.write(str(logs) + '\n')


def deleteFiles(folder):
    for filename in os.listdir(folder):
        file_path = os.path.join(folder, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception as e:
            print('Failed to delete %s. Reason: %s' % (file_path, e))


dir_img = "media/selected/image/train"
dir_mask = "media/selected/mask/train"
dir_checkpoint = "base/checkpoints"


def train_model(
        model,
        device,
        epochs: int = 5,
        batch_size: int = 1,
        learning_rate: float = 1e-5,
        val_percent: float = 0.1,
        save_checkpoint: bool = True,
        img_scale: float = 0.5,
        amp: bool = False,
        weight_decay: float = 1e-8,
        momentum: float = 0.999,
        gradient_clipping: float = 1.0,
):
    # 1. Create dataset
    try:
        dataset = CarvanaDataset(dir_img, dir_mask, img_scale)
    except (AssertionError, RuntimeError, IndexError):
        dataset = BasicDataset(dir_img, dir_mask, img_scale)

    # 2. Split into train / validation partitions
    n_val = int(len(dataset) * val_percent)
    n_train = len(dataset) - n_val
    train_set, val_set = random_split(dataset, [n_train, n_val], generator=torch.Generator().manual_seed(0))

    # 3. Create data loaders
    loader_args = dict(batch_size=batch_size, num_workers=os.cpu_count(), pin_memory=True)
    train_loader = DataLoader(train_set, shuffle=True, **loader_args)
    val_loader = DataLoader(val_set, shuffle=False, drop_last=True, **loader_args)

    # Log in to WandB with your API key
    wandb.login(key="3e1234cfe5ed344ab23cea32ea863b2d5c110f09")

    # (Initialize logging)
    experiment = wandb.init(project='U-Net', resume='allow')
    experiment.config.update(
        dict(epochs=epochs, batch_size=batch_size, learning_rate=learning_rate,
             val_percent=val_percent, save_checkpoint=save_checkpoint, img_scale=img_scale, amp=amp)
    )

    logging.info(f'''Starting training:
        Epochs:          {epochs}
        Batch size:      {batch_size}
        Learning rate:   {learning_rate}
        Training size:   {n_train}
        Validation size: {n_val}
        Checkpoints:     {save_checkpoint}
        Device:          {device.type}
        Images scaling:  {img_scale}
        Mixed Precision: {amp}
    ''')

    # 4. Set up the optimizer, the loss, the learning rate scheduler and the loss scaling for AMP
    optimizer = optim.RMSprop(model.parameters(),
                              lr=learning_rate, weight_decay=weight_decay, momentum=momentum, foreach=True)
    scheduler = optim.lr_scheduler.ReduceLROnPlateau(optimizer, 'max', patience=5)  # goal: maximize Iou score
    grad_scaler = torch.cuda.amp.GradScaler(enabled=amp)
    criterion = nn.CrossEntropyLoss() if model.n_classes > 1 else nn.BCEWithLogitsLoss()
    global_step = 0
    iou = []

    # 5. Begin training
    for epoch in range(1, epochs + 1):
        model.train()
        epoch_loss = 0
        with tqdm(total=n_train, desc=f'Epoch {epoch}/{epochs}', unit='img') as pbar:
            for batch in train_loader:
                images, true_masks = batch['image'], batch['mask']

                assert images.shape[1] == model.n_channels, \
                    f'Network has been defined with {model.n_channels} input channels, ' \
                    f'but loaded images have {images.shape[1]} channels. Please check that ' \
                    'the images are loaded correctly.'

                images = images.to(device=device, dtype=torch.float32, memory_format=torch.channels_last)
                true_masks = true_masks.to(device=device, dtype=torch.long)

                with torch.autocast(device.type if device.type != 'mps' else 'cpu', enabled=amp):
                    masks_pred = model(images)
                    if model.n_classes == 1:
                        loss = criterion(masks_pred.squeeze(1), true_masks.float())
                        loss += iou_loss(F.sigmoid(masks_pred.squeeze(1)), true_masks.float(), multiclass=False)
                        iou.append(iou_coeff(F.sigmoid(masks_pred.squeeze(1)), true_masks.float()))
                    else:
                        loss = criterion(masks_pred, true_masks)
                        loss += iou_loss(
                            F.softmax(masks_pred, dim=1).float(),
                            F.one_hot(true_masks, model.n_classes).permute(0, 3, 1, 2).float(),
                            multiclass=True
                        )
                        iou.append(multiclass_iou_coeff(
                            F.softmax(masks_pred, dim=1).float(),
                            F.one_hot(true_masks, model.n_classes).permute(0, 3, 1, 2).float(),
                        ))

                optimizer.zero_grad(set_to_none=True)
                grad_scaler.scale(loss).backward()
                torch.nn.utils.clip_grad_norm_(model.parameters(), gradient_clipping)
                grad_scaler.step(optimizer)
                grad_scaler.update()

                pbar.update(images.shape[0])
                global_step += 1
                epoch_loss += loss.item()
                experiment.log({
                    'train_loss': loss.item(),
                    'step': global_step,
                    'epoch': epoch
                })

                pbar.set_postfix(**{'loss (batch)': loss.item()})

                # Evaluation round
                division_step = (n_train // (5 * batch_size))
                if division_step > 0:
                    if global_step % division_step == 0:
                        histograms = {}
                        for tag, value in model.named_parameters():
                            tag = tag.replace('/', '.')
                            if not torch.isinf(value).any():
                                histograms['Weights/' + tag] = wandb.Histogram(value.data.cpu())
                            if not torch.isinf(value.grad).any():
                                histograms['Gradients/' + tag] = wandb.Histogram(value.grad.data.cpu())

                        val_score = evaluate(model, val_loader, device, amp)
                        scheduler.step(val_score)

                        logging.info('Validation Iou score: {}'.format(val_score))

                        try:
                            experiment.log({
                                'learning_rate': optimizer.param_groups[0]['lr'],
                                'avg_validation_Iou': val_score,
                                'images': wandb.Image(images[0].cpu()),
                                'masks': {
                                    'true': wandb.Image(true_masks[0].float().cpu()),
                                    'pred': wandb.Image(masks_pred.argmax(dim=1)[0].float().cpu()),
                                },
                                'step': global_step,
                                'epoch': epoch,
                                'validation_Iou': iou[global_step - 1]
                                # **histograms
                            })
                        except:
                            pass

        if save_checkpoint:
            Path(dir_checkpoint).mkdir(parents=True, exist_ok=True)
            state_dict = model.state_dict()
            state_dict['mask_values'] = dataset.mask_values
            torch.save(state_dict, dir_checkpoint + '/checkpoint_epoch' + str(epoch) + '.pth')
            print(f'Checkpoint {epoch} saved!')

            # Save model to W&B
            wandb.save(dir_checkpoint + '/checkpoint_epoch' + str(epoch) + '.pth')


def training(model_path="base/MODEL.pth"):
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    logging.info(f'Using device {device}')

    model = torch.hub.load('milesial/Pytorch-UNet', 'unet_carvana', pretrained=False, scale=0.5)
    model.to(device=device)

    state_dict = torch.load(model_path, map_location=device)
    try:
        model.load_state_dict(state_dict)
    except:
        mask_values = state_dict.pop('mask_values')
        model.load_state_dict(state_dict)

    deleteFiles(dir_checkpoint)

    try:
        train_model(
            model=model,
            epochs=5,
            batch_size=1,
            learning_rate=1e-5,
            device=device,
            val_percent=0.1,
            save_checkpoint=True,
            img_scale=0.5,
            amp=False,
            weight_decay=1e-8, )

    except:
        logging.error('Detected OutOfMemoryError! '
                      'Enabling checkpointing to reduce memory usage, but this slows down training. '
                      'Consider enabling AMP (--amp) for fast and memory efficient training')
        torch.cuda.empty_cache()
        model.use_checkpointing()
        train_model(model=model,
                    epochs=5,
                    batch_size=1,
                    learning_rate=1e-5,
                    device=device,
                    val_percent=0.1,
                    save_checkpoint=True,
                    img_scale=0.5,
                    amp=False,
                    weight_decay=1e-8,
                    )

    deleteFiles(dir_img)
    deleteFiles(dir_mask)
