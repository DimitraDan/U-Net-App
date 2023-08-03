import os, shutil
import cv2
import base64
import numpy as np
import io
from base.manageImages import convert_image, base64_file
from PIL import Image

import os
import base64
import io
from PIL import Image


def insertToFolder(folderImage, folderMask, image, mask):
    _, _, imageFiles = next(os.walk(folderImage))
    _, _, maskFiles = next(os.walk(folderMask))
    print(folderImage)

    # determine file extension of the input image
    if image.startswith('data:image/jpeg;base64,'):
        ext = '.jpeg'
        image_data = image.replace('data:image/jpeg;base64,', '')
    elif image.startswith('data:image/png;base64,'):
        ext = '.png'
        image_data = image.replace('data:image/png;base64,', '')
    else:
        raise ValueError('Unsupported image format')

    # determine file extension of the mask image
    if mask.startswith('data:image/jpeg;base64,'):
        mask_data = mask.replace('data:image/jpeg;base64,', '')
    elif mask.startswith('data:image/png;base64,'):
        mask_data = mask.replace('data:image/png;base64,', '')
    else:
        raise ValueError('Unsupported mask format')

    # convert base64 string to binary data
    binary_img_data = base64.b64decode(image_data)
    binary_mask_data = base64.b64decode(mask_data)

    # Save the image and mask files to their respective folders
    img_filename = os.path.join(folderImage, str(len(imageFiles)) + ext)
    seg_mask_filename = os.path.join(folderMask, str(len(maskFiles)) + '_Segmentation.png')

    with open(img_filename, 'wb') as f:
        f.write(binary_img_data)

    with io.BytesIO(binary_mask_data) as stream:
        with Image.open(stream) as img:
            img = img.convert("L").point(lambda x: 0 if x < 128 else 255, '1')
            img.save(seg_mask_filename, "PNG")


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
