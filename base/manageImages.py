import base64
import io
import os
from base64 import b64encode
from io import BytesIO

import cv2
import numpy as np
from PIL import Image as PIL_Image
from django.core.files.base import ContentFile

from base.models import *


def readb64(encoded_image):
    header, data = encoded_image.split(',', 1)
    image_data = base64.b64decode(data)
    np_array = np.frombuffer(image_data, np.uint8)
    image = cv2.imdecode(np_array, cv2.IMREAD_UNCHANGED)
    return image


def arrayTo64Mask(img):
    pil_img = PIL_Image.fromarray(img)
    pil_img = pil_img.convert("L")
    buff = BytesIO()
    pil_img.save(buff, format="png")
    encoded = base64.b64encode(buff.getvalue()).decode("utf-8")
    mime = 'image/png;'
    img = "data:%sbase64,%s" % (mime, encoded)
    return img


def base64_file(data, name=None):
    _format, _img_str = data.split(';base64,')
    _name, ext = _format.split('/')
    if not name:
        name = _name.split(":")[-1]
    return ContentFile(base64.b64decode(_img_str), name='{}.{}'.format(name, ext))


def imageToStr(img):
    with io.BytesIO() as buf:
        img.save(buf, 'jpeg')
        image_bytes = buf.getvalue()
    encoded = b64encode(image_bytes).decode()
    mime = 'image/jpeg;'
    img = "data:%sbase64,%s" % (mime, encoded)
    return img


def convert_image(image_file, output_format):
    # Open the image using PIL
    img = PIL_Image.open(image_file)

    # If the image mode is not RGB, convert to RGB format
    if img.mode != 'RGB':
        img = img.convert('RGB')

    # Create an in-memory byte stream for the output data
    output_stream = io.BytesIO()

    # Save the image in the desired output format to the byte stream
    img.save(output_stream, format=output_format)

    # Reset the byte stream's position to the beginning
    output_stream.seek(0)

    # Return the byte stream's contents as a Django ContentFile object with the appropriate file extension
    filename, extension = os.path.splitext(image_file.name)
    return ContentFile(output_stream.getvalue(), name=filename + '.' + output_format.lower())


def createMask(request, image, x_points, y_points, save='NO'):
    img = readb64(image)
    w, h, c = img.shape

    MASK_HEIGHT = h
    MASK_WIDTH = w
    all_points = []
    for i, x in enumerate(x_points.split(",")):
        if x != '':
            all_points.append([int(x), int(y_points.split(',')[i])])

    arr = np.array(all_points)
    mask = np.zeros((MASK_WIDTH, MASK_HEIGHT))
    mask = cv2.fillPoly(mask, [arr], color=(255))
    mask = arrayTo64Mask(mask)

    if save == 'YES':
        MultipleImage(
            images=convert_image(base64_file(image), 'JPEG'),
            purpose='report',
            masks=convert_image(base64_file(mask), 'PNG'),
            postedBy=request.user
        ).save()

    return mask
