import imageReaderRefactor as iR
import pymongo
import cv2
import os
import pandas as pd
import os
import random
from geopy.geocoders import Nominatim

URl1 = 'mongodb://findOnlyReadUser:RojutuNHqy@idenmon.zapto.org:888/?authSource=prodLaboratorio'
URl2 = 'mongodb+srv://findOnlyReadUser:RojutuNHqy@clusterfinddemo-lwvvo.mongodb.net/datamap?retryWrites=true'

def query_qr(qr, path, string_connection1 = URl1, string_connection2 = URl2):
    
    client1 = pymongo.MongoClient(URl1)
    db1 = client1.prodLaboratorio
    client2 =  pymongo.MongoClient(URl2)
    db2 = client2.datamap
    #GATHERING IMAGES SECTION
    imgsDB = iR.readFromDBAtlas(qr,
                         string_connection2, 
                         array=True)

    if len(imgsDB)==0: #Si no encuentro nada en Atlas
        #Busca en hub localmente (todas las que haya)
        imgsLocal = iR.readImageLocalV2(qr, path, ext = '.png')
        print('Local')
        print('Existen {} imágenes'.format(len(imgsLocal)))
        if len(imgsLocal) < 3: #Si no hay mas de 3 imagenes toma todas las que haya
            iR.multiDisp(imgsLocal, rows=1, cols=len(imgsLocal), figsize = (39,39))
        else: #Si no toma 3 al azar
            rand_sample = random.sample(imgsLocal, k=3)
            iR.multiDisp(rand_sample, rows=1, cols=3, figsize = (39,39))
    else:
        print('Extraídas de la base de datos')
        print('Existen {} imágenes'.format(len(imgsDB)))
        if len(imgsDB) < 3: #Si no hay mas de 3 imagenes toma todas las que haya
            iR.multiDisp(imgsDB, rows=1, cols=len(imgsDB), figsize = (39,39))
        else:#Si no toma 3 al azar
            rand_sample = random.sample(imgsDB, k=3)
            iR.multiDisp(rand_sample, rows=1, cols=3, figsize = (39,39))
    #GATHERING QR DATA SECTION
    listQrs = []
    #Columnas predeterminadas de dataframe
    column_df = ['No. Imagen', 'Validez', 'Fecha + 5hrs', 'Ciudad'] 
    #Busca todos los registros con ese QR en db2
    pruebas = list(db2.registerstotals.find({'qrCode': qr}))
    #Localizador de prueba
    geolocator = Nominatim(user_agent="Query")
    if len(list(pruebas)) > 0: #Si existen registros en esta base
        for doc in pruebas:
            resultDict = dict()
            #Extraccion ciudad
            latitude = str(doc['location'][0]['latitude'])
            longitude = str(doc['location'][0]['longitude'])
            exLoc = latitude + ',' + longitude
            location = geolocator.reverse(exLoc)
            #Adicion de informacion a campos (refactor)
            resultDict.update
            ([
                 ('Ciudad', location.raw['address']['city']), 
                 ('Validez', doc['control']), 
                 ('No. Imagen', doc['count']), 
                 ('Fecha + 5hrs', str(doc['createdAt'])[0:-10]) 
            ])
            namesProteins=[]
            for marker in doc['marker']: #Existen 5 marcadores dentro del diccionario 'marker'
                namesProteins.append(marker['name'])
                #Añadimos uno por uno los nombres de las proteinas al diccionario
                header = column_df+namesProteins
                #Nombre de la columna = marker['name']
                #Contenido de la columna = marker['result']
                resultDict[marker['name']] = marker['result']
            #Reunimos todos los diccionarios en una lista
            listQrs.append(resultDict)
        #Creacion de dataframe a partir de diccionarios
        result_df = pd.DataFrame.from_dict(listQrs)
        result_df = result_df[header]
        result_df = result_df.sort_values(by=['No. Imagen'], ascending=True)
        print(result_df.to_string(index=False))
        
    else: #Mismo procedimiento pero buscando en db1
        pruebas = list(db1.registerstotals.find({'qrCode': qr}))
        if len(list(pruebas)) > 0:
            for doc in pruebas:
                resultDict = dict()
                resultDict['QR'] = doc['qrCode']
                resultDict['Validez'] = doc['control']
                resultDict['No. Imagen'] = doc['count']
                namesProteins=[]
                for marker in doc['marker']:
                    namesProteins.append(marker['name'])
                    header = column_df+namesProteins
                    resultDict[marker['name']] = marker['result']
                listQrs.append(resultDict)
            result_df = pd.DataFrame.from_dict(listQrs)
            result_df = result_df[header]
            result_df = result_df.sort_values(by=['No. Imagen'], ascending=True)
            print(result_df.to_string(index=False))
        else:
            print('No existe información de ese QR!')


def fromDbToHub(path, qr, thisQrOnly= True, string_connection = URl2):
    """thisQrOnly specifies if only a specific qr code should be sent to the jupyter hub folder. If it is true, all images from imagestotals collection will be saved
    """
    client =  pymongo.MongoClient(string_connection)
    db = client.datamap
    if not thisQrOnly:
        db_tests = list(db.imagestotals.find())
    else:
        db_tests = list(db.imagestotals.find({'fileName': qr}))
    for prueba in db_tests:
        
        count = prueba['count']
        img = iR.readFromDBAtlas(prueba['fileName'] ,
                             string_connection, 
                             array=False)
        cv2.imwrite(path+prueba['fileName']+str(count)+'.png',img)