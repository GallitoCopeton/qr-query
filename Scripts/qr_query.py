import re

import cv2
import matplotlib.pyplot as plt
import pandas as pd
import pymongo
from geopy.geocoders import Nominatim

import perspective as pPe
import preProcessing as pP
import read_image as ir
import readImage as rI
import sorts as srt
from DataBrowser import DataBrowser
from ImageBrowser import ImageBrowser

# Variables that should not change their values are gritten in UPPER CASE.

# Default URIs to connect to MongoDB URI1: LOCAL server URI2: Atlas.
URI1 = 'mongodb://findOnlyReadUser:RojutuNHqy@idenmon.zapto.org:888/?authSource=prodLaboratorio'
URI2 = 'mongodb+srv://findOnlyReadUser:RojutuNHqy@clusterfinddemo-lwvvo.mongodb.net/datamap?retryWrites=true'


def getImages(QR_code, amount):
    DB1 = localMongoConnection(URI1)
    DB2 = cloudMongoConnection(URI2)
    localImageBrowser = ImageBrowser(QR_code, DB1, 'local')
    localImageResult = localImageBrowser.browseImages()
    if localImageResult['timeout']:
        print('Server is unreachable, timeout error.')
    if not localImageResult['found']:
        print('No images were found locally, searching in the cloud now.')
    cloudImageBrowser = ImageBrowser(QR_code, DB2, 'cloud')
    cloudImageResult = cloudImageBrowser.browseImages()
    if cloudImageResult['timeout']:
        print('Mongo Atlas is unreachable, timeout error.')
    if not cloudImageResult['found']:
        print('No images were found in Atlas.')
    images = []
    for image in localImageResult['images']:
        images.append(image)
    for image in cloudImageResult['images']:
        images.append(image)
    return images


def getData(QR_code):
    DB1 = localMongoConnection(URI1)
    DB2 = cloudMongoConnection(URI2)
    localDataBrowser = DataBrowser(QR_code, DB1, 'local')
    localDataResult = localDataBrowser.browseData()
    if localDataResult['timeout']:
        print('Server is unreachable, timeout error')
    if not localDataResult['found']:
        print('No data was found locally, searching in the cloud now.')
    cloudDataBrowser = DataBrowser(QR_code, DB2, 'cloud')
    cloudDataResult = cloudDataBrowser.browseData()
    if cloudDataResult['timeout']:
        print('Mongo Atlas is unreachable, timeout error.')
    if not cloudDataResult['found']:
        print('No data was found in Atlas.')
    try:
        return localDataResult['data'].append(localDataResult['data'], ignore_index=True)
    except:
        if localDataResult['data'] is not None:
            return localDataResult['data']
        else:
            return cloudDataResult['data']


def localMongoConnection(URI):
    if URI:
        try:
            CLIENT1 = pymongo.MongoClient(URI)
            DB1 = CLIENT1.prodLaboratorio
            print('Connection to local Mongo successful.')
            return DB1
        except pymongo.errors.InvalidURI:
            print('Could not connect to local Mongo, incorrect URI.')
            return None
    else:
        print('No URI to connect to')
        return None


def cloudMongoConnection(URI):
    if URI:
        try:
            CLIENT2 = pymongo.MongoClient(URI)
            DB2 = CLIENT2.datamap
            print('Connection to Atlas successful.')
            return DB2
        except pymongo.errors.InvalidURI:
            print('Could not connect to Atlas, incorrect URI.')
            return None
    else:
        print('No URI to connect to')
        return None


def getQrSquare(path):
    """Use Benjas algorithm to extract the QR site instead of test site"""
    imageCv2 = cv2.imread(path)
    imgBinary = pP.contourBinarization(
        imageCv2, 3, 7, 85, 2, inverse=True, mean=False)
    externalSquare = pP.findTreeContours(imgBinary)
    ext_index = 1
    externalOrdSquare = srt.sortPointsContours(externalSquare)
    perspectiveBinary = pPe.perspectiveTransform(
        imgBinary, externalOrdSquare[ext_index], -5, True)
    perspectiveBGR = pPe.perspectiveTransform(
        imageCv2, externalOrdSquare[ext_index], -5)
    external = pP.findExternalContours(perspectiveBinary)
    if(len(external) > 0):
        minCnt = min(external, key=cv2.contourArea)
        return pPe.perspectiveTransform(perspectiveBGR, srt.sortPoints(minCnt), 15, False)
    else:
        print('No pudo leerse el código, intenta escribirlo a mano')


def isValidQr(qrCode):
    regexQr = r'\d{15}'
    return re.search(regexQr, qrCode)


def splitInputQrs(inputQrs):
    if len(inputQrs) == 0:
        return None
    regexSplit = r' |,|, '
    return re.split(regexSplit, inputQrs)
