import os
import re

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
days = 10
todaysDate = datetime.datetime.now()
daysBefore = datetime.timedelta(days=days)
targetDate = todaysDate-daysBefore
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
excelName = f'Reporte-{dateString}-{days}-dias.xlsx'
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
listOfDoneRegisters = [file for file in os.listdir(fullPath) if '.' not in file]
notInList = {'$nin': listOfDoneRegisters}
dateQuery = {'$lt': todaysDate, '$gte': targetDate}
headers = []
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
            {'geo_loc': locationQuery},
            {'qrCode': notInList}
        ]
    })
    if documentsCount == 0:
        print(f'No existen registros en este periodo en {country.capitalize()}')
        continue
    documentsFound = registersDB.registerstotals.find({
        '$and': [
            {'createdAt': dateQuery},
            {'geo_loc': locationQuery},
            {'qrCode': notInList}
        ]
    })
    allTestInfo = []
    testDataframes = []
    headers = ['País', 'Código QR', 'Count', 'Valid', 'Date']
    for test in documentsFound:
        qrCode = test['qrCode']
        registerNumber = test['count']
        validity = test['control'].upper()
        date = getLocalTime(test['createdAt']).ctime()
        testInfo = [country.capitalize(), qrCode, registerNumber,
                    validity, date]
        
        [testInfo.append(marker['result'].upper())
            for marker in test['marker']]
        [headers.append(marker['name'].upper())
            for marker in test['marker']]
        imageTestQuery = {
            'filename': qrCode,
            'count': registerNumber
        }
        if 'HIV' in headers:
            testInfo.insert(-2, None)
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
        testInfo.append(imagesExist)
        headers.append('Imágenes')
        allTestInfo.append(testInfo)
    testDataframe = pd.DataFrame(allTestInfo, columns=sorted(set(headers), key=headers.index))
    testDataframe.set_index('País', inplace=True)
    testDataframes.append(testDataframe)
    countryDataframe = pd.concat(testDataframes)
    totalTests += len(countryDataframe)
    totalValidTests += len(
        countryDataframe[countryDataframe['Valid'] == 'VALID'])
    totalInvalidTests += len(
        countryDataframe[countryDataframe['Valid'] == 'INVALID'])
    totalPositives += len(
        countryDataframe[countryDataframe['TB'] == 'POSITIVE'])
    totalNegatives += len(
        countryDataframe[countryDataframe['TB'] == 'NEGATIVE'])
    totalTestsWithImages += len(
        countryDataframe[countryDataframe['Imágenes'] == 'Sí'])
    totalTestsNoImages += len(
        countryDataframe[countryDataframe['Imágenes'] == 'No'])
    if startRow == 0:
        countryDataframe.to_excel(writer, sheet_name='Sheet1',
                                  startrow=startRow)
    else:
        countryDataframe.to_excel(writer, sheet_name='Sheet1',
                                  startrow=startRow, header=False)
    startRow += len(list(documentsFound)) + 2

# %%
reportHeaders = [
    'Días del reporte',
    'Total Tests',
    'Total Valid Tests',
    'Total Invalid Tests',
    'Total Positives',
    'Total Negatives',
    'Total Tests With Images',
    'Total Tests Without Images'
]
reportData = [
    days,
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
                         startcol=len(headers) + 1)
worksheet = writer.sheets['Sheet1']
worksheet.set_column('A:A', 10, None)
worksheet.set_column('B:B', 25, None)
worksheet.set_column('D:D', 15, None)
worksheet.set_column('E:E', 25, None)
worksheet.set_column('F:K', 17, None)
worksheet.set_column('M:M', 25, None)
writer.save()
