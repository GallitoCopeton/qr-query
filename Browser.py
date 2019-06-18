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
        self.__timeout_local = False
        self.__timeout_mongo = False
        self.LOCATION = LOCATION.upper()
        self.found = False

    def browse_images(self):
        try:
            images = ir.read_from_DB(self.DB, self.QR)
            if images == 0:
                print('The qr is not found locally.')
                self.found = False
                if self.LOCATION == 'CLOUD':
                    return {
                        'TIMEOUT_'+self.LOCATION: self.__timeout_mongo,
                        'found': self.found
                    }
                 elif self.LOCATION == 'LOCAL':
                    return {
                        'TIMEOUT_'+self.LOCATION: self.__timeout_local,
                        'found': self.found
                    }      
            elif images != 0 and len(images) < 3:
                show_results(images)
                self.found = True
                if self.LOCATION == 'CLOUD':
                    return {
                 
                        'TIMEOUT_'+self.LOCATION: self.__timeout_mongo,
                        'found': self.found
                    }
                 elif self.LOCATION == 'LOCAL':
                    return {
                        'TIMEOUT_'+self.LOCATION: self.__timeout_local,
                        'found': self.found
                    }
            elif images != 0 and len(images) > 3:
                rand_sample = random.sample(images, k=3)
                show_results(rand_sample)
                return {
                        'TIMEOUT_'+self.LOCATION: self.__timeout_local,
                        'found': self.found
                    }
        except pymongo.errors.ServerSelectionTimeoutError:
            print('Local connection timeout error, server unavailable.')
            if self.LOCATION == 'CLOUD':
                self.__timeout_local = True
            if self.LOCATION == 'LOCAL':
                self.__timeout_mongo = True


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
