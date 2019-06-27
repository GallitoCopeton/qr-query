import base64
import os

import cv2
import numpy as np
import pymongo
from matplotlib import pyplot as plt


def read_from_DB(db, qr, array=True, count=0):
    """
    This function will read images from a database, local or remote.
    """
    if array:
        cursor = db.imagestotals.find({'fileName': qr})
        if cursor.count() > 0:
            return make_image_list(cursor)
        else:
            return 0
    else:
        cursor = db.imagestotals.find_one({'fileName': qr, 'count': count})
        if cursor:
            return readb64(cursor['file'])
        else:
            return 0


def readb64(base64_string):
    """
    This function will decode images from base 64 to matrix form.
    """
    nparr = np.fromstring(base64.b64decode(base64_string, '-_'), np.uint8)
    image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    rows, cols, _ = image.shape
    if(rows < cols):
        image = cv2.rotate(image, cv2.ROTATE_90_CLOCKWISE)
    return image


def make_image_list(cursor):
    """
    This function will arange a list of decoded images from a Mongo cursor.
    """
    images = []
    for entry in cursor:
        images.append(readb64(entry['file']))
    return images

def show_results(images):
    fig = plt.figure(figsize=(15, 15))
    fig.subplots_adjust(.1, 0)
    for i, image in enumerate(images):
        ax = fig.add_subplot(1, 3, i+1)
        plt.axis('off')
        ax.imshow(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
    plt.show()