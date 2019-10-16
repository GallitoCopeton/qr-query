# %%
import os
import re

import pymongo
import datetime
import numpy as np
from matplotlib import pyplot as plt
import cv2

try:
    os.chdir(os.path.join(os.getcwd(), 'Scripts'))
    print(os.getcwd())
except:
    print(os.getcwd())
    pass

import readImage as ir


# Default URIs to connect to MongoDB URI1: LOCAL server URI2: Atlas.
URI1 = 'mongodb://imagesUser:cK90iAgQD005@idenmon.zapto.org:888/unimaHealthImages?authSource=unimaHealthImages&authMechanism=SCRAM-SHA-1'
URI2 = 'mongodb+srv://findOnlyReadUser:RojutuNHqy@clusterfinddemo-lwvvo.mongodb.net/datamap?retryWrites=true'
QR_code_start = int('1')
QR_code_finish = int('2')
QR_array = np.arange(QR_code_start, QR_code_finish, 1)
QR_array = [str(qr) for qr in QR_array]
print(QR_array)
CLIENT1 = pymongo.MongoClient(URI1)
CLIENT2 = pymongo.MongoClient(URI2)
DB2 = CLIENT2.datamap
foundQrsImages = []
#%% search with qrs

for QR in QR_array:
    cursor = DB2.imagestotals.find({'fileName': QR}).sort([('createdAt', pymongo.DESCENDING)]).limit(2)
    for i, doc in enumerate(cursor):
        print(doc)
        image = ir.readb64(doc['file'])
        date = doc['createdAt']
        date = datetime.datetime.date(date)
        plt.imsave(f'Images/Img{i+1}-{QR}-{date}.png', cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
        print(doc['fileName']+'-'+str(i))
        foundQrsImages.append(doc['fileName'])
foundQrsImages = set(foundQrsImages)
foundQrsRegisters = []
for QR in QR_array:
    cursor = DB2.registerstotals.find({'qrCode': QR}).limit(2)
    for i, doc in enumerate(cursor):
        print(doc['qrCode']+'-'+str(i))
        foundQrsRegisters.append(doc['qrCode'])
foundQrsRegisters = set(foundQrsRegisters)
#%% search last registered images
foundQrsImages = []
DB1 = CLIENT1.unimaHealthImages
cursor = DB1.imagetotals.find().limit(100).sort('_id', -1)
destFolder = 'oct 16_5-7_images/'
if not os.path.isdir(destFolder):
    os.mkdir(destFolder)
for i, doc in enumerate(cursor):
        image = ir.readb64(doc['file'])
        date = doc['createdAt']
        QR = doc['filename']
        date = re.sub(r':', r'_',str(doc['createdAt'])[0:19])
        plt.imsave(f'{destFolder}Img{i+1}-{QR}-{date}.png', cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
        print(doc['filename']+'-'+str(i))
        foundQrsImages.append(doc['filename'])
foundQrsImages = set(foundQrsImages)