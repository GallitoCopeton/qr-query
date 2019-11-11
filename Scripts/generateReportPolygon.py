# %%
import datetime
import json
import os
import re
import sys
from collections import OrderedDict

import matplotlib
import numpy as np
import pandas as pd
import pymongo
from dateutil import tz
from matplotlib import pyplot as plt

import qrQuery
from ImageProcessing.colorTransformations import BGR2RGB
from ReadImages import readImage as rI
from ShowProcess import showProcesses as sP

scriptPath = os.path.dirname(os.path.abspath(__file__))
os.chdir(scriptPath)


# %%
URI = 'mongodb+srv://findOnlyReadUser:RojutuNHqy@clusterfinddemo-lwvvo.mongodb.net/datamap?retryWrites=true'
dbName = 'datamap'

collectionNameImages = 'imagestotals'
collectionNameData = 'registerstotals'
collectionImages = qrQuery.getCollection(URI, dbName, collectionNameImages)
collectionData = qrQuery.getCollection(URI, dbName, collectionNameData)
# %%
todaysDate = datetime.datetime.now()
startDay = 10
finishDay = 13
startDate = todaysDate - datetime.timedelta(days=startDay)
finishDate = startDate - datetime.timedelta(days=finishDay-startDay)

# %%
with open('./json/polygons.json', 'r') as file:
    polygonsJson = json.load(file)['polygons']
countriesPolygons = [entry['countries'] for entry in polygonsJson]
# %%
# Carpetas
allReportsFolder = './reports'
qrQuery.makeFolder(allReportsFolder)
dateString = re.sub(r':', '_', todaysDate.ctime())[4:]
todaysReportFolder = f'Reporte de {dateString}/'
fullPath = '/'.join([allReportsFolder, todaysReportFolder])
qrQuery.makeFolder(fullPath)
# Inicialización archivo excel
excelName = f'Reporte-{dateString}-{finishDay-startDay}-dias.xlsx'
fullExcelPath = ''.join([fullPath, excelName])
writer = pd.ExcelWriter(fullExcelPath, engine='xlsxwriter')
startRow = 0
# Inicialización valores tabla resumen
totalTests = 0
totalInvalidTests = 0
totalValidTests = 0
totalPositives = 0
totalNegatives = 0
totalTestsWithImages = 0
totalTestsNoImages = 0
# Queries
dateQuery = {'$lt': startDate, '$gte': finishDate}
countryDataframes = []
for country in countriesPolygons[0].keys():
    polygon = countriesPolygons[0][country]
    locationQuery = {'$geoWithin':
                     {'$geometry': {
                         'type': 'Polygon',
                         'coordinates': polygon
                     }}}
    fullQuery = {
        '$and': [
            {'createdAt': dateQuery},
            {'geo_loc': locationQuery}
        ]
    }
    documentsCount = qrQuery.getDocumentCount(collectionData, fullQuery)
    if documentsCount == 0:
        print(
            f'No existen registros en este periodo en {country.capitalize()}')
        continue
    documentsFound = collectionData.find(fullQuery)
    allTestInfo = []
    testDataframes = []
    for test in documentsFound:
        qrCode = test['qrCode']
        registerNumber = test['count']
        validity = test['control'].upper()
        date = qrQuery.getLocalTime(test['createdAt']).ctime()
        generalInfo = [('País', country.capitalize()),
                       ('Código QR', qrCode),
                       ('Registro No.', registerNumber),
                       ('Validez', test['control'].upper()),
                       ('Fecha', qrQuery.getLocalTime(test['createdAt']).ctime())]
        proteinInfo = [(marker['name'].upper(), marker['result'].upper())
                       for marker in test['marker']]
        diseaseInfo = [(disease['name'].upper(), disease['result'].upper())
                       for disease in test['disease']]
        imageTestQuery = {
            'fileName': qrCode,
            'count': registerNumber
        }
        imageDetails = rI.customQuery(
            collectionImages, imageTestQuery)
        imagesExist = 'Sí' if len(imageDetails) > 0 else 'No'
        if len(imageDetails) > 0:
            imageDetails[0]['qr'] = qrCode
            fig = sP.showClusterProcess(
                imageDetails[0]['file'], 3, 5, (7, 8), show=True, returnFig=True)
            if fig is False:
                print(
                    f'Ocurrió un error con el registro {registerNumber} del qr {qrCode}')
            elif type(fig) is matplotlib.figure.Figure:
                figName = 'process.png'
                fullPathFig = ''.join(
                    [fullPath, qrCode, '-', str(registerNumber)])
                qrQuery.makeFolder(fullPathFig)
                fig.savefig(''.join([fullPathFig, '/', figName]))
            originalImageName = 'original.png'
            fullPathOriginalImage = ''.join(
                [fullPath, qrCode, '-', str(registerNumber)])
            qrQuery.makeFolder(fullPathOriginalImage)

            plt.imsave(''.join([fullPathOriginalImage, '/', originalImageName]),
                       BGR2RGB(imageDetails[0]['file']))
        else:
            print(
                f'El registro {registerNumber} del qr {qrCode} no tiene imágenes')
            pathNotFoundImage = ''.join(
                [fullPath, qrCode, '-', str(registerNumber)])
            qrQuery.makeFolder(pathNotFoundImage)
        imagesInfo = [('Imágenes', imagesExist)]
        testInfo = generalInfo+proteinInfo+diseaseInfo+imagesInfo
        testInfoDict = OrderedDict(testInfo)
        allTestInfo.append(testInfoDict)
    countryDataframe = pd.DataFrame(allTestInfo)
    countryDataframes.append(countryDataframe)
try:
    fullDataframe = pd.concat(countryDataframes, sort=False)
except ValueError:
    print('No se encontró ningún registro en esta búsqueda')
    sys.exit(0)
fullDataframe.set_index('País', inplace=True)
# Resumen de información
totalTests += len(fullDataframe)
totalValidTests += len(
    fullDataframe[fullDataframe['Validez'] == 'VALID'])
totalInvalidTests += len(
    fullDataframe[fullDataframe['Validez'] == 'INVALID'])
totalPositives += len(
    fullDataframe[fullDataframe['TB'] == 'POSITIVE'])
totalNegatives += len(
    fullDataframe[fullDataframe['TB'] == 'NEGATIVE'])
totalTestsWithImages += len(
    fullDataframe[fullDataframe['Imágenes'] == 'Sí'])
totalTestsNoImages += len(
    fullDataframe[fullDataframe['Imágenes'] == 'No'])
if startRow == 0:
    fullDataframe.to_excel(writer, sheet_name='Sheet1',
                           startrow=startRow)
else:
    fullDataframe.to_excel(writer, sheet_name='Sheet1',
                           startrow=startRow, header=False)
startRow += documentsCount + 2

# %%
reportHeaders = [
    'Días del reporte',
    'Tests Totales',
    'Tests Válidos Totales',
    'Tests Inválidos Totales',
    'Total Positivos',
    'Total Negativos',
    'Tests Con Imagen Totales',
    'Tests Sin Imagen Totales'
]
reportData = [
    finishDay-startDay,
    totalTests,
    totalValidTests,
    totalInvalidTests,
    totalPositives,
    totalNegatives,
    totalTestsWithImages,
    totalTestsNoImages
]
reportDataframe = pd.DataFrame(
    reportData, index=reportHeaders, columns=['Cantidad'])
reportDataframe.to_excel(writer, sheet_name='Sheet1',
                         startrow=len(fullDataframe) + 3,
                         startcol=5)
worksheet = writer.sheets['Sheet1']
worksheet.set_column('A:A', 10, None)
worksheet.set_column('B:B', 20, None)
worksheet.set_column('C:C', 20, None)
worksheet.set_column('D:D', 17, None)
worksheet.set_column('E:E', 25, None)
worksheet.set_column('F:N', 25, None)
worksheet.set_column('Q:Q', 25, None)
writer.save()
