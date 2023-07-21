import os

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone

class CustomUser(AbstractUser):
    user_type_data = ((1, "Admin"), (2, "Doctor"), (3, "Patient"))
    user_type = models.CharField(default=1, choices=user_type_data, max_length=10)
    birthday = models.CharField(max_length=20)


def upload_path_img(self, filename):
    return f'image/{self.purpose}/{filename}'


def upload_path_mask(self, filename):
    return f'mask/{self.purpose}/{filename}'


def upload_path_true_mask(self, filename):
    return f'mask/trueMask/{filename}'


def upload_path_pred_mask(self, filename):
    return f'mask/predMask/{filename}'


def upload_path_run_image(self, filename):
    return f'image/runImage/{filename}'


class MultipleImage(models.Model):
    id = models.AutoField(primary_key=True)
    images = models.FileField(upload_to=upload_path_img, blank=True)
    masks = models.FileField(upload_to=upload_path_mask, blank=True)
    purpose = models.CharField(max_length=20)
    postedBy = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    date = models.DateField(default=timezone.now)


class TrainLoss(models.Model):
    id = models.AutoField(primary_key=True)
    train_loss = models.FloatField()
    epoch = models.IntegerField()
    step = models.IntegerField()


class Validation(models.Model):
    id = models.AutoField(primary_key=True)
    learning_rate = models.FloatField()
    avg_validation_Iou = models.FloatField()
    epoch = models.IntegerField()
    step = models.IntegerField()
    validation_Iou = models.FloatField()
    image = models.FileField(upload_to=upload_path_run_image, blank=True)
    true_mask = models.FileField(upload_to=upload_path_true_mask, blank=True)
    pred_mask = models.FileField(upload_to=upload_path_pred_mask, blank=True)


class Checkpoint(models.Model):
    id = models.AutoField(primary_key=True)
    epoch = models.IntegerField()
    file_path = models.FileField(upload_to='checkpoint_files/')


class Run(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=20, unique=True)
    trainer = models.ForeignKey(CustomUser, on_delete=models.PROTECT)
    status = models.CharField(max_length=10)
    date = models.DateField(default=timezone.now)
    train_loss = models.ManyToManyField(TrainLoss, blank=True)
    validation_loss = models.ManyToManyField(Validation, blank=True)
    checkpoint = models.ManyToManyField(Checkpoint, blank=True)

    def delete(self, *args, **kwargs):
        # Delete associated TrainLoss objects
        self.train_loss.all().delete()

        # Delete associated Validation objects and their files
        for validation in self.validation_loss.all():
            validation.image.delete()
            validation.true_mask.delete()
            validation.pred_mask.delete()
        self.validation_loss.all().delete()

        # Delete associated Checkpoint objects and their files
        for checkpoint in self.checkpoint.all():
            checkpoint.file_path.delete()
        self.checkpoint.all().delete()

        super().delete(*args, **kwargs)


class FailedRun(models.Model):
    run = models.ForeignKey(Run, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)
    model_path = models.CharField(max_length=255)
    optimizer_state_path = models.CharField(max_length=255)
    image_files = models.ManyToManyField(MultipleImage)

    def rollback_checkpoints(self):
        # Delete the saved model checkpoint
        if os.path.exists(self.model_path):
            os.remove(self.model_path)

        # Delete the saved optimizer state
        if os.path.exists(self.optimizer_state_path):
            os.remove(self.optimizer_state_path)

        # Delete the associated image files
        self.image_files.all().delete()


class Patient(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    image = models.ManyToManyField(MultipleImage)
    treatment = models.CharField(max_length=300)
    diagnosis = models.CharField(max_length=50)


class Doctor(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    specialisation = models.CharField(max_length=50, null=True)
    experience = models.CharField(max_length=50, null=True)
    patient = models.ManyToManyField(Patient)
