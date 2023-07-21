from rest_framework import serializers
from base.models import *


class CustomUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['id', 'username', 'email', 'user_type', 'birthday']


class MultipleImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = MultipleImage
        fields = ['id', 'images', 'masks', 'purpose', 'postedBy', 'date']


class TrainLossSerializer(serializers.ModelSerializer):
    class Meta:
        model = TrainLoss
        fields = ['id', 'train_loss', 'epoch', 'step']


class ValidationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Validation
        fields = ['id', 'learning_rate', 'avg_validation_Iou', 'epoch', 'step', 'validation_Iou', 'image', 'true_mask',
                  'pred_mask']


class CheckpointSerializer(serializers.ModelSerializer):
    class Meta:
        model = Checkpoint
        fields = ['id', 'epoch', 'file_path']


class RunSerializer(serializers.ModelSerializer):
    train_loss = TrainLossSerializer(many=True, read_only=True)
    validation_loss = ValidationSerializer(many=True, read_only=True)
    checkpoint = CheckpointSerializer(many=True, read_only=True)

    class Meta:
        model = Run
        fields = ['id', 'name', 'trainer', 'status', 'date', 'train_loss', 'validation_loss', 'checkpoint']


class FailedRunSerializer(serializers.ModelSerializer):
    image_files = MultipleImageSerializer(many=True, read_only=True)

    class Meta:
        model = FailedRun
        fields = ['id', 'run', 'timestamp', 'model_path', 'optimizer_state_path', 'image_files']


class PatientSerializer(serializers.ModelSerializer):
    image = MultipleImageSerializer(many=True, read_only=True)

    class Meta:
        model = Patient
        fields = ['id', 'user', 'image', 'treatment', 'diagnosis']


class DoctorSerializer(serializers.ModelSerializer):
    patient = PatientSerializer(many=True, read_only=True)

    class Meta:
        model = Doctor
        fields = ['id', 'user', 'specialisation', 'experience', 'patient']
