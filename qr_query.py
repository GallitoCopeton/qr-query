import os
import random

import cv2
import matplotlib.pyplot as plt
import pandas as pd
import pymongo
from geopy.geocoders import Nominatim

import read_image as ir

# Variables that should not change their values are gritten in UPPER CASE

# Default URIs to connect to MongoDB URI1: LOCAL server URI2: Atlas
URI1 = 'mdongodb://findOnlyReadUser:RojutuNHqy@idenmon.zapto.org:888/?authSource=prodLaboratorio'
URI2 = 'mongodb+srv://findOnlyReadUser:RojutuNHqy@clusterfinddemo-lwvvo.mongodb.net/datamap?retryWrites=true'
# Testing
QR = '601170500100387'
PATH = './'

# Check type of connection to databases
if URI1:
    try:
        CLIENT1 = pymongo.MongoClient(URI1)
        DB1 = CLIENT1.prodLaboratorio
        LOCAL = True
        print('Connection to local Mongo successful.')
    except pymongo.errors.InvalidURI:
        print('Could not connect to local Mongo, incorrect URI.')
        LOCAL = False
if URI2:
    try:
        CLIENT2 = pymongo.MongoClient(URI2)
        DB2 = CLIENT2.datamap
        CLOUD = True
        print('Connection to Atlas successful.')
    except pymongo.errors.InvalidURI:
        print('Could not connect to Atlas, incorrect URI.')
        CLOUD = False

if LOCAL or CLOUD:
    if LOCAL:
        try:
            l_images_from_DB = ir.read_from_DB(DB1, QR)
            if len(l_images_from_DB) < 3:
                fig = plt.figure(figsize=(15, 15))
                fig.subplots_adjust(.1, 0)
                for i, local_image in enumerate(l_images_from_DB):
                    ax = fig.add_subplot(1, 3, i+1)
                    plt.axis('off')
                    ax.imshow(cv2.cvtColor(local_image, cv2.COLOR_BGR2RGB))
                plt.show()
            elif len(l_images_from_DB) > 3:
                rand_sample = random.sample(l_images_from_DB, k=3)
                fig = plt.figure(figsize=(15, 15))
                fig.subplots_adjust(.1, 0)
                for i, local_image in enumerate(rand_sample):
                    ax = fig.add_subplot(1, 3, i+1)
                    plt.axis('off')
                    ax.imshow(cv2.cvtColor(local_image, cv2.COLOR_BGR2RGB))
                plt.show()
            elif l_images_from_DB == 0:
                print('The qr is not found locally.')
        except pymongo.errors.ServerSelectionTimeoutError:
            print('Local connection timeout error, server unavailable.')
    elif CLOUD:
        try:
            c_images_from_DB = ir.read_from_DB(DB2, QR)
            if c_images_from_DB != 0 and len(c_images_from_DB) < 3:
                fig = plt.figure(figsize=(15, 15))
                fig.subplots_adjust(.1, 0)
                for i, local_image in enumerate(c_images_from_DB):
                    ax = fig.add_subplot(1, 3, i+1)
                    plt.axis('off')
                    ax.imshow(cv2.cvtColor(local_image, cv2.COLOR_BGR2RGB))
                plt.show()
            elif c_images_from_DB != 0 and len(c_images_from_DB) > 3:
                rand_sample = random.sample(c_images_from_DB, k=3)
                fig = plt.figure(figsize=(15, 15))
                fig.subplots_adjust(.1, 0)
                for i, local_image in enumerate(rand_sample):
                    ax = fig.add_subplot(1, 3, i+1)
                    plt.axis('off')
                    ax.imshow(cv2.cvtColor(local_image, cv2.COLOR_BGR2RGB))
                plt.show()
            elif c_images_from_DB == 0:
                print('The qr code is not found in the remote database.')
        except pymongo.errors.ServerSelectionTimeoutError:
            print('Atlas connection timeout error, database unavailable.')
    else:
        print('There are no images with that qr in neither databases')
else:
    print('No connection was successful, no information could be gathered.')
