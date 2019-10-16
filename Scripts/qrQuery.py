import re

import cv2
import matplotlib.pyplot as plt
import pandas as pd
import pymongo
from geopy.geocoders import Nominatim

import perspective as pPe
import preProcessing as pP
import sorts as srt
from DataBrowser import DataBrowser
from ImageBrowser import ImageBrowser

# Variables that should not change their values are gritten in UPPER CASE.

# Default URIs to connect to MongoDB URI1: LOCAL server URI2: Atlas.
URI1 = 'mongodb://imagesUser:cK90iAgQD005@idenmon.zapto.org:888/unimaHealthImages?authSource=unimaHealthImages&authMechanism=SCRAM-SHA-1'
URI2 = 'mongodb+srv://findOnlyReadUser:RojutuNHqy@clusterfinddemo-lwvvo.mongodb.net/datamap?retryWrites=true'


def getImages(QR_code):
    DB1 = localMongoConnection(URI1)
    DB2 = cloudMongoConnection(URI2)
    localImageBrowser = ImageBrowser(QR_code, DB1, 'local')
    localImageResult = localImageBrowser.browseImages()
    if localImageResult['timeout']:
        pass
        #print('Server is unreachable, timeout error.')
    if not localImageResult['found']:
        pass
        #print('No images were found locally, searching in the cloud now.')
    cloudImageBrowser = ImageBrowser(QR_code, DB2, 'cloud')
    cloudImageResult = cloudImageBrowser.browseImages()
    if cloudImageResult['timeout']:
        pass
        #print('Mongo Atlas is unreachable, timeout error.')
    if not cloudImageResult['found']:
        pass
        #print('No images were found in Atlas.')
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
        pass
        #print('Server is unreachable, timeout error')
    if not localDataResult['found']:
        pass
        #print('No data was found locally, searching in the cloud now.')
    cloudDataBrowser = DataBrowser(QR_code, DB2, 'cloud')
    cloudDataResult = cloudDataBrowser.browseData()
    if cloudDataResult['timeout']:
        pass
        #print('Mongo Atlas is unreachable, timeout error.')
    if not cloudDataResult['found']:
        pass
        #print('No data was found in Atlas.')
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
            DB1 = CLIENT1.unimaHealthImages
            return DB1
        except pymongo.errors.InvalidURI:
            return None
    else:
        print('No URI to connect to')
        return None


def cloudMongoConnection(URI):
    if URI:
        try:
            CLIENT2 = pymongo.MongoClient(URI)
            DB2 = CLIENT2.datamap
            return DB2
        except pymongo.errors.InvalidURI:
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
    if re.search(regexQr, qrCode):
        return True
    else:
        return False


def isNone(variable):
    if variable is None:
        return True
    else:
        return False


def splitInputQrs(inputQrs):
    if len(inputQrs) == 0:
        return None
    inputQrs = ",".join(inputQrs.split())
    regex = r'[^,\s][^\,]*[^,\s]*'
    return re.findall(regex, inputQrs)


def askForAmount(prompt):
    amount = -1
    while amount < 0:
        try:
            amount = int(input(prompt))
            if amount < 0:
                print('Introduce valores mayores a 0')
        except ValueError:
            print('No puedes introducir caracteres, sólo números')
    return amount


def getLatestImagesQrs(n):
    DB1 = localMongoConnection(URI1)
    localImageBrowser = ImageBrowser(None, DB1, 'local')
    return localImageBrowser.getLatestQrs(n)


def getLatestRegistersQrs(n):
    DB2 = cloudMongoConnection(URI2)
    cloudImageBrowser = DataBrowser(None, DB2, 'cloud')
    return cloudImageBrowser.getLatestQrs(n)


def fixQr(qr):
    return re.sub(r'[\[\]\'\"]', r'', qr)
