import os
import sys
import json
from datetime import datetime

import pymongo
from matplotlib import pyplot as plt
import cv2
import pandas as pd

import readImage as ir
import DataBrowser

# Default URIs to connect to MongoDB URI1: LOCAL server URI2: Atlas.
URI2 = 'mongodb+srv://findOnlyReadUser:RojutuNHqy@clusterfinddemo-lwvvo.mongodb.net/datamap?retryWrites=true'
CLIENT2 = pymongo.MongoClient(URI2)
db2 = CLIENT2.datamap

# Prepare folders


def createFolder(path):
    if not os.path.isdir(path):
        os.mkdir(path)


def saveImage(destination, image):
    plt.imsave(destination, cv2.cvtColor(image, cv2.COLOR_BGR2RGB))


RESULT_ROOT = './RESULT/'
createFolder(RESULT_ROOT)
completeRegister = pd.DataFrame()
doneQrs = os.listdir(RESULT_ROOT)
cursorImages = db2.imagestotals.find({'fileName': {'$nin': doneQrs}}, no_cursor_timeout=True)
#%%
for i, dataImage in enumerate(cursorImages):
    
    count = dataImage['count']
    qr = dataImage['fileName']
    print(f'Process for qr {qr}')
    if count > 30:
        print(f'Too many images, will skip qr {qr}')
        continue
    dataBrowser = DataBrowser.DataBrowser(qr, db2, 'cloud')
    dataForQr = dataBrowser.browseData()['data']
    date = datetime.date(dataImage['createdAt'])
    DEST_FOLDER = RESULT_ROOT+qr+'/'
    createFolder(DEST_FOLDER)
    IMAGE_NAME = f'{qr}-{date}-{count}.png'
    if dataForQr is not None:
        completeRegister = completeRegister.append(dataForQr)
    image = ir.readb64(dataImage['file'])
    saveImage(DEST_FOLDER+IMAGE_NAME, image)
cursorImages.close()
XLSX_NAME = f'registro total busqueda.xlsx'
completeRegister.to_excel(RESULT_ROOT+XLSX_NAME)
