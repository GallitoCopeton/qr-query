import pymongo as pymongo
import base64
import cv2
import numpy as np
import os
from matplotlib import pyplot as plt

#Read only, mongodb connection
MONGO_URL = 'mongodb://findOnlyReadUser:RojutuNHqy@unimahealth.ddns.net:888/datamap'

def readb64(base64_string):
    nparr = np.fromstring(base64.b64decode(base64_string,'-_'), np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    rows, cols, channels = img.shape
    if(rows < cols):
        img = cv2.rotate(img, cv2.ROTATE_90_CLOCKWISE)
    return img

#Read from imagestotals
def readFromDB(qr, string_connection, array, count = 0):
    client = pymongo.MongoClient(string_connection)
    db = client.prodLaboratorio

    if(array):
        cursor_img_totals = db.imagestotals.find({'fileName': qr})
        if(cursor_img_totals.count() > 0): return imageArray(cursor_img_totals)
        cursor_img_totals = db.imagehemas.find({'fileName': qr})
        if(cursor_img_totals.count() > 0): return imageArray(cursor_img_totals)
        else: 
            return ("No records!")
    else:
        cursor_img_totals = db.imagestotals.find_one({'fileName': qr, 'count': count})
        if(cursor_img_totals): return readb64(cursor_img_totals['file']) 
        else: 
            return ("No records!")
        
def readFromDBAtlas(qr, string_connection, array, count = 0):
    client = pymongo.MongoClient(string_connection)
    db = client.datamap
    if(array):
        cursor_img_totals = db.imagestotals.find({'fileName': qr})
        if(cursor_img_totals.count() > 0): 
            return imageArray(cursor_img_totals)
        else: 
            return ("No records!")
    else:
        cursor_img_totals = db.imagestotals.find_one({'fileName': qr, 'count': count})
        if(cursor_img_totals): 
            return readb64(cursor_img_totals['file'])
        else: 
            return ("No records!")

# Return array of base64 images
def imageArray(cursor):
    images = []
    for c in cursor:
        images.append(readb64(c['file']))
    return images

def readLocal(path):
    return cv2.imread(path,1)

def readImageLocalV2(qr, path, ext = '.png'):
    imgs = []
    for file in os.listdir(path):
        fileName = os.fsdecode(file)[0:-4] #To remove extension .png
        poppedName = fileName[0:-1-(len(fileName)-len(qr)-1)]
        if qr == poppedName:
            fileName = fileName + ext
            img = readLocal(path+fileName)
            imgs.append(img)
    return imgs

def readImage(qr, path = '../../Imagenes/', count = 0, local = False, array = False, ext = 'png', string_connection = MONGO_URL):
    print('Hello')
    if(local):
        img = readLocal(path + str(qr) + "." + ext)
        print(path + str(qr) + "." + ext)
        return img
    else:
        return readFromDB(qr, array, string_connection, count)
def multiDisp(imgs, figsize= (20,20), hspace = .1, wspace = 0, rows = 7, cols = 9):    
    fig = plt.figure(figsize=figsize)
    fig.subplots_adjust(hspace, wspace)
    for i, img in enumerate(imgs):
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        ax = fig.add_subplot(rows, cols, i+1)
        plt.title('Window{}'.format(i+1))
        plt.axis('off')
        ax.imshow(img)