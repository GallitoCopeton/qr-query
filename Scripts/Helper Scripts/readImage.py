import base64
import os
from datetime import datetime

import cv2
import numpy as np
import pymongo
from matplotlib import pyplot as plt


def readSingleFromDb(collection, qr, count=0):
    """
    This function will read images from a database, local or remote.
    Will return 0 if no images found
    """
    cursor = collection.find_one({'filename': qr, 'count': count})
    if cursor:
        return readb64(cursor['file'])
    else:
        return 0


def readSingleFromDbDetails(collection, qr, count=0):
    """
    This function will read images from a database, local or remote.
    Will return 0 if no images found
    """
    cursor = collection.find_one({'filename': qr, 'count': count})
    if cursor:
        return {
            'image': readb64(cursor['file']),
            'createdAt': datetime.date(cursor['createdAt']),
            'qr': cursor['fileName'],
            'count': cursor['count']
        }
    else:
        return 0


def readManyFromDb(collection, qr):
    """
    This function will read images from a database, local or remote.
    Will return an empty array if no images found
    """
    cursor = collection.find({'filename': qr}).sort(
        [('createdAt', pymongo.DESCENDING)])
    if cursor is not None:
        return getImageList(cursor)
    else:
        return []


def readManyFromDbDetails(collection, qr):
    """
    This function will read images from a database, local or remote.
    Will return an empty array if no images found
    """
    cursor = collection.find({'filename': qr}).sort(
        [('createdAt', pymongo.DESCENDING)]).limit(10)
    if cursor is not None:
        return getImageListDetails(cursor)
    else:
        return []


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


def getImageList(cursor):
    """
    This function will arange a list of decoded images from a Mongo cursor.
    """
    return [readb64(entry['file']) for entry in cursor]


def getImageListDetails(cursor):
    """
    This function will arange a list of decoded images from a Mongo cursor.
    """
    return [{
        'image': readb64(entry['file']),
        'createdAt': datetime.date(entry['createdAt']),
        'qr': entry['filename'],
        'count': entry['count']
    } for entry in cursor]


def showImages(images):
    fig = plt.figure(figsize=(25,  25))
    fig.subplots_adjust(.1, 0)
    for i, image in enumerate(images):
        ax = fig.add_subplot(len(images), 1, i+1)
        plt.axis('off')
        if type(image) is dict:
            imageBGR = image['image']
            date = image['createdAt']
            qr = image['qr']
            count = image['count']
            title = '{}-{}-Num({})'.format(date, qr, count)
            ax.imshow(cv2.cvtColor(imageBGR, cv2.COLOR_BGR2RGB))
            plt.title(title)
        else:
            ax.imshow(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
            title = 'Num({})'.format(str(i+1))
            plt.title(title)
    plt.show()
