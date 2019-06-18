import os
import random

import cv2
import matplotlib.pyplot as plt
import pandas as pd
import pymongo
from geopy.geocoders import Nominatim

import read_image as ir


class Browser:

    def __init__(self, QR, DB, LOCATION):
        self.QR = QR
        self.DB = DB
        self.__TIMEOUT_LOCAL = False
        self.__TIMEOUT_MONGO = False
        self.LOCATION = LOCATION.lower()

    def browse_images_local(self):
        if self.LOCATION == 'cloud':
            print('Please use the method "browse_images_local" for cloud usage.')
        try:
            local_images = ir.read_from_DB(self.DB, self.QR)
            if local_images == 0:
                print('The qr is not found locally.')
                return False
            elif local_images != 0 and len(local_images) < 3:
                show_results(local_images)
                return True
            elif local_images != 0 and len(local_images) > 3:
                rand_sample = random.sample(local_images, k=3)
                show_results(rand_sample)
                return True
        except pymongo.errors.ServerSelectionTimeoutError:
            print('Local connection timeout error, server unavailable.')
            self.__TIMEOUT_LOCAL = True
    def browse_images_cloud(self):
        try:
            local_images = ir.read_from_DB(self.DB, self.QR)
            if local_images == 0:
                print('The qr is not found locally.')
                return False
            elif local_images != 0 and len(local_images) < 3:
                show_results(local_images)
                return True
            elif local_images != 0 and len(local_images) > 3:
                rand_sample = random.sample(local_images, k=3)
                show_results(rand_sample)
                return True
        except pymongo.errors.ServerSelectionTimeoutError:
            print('Local connection timeout error, server unavailable.')
            self.__TIMEOUT_LOCAL = True


def show_results(images):
    fig = plt.figure(figsize=(15, 15))
    fig.subplots_adjust(.1, 0)
    for i, image in enumerate(images):
        ax = fig.add_subplot(1, 3, i+1)
        plt.axis('off')
        ax.imshow(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
    plt.show()


QR = '601170500100387'
URI1 = 'mongodb://findOnlyReadUser:RojutuNHqy@idenmon.zapto.org:888/?authSource=prodLaboratorio'

CLIENT1 = pymongo.MongoClient(URI1)
DB1 = CLIENT1.prodLaboratorio

bro = Browser(QR, DB1)
result = bro.browse_images_local()
