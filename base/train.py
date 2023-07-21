import logging
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
from base.models import Run, TrainLoss, Validation, Checkpoint, FailedRun

dir_img = "media/selected/image/train/"
dir_mask = "media/selected/mask/train/"
dir_checkpoint = "base/checkpoints/"


def create_image_representation(image_tensor, format='jpeg'):
    # Assuming image_tensor is a tensor representing an image
    # Convert the tensor to a PIL Image
    to_pil = ToPILImage()
    image = to_pil(image_tensor.cpu())

    # Create a BytesIO object to hold the image data
    image_io = BytesIO()

    # Save the PIL Image to the BytesIO object with the specified format
    image.save(image_io, format=format)

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
    n_val = int(len(dataset) * val_percent)
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

                train_loss = TrainLoss.objects.create(
                    train_loss=loss.item(),
                    epoch=epoch,
                    step=global_step
                )
                run.train_loss.add(train_loss)

                pbar.set_postfix(**{'loss (batch)': loss.item()})

                # Evaluation round
                division_step = (n_train // (5 * batch_size))
                if division_step > 0:
                    if global_step % division_step == 0:
                        val_score = evaluate(model, val_loader, device, amp)
                        scheduler.step(val_score)

                        logging.info('Validation Iou score: {}'.format(val_score))
                        validation = Validation.objects.create(
                            learning_rate=optimizer.param_groups[0]['lr'],
                            avg_validation_Iou=val_score,
                            epoch=epoch,
                            step=global_step,
                            validation_Iou=iou[global_step - 1],
                            image=create_image_representation(images[0], 'jpeg'),
                            true_mask=create_image_representation(true_masks[0].float(), 'png'),
                            pred_mask=create_image_representation(masks_pred.argmax(dim=1)[0].float(), 'png')
                        )
                        run.validation_loss.add(validation)

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

    model = torch.hub.load('milesial/Pytorch-UNet', 'unet_carvana', pretrained=False, scale=0.5)
    model.to(device=device)

    state_dict = torch.load(model_path, map_location=device)
    try:
        model.load_state_dict(state_dict)
    except:
        state_dict.pop('mask_values')
        model.load_state_dict(state_dict)

    deleteFiles(dir_checkpoint)
    run = Run.objects.create(status='RUNNING', trainer=request.user, name=request.POST.get("name"))
    try:
        torch.cuda.empty_cache()
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
            amp=False,
            weight_decay=1e-8,
        )
        # Training completed successfully
        run.status = 'FINISHED'
        run.save()
    except KeyboardInterrupt or Exception as e:
        checkpoint_uuid = uuid.uuid4()

        run.status = 'FAILED'
        run.save()
        print(f"Training failed: {str(e)}")

        # Create FailedRun instance
        failed_run = FailedRun.objects.create(
            run=run,
            model_path=f'{dir_checkpoint}/failed_run_{checkpoint_uuid}.pth',
            optimizer_state_path=f'{dir_checkpoint}/optimizer_state_{checkpoint_uuid}.pth'
        )
        failed_run.image_files.set(run.image_files.all())  # Copy image files from the failed run
        return failed_run
    finally:
        deleteFiles(dir_img)
        deleteFiles(dir_mask)
        return run
