import random

import matplotlib.pyplot as plt
import pandas as pd
import pymongo
from geopy.geocoders import Nominatim

import read_image as ir
from DataBrowser import DataBrowser
from ImageBrowser import ImageBrowser

# Variables that should not change their values are gritten in UPPER CASE.

# Default URIs to connect to MongoDB URI1: LOCAL server URI2: Atlas.
URI1 = 'mongodb://findOnlyReadUser:RojutuNHqy@idenmon.zapto.org:888/?authSource=prodLaboratorio'
URI2 = 'mongodb+srv://findOnlyReadUser:RojutuNHqy@clusterfinddemo-lwvvo.mongodb.net/datamap?retryWrites=true'
# Testing
QR = '601170500100126'
# PATH = './'

# Check type of connection to databases.
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
        
# Gather images. Priority on local storage.
if LOCAL or CLOUD:
    local_image_browser = ImageBrowser(QR, DB1, 'local')
    local_image_result = local_image_browser.browse_images()
    if local_image_result['timeout']:
        print('Server is unreachable, timeout error.')
    if not local_image_result['found']:
        print('No images were found locally, searching in the cloud now.')
        cloud_image_browser = ImageBrowser(QR, DB2, 'cloud')
        cloud_image_result = cloud_image_browser.browse_images()
        if cloud_image_result['timeout']:
            print('Mongo Atlas is unreachable, timeout error.')
        if not cloud_image_result['found']:
            print('No images were found in Atlas.')
else:
    print('No connection was successful, no information could be gathered.')

# Gather data. Priority on local storage
if LOCAL or CLOUD:
    local_data_browser = DataBrowser(QR, DB1, 'local')
    local_data_result = local_data_browser.browse_data()
    if local_data_result['timeout']:
        print('Server is unreachable, timeout error')
    if not local_data_result['found']:
        print('No data was found locally, searching in the cloud now.')
        cloud_data_browser = DataBrowser(QR, DB2, 'cloud')
        cloud_data_result = cloud_data_browser.browse_data()
        if cloud_data_result['timeout']:
            print('Mongo Atlas is unreachable, timeout error.')
        if not cloud_data_result['found']:
            print('No data was found in Atlas.')

def qr_search(QR_code):
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
            
    # Gather images. Priority on local storage.
    if LOCAL or CLOUD:
        local_image_browser = ImageBrowser(QR, DB1, 'local')
        local_image_result = local_image_browser.browse_images()
        if local_image_result['timeout']:
            print('Server is unreachable, timeout error.')
        if not local_image_result['found']:
            print('No images were found locally, searching in the cloud now.')
            cloud_image_browser = ImageBrowser(QR, DB2, 'cloud')
            cloud_image_result = cloud_image_browser.browse_images()
            if cloud_image_result['timeout']:
                print('Mongo Atlas is unreachable, timeout error.')
            if not cloud_image_result['found']:
                print('No images were found in Atlas.')
    else:
        print('No connection was successful, no information could be gathered.')

    # Gather data. Priority on local storage
    if LOCAL or CLOUD:
        local_data_browser = DataBrowser(QR, DB1, 'local')
        local_data_result = local_data_browser.browse_data()
        if local_data_result['timeout']:
            print('Server is unreachable, timeout error')
        if not local_data_result['found']:
            print('No data was found locally, searching in the cloud now.')
            cloud_data_browser = DataBrowser(QR, DB2, 'cloud')
            cloud_data_result = cloud_data_browser.browse_data()
            if cloud_data_result['timeout']:
                print('Mongo Atlas is unreachable, timeout error.')
            if not cloud_data_result['found']:
                print('No data was found in Atlas.')