import random

import cv2
import matplotlib.pyplot as plt
import pandas as pd
import pymongo
from geopy.geocoders import Nominatim

import read_image as ir
from Browser import Browser

# Variables that should not change their values are gritten in UPPER CASE.

# Default URIs to connect to MongoDB URI1: LOCAL server URI2: Atlas.
URI1 = 'mongodb://findOnlyReadUser:RojutuNHqy@idenmon.zapto.org:888/?authSource=prodLaboratorio'
URI2 = 'mongodb+srv://findOnlyReadUser:RojutuNHqy@clusterfinddemo-lwvvo.mongodb.net/datamap?retryWrites=true'
# Testing
QR = '601170500100387'
PATH = './'

# Check type of connection to databases.
if URI1:
    try:
        CLIENT1 = pymongo.MongoClient(URI1)
        DB1 = CLIENT1.prodLaboratorio
        LOCAL = True
        print('Connection to local Mongo successful.')
        tests_local = DB1.registerstotals.find({'qrCode': QR})
    except pymongo.errors.InvalidURI:
        print('Could not connect to local Mongo, incorrect URI.')
        LOCAL = False
if URI2:
    try:
        CLIENT2 = pymongo.MongoClient(URI2)
        DB2 = CLIENT2.datamap
        CLOUD = True
        print('Connection to Atlas successful.')
        tests_mongo = DB2.registerstotals.find({'qrCode': QR})
    except pymongo.errors.InvalidURI:
        print('Could not connect to Atlas, incorrect URI.')
        CLOUD = False
        
# Gather images. Priority on local storage.
if LOCAL or CLOUD:
    local_browser = Browser(QR, DB1, 'local')
    local_result = local_browser.browse_images()
    if local_result['timeout']:
        print('Server is unreachable, timeout error.')
    if not local_result['found']:
        print('No results were found locally, searching in the cloud now.')
        cloud_browser = Browser(QR, DB2, 'cloud')
        cloud_result = cloud_browser.browse_images()
        if cloud_result['timeout']:
            print('Mongo Atlas is unreachable, timeout error.')
        if not cloud_result['found']:
            print('No results were found in Atlas.')
else:
    print('No connection was successful, no information could be gathered.')

# Gather data from Mongo Atlas
geolocator = Nominatim(user_agent="Query")
if not local_result['timeout']:
    if tests_mongo.count() > 0:
        result_dataframe = pd.DataFrame()
        for doc in tests_mongo:
            # Location extraction
            latitude = str(doc['location'][0]['latitude'])
            longitude = str(doc['location'][0]['longitude'])
            exact_location = latitude + ',' + longitude
            location = geolocator.reverse(exact_location)
            # Object building
            temporary_dict = {
                'Ciudad': location.raw['address']['city'],
                'Validez': doc['control'],
                'No. Imagen': doc['count'],
                'Fecha + 5hrs': str(doc['createdAt'])
            }
            # Update dataframe
            for marker in doc['marker']:
                temporary_dict[marker['name']] = marker['result']
            result_dataframe = result_dataframe.append(
                temporary_dict, ignore_index=True)
elif not TIMEOUT_MONGO:
    if tests_local.count() > 0:
        result_dataframe = pd.DataFrame()
        for doc in tests_local:
            # Location extraction
            latitude = str(doc['location'][0]['latitude'])
            longitude = str(doc['location'][0]['longitude'])
            exact_location = latitude + ',' + longitude
            location = geolocator.reverse(exact_location)
            # Object building
            temporary_dict = {
                'Ciudad': location.raw['address']['city'],
                'Validez': doc['control'],
                'No. Imagen': doc['count'],
                'Fecha + 5hrs': str(doc['createdAt'])
            }
            for marker in doc['marker']:
                temporary_dict[marker['name']] = marker['result']
            # Update dataframe
            result_dataframe = result_dataframe.append(
                temporary_dict, ignore_index=True)
