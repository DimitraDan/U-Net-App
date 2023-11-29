import shutil
import cv2
import numpy as np

import os
import base64
import io
from PIL import Image

from medicalApp import settings


def insertToFolder(folderImage, folderMask, image, mask):
    _, _, imageFiles = next(os.walk(folderImage))
    _, _, maskFiles = next(os.walk(folderMask))

    # Handle the image input
    if image.startswith('data:image/jpeg;base64,'):
        image_data = image.split(',', 1)[1]  # Extract base64 data
        # Add padding if missing
        while len(image_data) % 4 != 0:
            image_data += '='
        binary_img_data = base64.b64decode(image_data)  # Convert base64 to binary data
    elif image.startswith('data:image/png;base64,'):
        image_data = image.split(',', 1)[1]  # Extract base64 data
        # Add padding if missing
        while len(image_data) % 4 != 0:
            image_data += '='
        binary_img_data = base64.b64decode(image_data)  # Convert base64 to binary data
    elif image.endswith(('.jpeg', '.jpg', '.png')):
        with open('./' + image, 'rb') as file:
            binary_img_data = file.read()
    else:
        raise ValueError('Unsupported image format')

    # Handle the mask input
    if mask.startswith('data:image/jpeg;base64,'):
        mask_data = mask.split(',', 1)[1]  # Extract base64 data
        # Add padding if missing
        while len(mask_data) % 4 != 0:
            mask_data += '='
        binary_mask_data = base64.b64decode(mask_data)  # Convert base64 to binary data
    elif mask.startswith('data:image/png;base64,'):
        mask_data = mask.split(',', 1)[1]  # Extract base64 data
        # Add padding if missing
        while len(mask_data) % 4 != 0:
            mask_data += '='
        binary_mask_data = base64.b64decode(mask_data)  # Convert base64 to binary data
    elif mask.endswith(('.jpeg', '.jpg', '.png')):
        with open('./' + mask, 'rb') as file:
            binary_mask_data = file.read()
    else:
        raise ValueError(f'Unsupported mask format for: {mask}')

    # Save the image and mask files to their respective folders
    img_filename = os.path.join(folderImage, str(len(imageFiles)) + '.jpeg')
    seg_mask_filename = os.path.join(folderMask, str(len(maskFiles)) + '_Segmentation' + '.png')

    with open(img_filename, 'wb') as f:
        f.write(binary_img_data)

    with open(seg_mask_filename, 'wb') as f:
        f.write(binary_mask_data)


def find_dir_with_string(start_dir, search_string):
    for dirpath, dirnames, filenames in os.walk(start_dir):
        for dirname in dirnames:
            if search_string in dirname:
                return os.path.join(dirpath, dirname)


def readb64(encoded_image):
    header, data = encoded_image.split(',', 1)
    image_data = base64.b64decode(data)
    np_array = np.frombuffer(image_data, np.uint8)
    image = cv2.imdecode(np_array, cv2.IMREAD_UNCHANGED)
    return image


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


def copy_images_and_masks(obj):
    # Copy the image to a new location with a specific name
    image_destination = os.path.join(
        settings.MEDIA_ROOT, "image/run_eval/", f"{obj.id}.jpeg"
    )
    shutil.copyfile(os.path.join(settings.MEDIA_ROOT, obj.images.name), image_destination)

    # Copy the mask to a new location with a specific name
    mask_destination = os.path.join(
        settings.MEDIA_ROOT, "mask/run_eval/", f"{obj.id}_Segmentation.png"
    )
    shutil.copyfile(os.path.join(settings.MEDIA_ROOT, obj.masks.name), mask_destination)
