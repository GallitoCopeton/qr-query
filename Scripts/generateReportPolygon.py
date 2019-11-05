import os
import re
from collections import OrderedDict

import datetime
from dateutil import tz
import json
import sys

import pandas as pd
from matplotlib import pyplot as plt

sys.path.insert(0, './Helper Scripts')
sys.path.insert(0, './Golden Master (AS IS)')
import appProcessFunction as aP
from preProcessing import BGR2RGB
import readImage as rI
import qrQuery


def getLocalTime(date):
    fromZone = tz.tzutc()
    date = date.replace(tzinfo=fromZone)
    localTz = tz.tzlocal()
    return date.astimezone(localTz)


def makeFolder(folderName):
    if not os.path.isdir(folderName):
        os.mkdir(folderName)


# %%
registersURI = 'mongodb+srv://findOnlyReadUser:RojutuNHqy@clusterfinddemo-lwvvo.mongodb.net/datamap?retryWrites=true'
registersDB = qrQuery.cloudMongoConnection(registersURI)

imagesURI = 'mongodb://imagesUser:cK90iAgQD005@idenmon.zapto.org:888/unimaHealthImages?authMechanism=SCRAM-SHA-1&authSource=unimaHealthImages'
imagesDB = qrQuery.localMongoConnection(imagesURI)
# %%
todaysDate = datetime.datetime.now()
startDay = 0
finishDay = 2
startDate = todaysDate - datetime.timedelta(days=startDay)
finishDate = startDate - datetime.timedelta(days=finishDay)
# %%
with open('./json/polygons.json', 'r') as file:
    polygonsJson = json.load(file)['polygons']
countriesPolygons = [entry['countries'] for entry in polygonsJson]
# %%
# Carpetas
allReportsFolder = './reports'
makeFolder(allReportsFolder)
dateString = re.sub(r':', '_',todaysDate.ctime())[4:]
todaysReportFolder = f'Reporte de {dateString}/'
fullPath = '/'.join([allReportsFolder, todaysReportFolder])
makeFolder(fullPath)
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
    
    documentsCount = registersDB.registerstotals.count_documents({
        '$and': [
            {'createdAt': dateQuery},
            {'geo_loc': locationQuery}
        ]
    })
    if documentsCount == 0:
        print(f'No existen registros en este periodo en {country.capitalize()}')
        continue
    documentsFound = registersDB.registerstotals.find({
        '$and': [
            {'createdAt': dateQuery},
            {'geo_loc': locationQuery}
        ]
    })
    allTestInfo = []
    
    for test in documentsFound:
        qrCode = test['qrCode']
        registerNumber = test['count']
        validity = test['control'].upper()
        date = getLocalTime(test['createdAt']).ctime()
        generalInfo = [('País', country.capitalize()),
                    ('Código QR', qrCode),
                    ('Registro No.', registerNumber),
                    ('Validez',test['control'].upper()),
                    ('Fecha',getLocalTime(test['createdAt']).ctime())]
        proteinInfo = [(marker['name'].upper(), marker['result'].upper())
            for marker in test['marker']]
        diseaseInfo = [(disease['name'].upper(), disease['result'].upper())
            for disease in test['disease']]
        
        imageTestQuery = {
            'filename': qrCode,
            'count': registerNumber
        }
        imageDetails = rI.readManyCustomQueryDetails(
            imagesDB.imagetotals, imageTestQuery, 1)
        imagesExist = 'Sí' if len(imageDetails) > 0 else 'No' 
        if len(imageDetails) > 0:
            imageDetails[0]['qr'] = qrCode
            error = False
            #error = aP.doFullProcess(
            #    imageDetails[0], figsize=8, folder=fullPath, show=True)
            if error:
                print(
                    f'Ocurrió un error con el registro {registerNumber} del qr {qrCode}')
#            originalImageName = 'original.png'
#            fullPathOriginalImage = ''.join(
#                [fullPath, qrCode,'-', str(registerNumber), '/', originalImageName])
#            plt.imsave(fullPathOriginalImage,
#                       BGR2RGB(imageDetails[0]['image']))
        else:
            print(f'El registro {registerNumber} del qr {qrCode} no tiene imágenes')
            pathNotFoundImage = ''.join([fullPath, qrCode, '-', str(registerNumber)])
            makeFolder(pathNotFoundImage)
        imagesInfo = [('Imágenes', imagesExist)]
        testInfo = generalInfo+proteinInfo+diseaseInfo+imagesInfo
        testInfoDict = OrderedDict(testInfo)
        allTestInfo.append(testInfoDict)
    countryDataframe = pd.DataFrame(allTestInfo)
    countryDataframes.append(countryDataframe)
fullDataframe = pd.concat(countryDataframes, sort=False)
fullDataframe.set_index('País', inplace=True)
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
startRow += len(list(documentsFound)) + 2

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
