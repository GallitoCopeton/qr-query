
import base64
import cv2
import numpy as np
import sys
from matplotlib import pyplot as plt

#Scripts para leer y procesar imagen
sys.path.insert(0, '../Golden Master (AS IS)')
import readImage

# Mongodb connection string - Does this user can write?
MONGO_URL = 'mongodb://findOnlyReadUser:RojutuNHqy@unimahealth.ddns.net:27017/datamap'

# Mongodb image collection
MONGO_COLLECTION_QR = "imagetotals"
MONGO_COLLECTION_XM = "imagexm" 

#Image folders
IMG_FOLDER = "C:/Users/LaptopUser/jupyterNotebook/Imagenes/"
XM_FOLDER = "C:/Users/LaptopUser/jupyterNotebook/Imagenes XM/" 

def writeLocal(filename, img, folder = XM_FOLDER):
    path = folder + filename
    return cv2.imwrite(path, img)

def print_im_happy():
    print("Im happy...")

print_im_happy()