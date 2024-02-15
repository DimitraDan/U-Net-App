import os

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone


class CustomUser(AbstractUser):
    user_type_data = ((1, "Admin"), (2, "Doctor"))
    user_type = models.CharField(default=1, choices=user_type_data, max_length=10)
    birthday = models.CharField(max_length=20)


def upload_path_img(instance, filename):
    return f'image/{instance.purpose}/{filename}'


def upload_path_mask(instance, filename):
    return f'mask/{instance.purpose}/{filename}'


def upload_path_true_mask(instance, filename):
    return f'mask/trueMask/{filename}'


def upload_path_pred_mask(instance, filename):
    return f'mask/predMask/{filename}'


def upload_path_run_image(instance, filename):
    return f'image/runImage/{filename}'


def create_directory_if_not_exists(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)


class MultipleImage(models.Model):
    id = models.AutoField(primary_key=True)
    images = models.FileField(upload_to=upload_path_img, blank=True)
    masks = models.FileField(upload_to=upload_path_mask, blank=True)
    purpose = models.CharField(max_length=20)
    postedBy = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    date = models.DateField(default=timezone.now)

    def save(self, *args, **kwargs):
        create_directory_if_not_exists(os.path.join('media', 'image', self.purpose))
        create_directory_if_not_exists(os.path.join('media', 'mask', self.purpose))
        create_directory_if_not_exists(os.path.join('media', 'mask', 'trueMask'))
        create_directory_if_not_exists(os.path.join('media', 'mask', 'predMask'))
        create_directory_if_not_exists(os.path.join('media', 'image', 'runImage'))
        super(MultipleImage, self).save(*args, **kwargs)


class AverageTrainLoss(models.Model):
    id = models.AutoField(primary_key=True)
    epoch = models.IntegerField()
    average_train_loss = models.FloatField(blank=True, null=True)
    average_validation_loss = models.FloatField(blank=True, null=True)


class Validation(models.Model):
    id = models.AutoField(primary_key=True)
    learning_rate = models.FloatField()
    epoch = models.IntegerField()
    validation_score = models.FloatField(blank=True, null=True)
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
    average_loss_round = models.ManyToManyField(AverageTrainLoss, blank=True)
    validation_round = models.ManyToManyField(Validation, blank=True)
    checkpoint = models.ManyToManyField(Checkpoint, blank=True)

    def delete(self, *args, **kwargs):
        # Delete associated Validation objects and their files
        for validation in self.validation_round.all():
            validation.image.delete()
            validation.true_mask.delete()
            validation.pred_mask.delete()
        self.validation_round.all().delete()

        # Delete associated Checkpoint objects and their files
        for checkpoint in self.checkpoint.all():
            checkpoint.file_path.delete()
        self.checkpoint.all().delete()

        super().delete(*args, **kwargs)
