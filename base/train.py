import logging
import math
import os
import uuid
from io import BytesIO
from pathlib import Path

import torch.nn as nn
import torch.nn.functional as F
from django.core.files import File
from torch import optim
from torch.utils.data import DataLoader, random_split
from torchvision.transforms import ToPILImage
from tqdm import tqdm

from base.data_loading import BasicDataset, CarvanaDataset
from base.evaluate import evaluate
from base.iou_score import *
from base.manageFolders import deleteFiles
from base.models import Run, Checkpoint, Validation, AverageTrainLoss
from unet.unetModel import UNet

dir_img = "media/image/run/"
dir_mask = "media/mask/run/"
dir_checkpoint = "base/checkpoints/"


def create_image_representation(image_tensor, format='jpeg'):
    # Assuming image_tensor is a tensor representing an image
    # Convert the tensor to a PIL Image
    to_pil = ToPILImage()

    # Ensure the tensor is in the correct range [0, 255]
    image_tensor = (image_tensor * 255).to(torch.uint8)

    # Convert the tensor to torch.uint8 type
    image_tensor = image_tensor.to(torch.uint8)

    # Convert to PIL Image
    image_pil = to_pil(image_tensor.squeeze().cpu())  # Remove batch dimension

    # Create a BytesIO object to hold the image data
    image_io = BytesIO()

    # Save the PIL Image to the BytesIO object with the specified format
    image_pil.save(image_io, format=format)

    # Create a Django File object from the BytesIO data
    image_file = File(image_io, name=f'{uuid.uuid4()}.{format}')

    return image_file


def train_model(
        run,
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

    # 2. Split into selected / validation partitions
    n_val = math.ceil(len(dataset) * val_percent)
    n_train = len(dataset) - n_val
    train_set, val_set = random_split(dataset, [n_train, n_val], generator=torch.Generator().manual_seed(0))

    # 3. Create data loaders
    loader_args = dict(batch_size=batch_size, num_workers=os.cpu_count(), pin_memory=True)
    train_loader = DataLoader(train_set, shuffle=True, **loader_args)
    val_loader = DataLoader(val_set, shuffle=False, drop_last=True, **loader_args)

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
    scheduler = optim.lr_scheduler.ReduceLROnPlateau(optimizer, 'max', patience=5)  # goal: maximize Dice score
    grad_scaler = torch.cuda.amp.GradScaler(enabled=amp)
    criterion = nn.CrossEntropyLoss() if model.n_classes > 1 else nn.BCEWithLogitsLoss()

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
                        loss += dice_loss(F.sigmoid(masks_pred.squeeze(1)), true_masks.float(), multiclass=False)
                    else:
                        loss = criterion(masks_pred, true_masks)
                        loss += dice_loss(
                            F.softmax(masks_pred, dim=1).float(),
                            F.one_hot(true_masks, model.n_classes).permute(0, 3, 1, 2).float(),
                            multiclass=True
                        )

                optimizer.zero_grad(set_to_none=True)
                grad_scaler.scale(loss).backward()
                torch.nn.utils.clip_grad_norm_(model.parameters(), gradient_clipping)
                grad_scaler.step(optimizer)
                grad_scaler.update()

                pbar.update(images.shape[0])
                epoch_loss += loss.item()
                pbar.set_postfix(**{'loss (batch)': loss.item()})

        # Calculate average training loss for each epoch
        average_train_loss = epoch_loss / len(train_loader)
        print(f'Training Average Loss: {average_train_loss}')

        # Evaluation round for each epoch
        val_images, val_masks, val_pred_mask_images, dice_scores, average_dice_score = evaluate(model, val_loader, device, False)
        scheduler.step(average_dice_score)
        logging.info('Validation Average Dice score: {}'.format(average_dice_score))

        for i in range(len(val_images)):
            print(f"Processing iteration {i}")
            print(f"LR: {optimizer.param_groups[0]['lr']}")
            print(f"Validation score: {dice_scores[i]}")

            validation = Validation.objects.create(
                learning_rate=optimizer.param_groups[0]['lr'],
                validation_score=dice_scores[i],
                epoch=epoch,
                image=create_image_representation(val_images[i], 'jpeg'),
                true_mask=create_image_representation(val_masks[i], 'png'),
                pred_mask=create_image_representation(1.0 - val_pred_mask_images[i], 'png')
            )
            run.validation_round.add(validation)

        average_loss = AverageTrainLoss.objects.create(
            epoch=epoch,
            average_train_loss=average_train_loss,
            average_validation_loss=average_dice_score
        )

        run.average_loss_round.add(average_loss)

        run.save()
        if save_checkpoint:
            try:
                checkpoint_uuid = uuid.uuid4()
                Path(dir_checkpoint).mkdir(parents=True, exist_ok=True)
                state_dict = model.state_dict()
                state_dict['mask_values'] = dataset.mask_values
                torch.save(state_dict, f'{dir_checkpoint}/checkpoint_{checkpoint_uuid}_{epoch}.pth')
                print(f'Checkpoint {epoch} saved!')

                checkpoint = Checkpoint.objects.create(epoch=epoch)
                checkpoint.file_path.save(f'checkpoint_{checkpoint_uuid}_{epoch}.pth',
                                          File(open(f'{dir_checkpoint}/checkpoint_{checkpoint_uuid}_{epoch}.pth', 'rb'))
                                          )
                run.checkpoint.add(checkpoint)
            except Exception as e:
                print(f"Error saving ch instance: {e}")


def training(model_path="base/MODEL.pth", request=None):
    if request.FILES.get("file") is not None:
        model_path = request.FILES.get("file")

    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    logging.info(f'Using device {device}')

    model = UNet(n_channels=3, n_classes=2, bilinear=False)
    model.to(device=device)

    state_dict = torch.load(model_path, map_location=device)
    try:
        model.load_state_dict(state_dict)
    except:
        state_dict.pop('mask_values')
        model.load_state_dict(state_dict)

    run = Run.objects.create(status='RUNNING', trainer=request.user, name=request.POST.get("name"))
    try:
        train_model(
            run=run,
            model=model,
            epochs=5,
            batch_size=1,
            learning_rate=1e-5,
            device=device,
            val_percent=0.1,
            save_checkpoint=True,
            img_scale=0.5,
            amp=True,
            weight_decay=1e-8,
        )
        run.status = 'FINISHED'
        run.save()
    except KeyboardInterrupt or Exception as e:
        run.status = 'FAILED'
        run.save()
        print(f"Training failed: {str(e)}")
    finally:
        deleteFiles(dir_img)
        deleteFiles(dir_mask)
        return run
