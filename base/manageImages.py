import base64
import io
from base64 import b64encode
from io import BytesIO

import cv2
import numpy as np
from PIL import Image as PIL_Image
from django.core.files.base import ContentFile

from base.models import *


def readb64(encoded_image):
    if ',' not in encoded_image:
        raise ValueError("Invalid encoded image format")

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


def base64_file(data, name=None, mask=False):
    split_data = data.split(';base64,')
    if len(split_data) == 2:
        _format, _img_str = split_data
    else:
        raise ValueError('Invalid base64 data format')

    _name, ext = _format.split('/')
    if not name:
        name = _name.split(":")[-1]

    decoded_data = base64.b64decode(_img_str)

    if mask:
        img_array = np.frombuffer(decoded_data, np.uint8)
        img = PIL_Image.open(io.BytesIO(img_array))

        if img.mode != 'L':
            # Convert to 'L' mode if not already in grayscale
            img = img.convert('L')

        decoded_data = img.tobytes()

    return ContentFile(decoded_data, name='{}.{}'.format(name, ext))


def imageToStr(img, format='jpeg'):
    supported_formats = ['jpeg', 'png']

    if format not in supported_formats:
        raise ValueError(f"Unsupported image format: {format}")

    with io.BytesIO() as buf:
        img.save(buf, format)
        image_bytes = buf.getvalue()

    encoded = b64encode(image_bytes).decode()
    mime = f'image/{format};'
    img_data = f"data:{mime}base64,{encoded}"
    return img_data


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


def createMask(request, image, x_points, y_points, is_circle=False, save='NO'):
    if image.startswith('data'):
        # Remove the 'data:image/jpeg;base64,' prefix if it exists
        image_data = image.split(',')[1] if ',' in image else image

        # Decode the base64 data
        image_bytes = base64.b64decode(image_data)

        # Create a BytesIO object to work with Pillow
        image_io = BytesIO(image_bytes)

        # Open the image using Pillow
        img = PIL_Image.open(image_io)
    else:
        current_directory = os.getcwd()
        img = PIL_Image.open(current_directory + image)

    w, h = img.size

    all_points = []
    for i, x in enumerate(x_points.split(",")):
        if x != '':
            x_float = float(x)
            y_float = float(y_points.split(',')[i])
            x_int = int(round(x_float))
            y_int = int(round(y_float))
            all_points.append([x_int, y_int])

    mask = np.zeros((h, w), dtype=np.uint8)

    if is_circle and len(all_points) >= 2:
        # For circles, we need at least two points to define the diameter
        center = tuple(all_points[0])
        radius = int(np.linalg.norm(np.array(all_points[0]) - np.array(all_points[1])))
        cv2.circle(mask, center, radius, 255, -1)
    else:
        arr = np.array(all_points, dtype=np.int32)
        cv2.fillPoly(mask, [arr], color=(255))

    mask = arrayTo64Mask(mask)

    if save == 'YES':
        MultipleImage(
            images=convert_image(base64_file(image), 'JPEG'),
            purpose='report',
            masks=convert_image(base64_file(mask), 'PNG'),
            postedBy=request.user
        ).save()

    return mask
