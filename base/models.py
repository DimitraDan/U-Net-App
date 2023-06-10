import uuid

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
    train_loss = models.ManyToManyField(TrainLoss)
    validation_loss =  models.ManyToManyField(Validation)
    checkpoint = models.ManyToManyField(Checkpoint)

class Patient(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE) 
    image = models.ManyToManyField(MultipleImage)
    treatment = models.CharField(max_length=300)
    diagnosis = models.CharField(max_length=50)

class Doctor(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    specialisation = models.CharField(max_length=50, null=True )
    experience = models.CharField(max_length=50, null=True)
    patient = models.ManyToManyField(Patient)