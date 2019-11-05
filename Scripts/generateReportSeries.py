import datetime
import json
import os
import re
import sys
from collections import defaultdict

import numpy as np
import pandas as pd
from dateutil import tz
from matplotlib import pyplot as plt

sys.path.insert(0, './Helper Scripts')
sys.path.insert(0, './Golden Master (AS IS)')
import appProcessFunction as aP
import qrQuery
import readImage as rI
from preProcessing import BGR2RGB



def getLocalTime(date):
    fromZone = tz.tzutc()
    date = date.replace(tzinfo=fromZone)
    localTz = tz.tzlocal()
    return date.astimezone(localTz)


def makeFolder(folderName):
    if not os.path.isdir(folderName):
        os.mkdir(folderName)


# %%
URI2 = 'mongodb+srv://findOnlyReadUser:RojutuNHqy@clusterfinddemo-lwvvo.mongodb.net/datamap?retryWrites=true'
DB2 = qrQuery.cloudMongoConnection(URI2)

imagesURI = 'mongodb://imagesUser:cK90iAgQD005@idenmon.zapto.org:888/unimaHealthImages?authMechanism=SCRAM-SHA-1&authSource=unimaHealthImages'
imagesDB = qrQuery.localMongoConnection(imagesURI)
# %%
todaysDate = datetime.datetime.now()
startDay = 0
finishDay = 2
startDate = todaysDate - datetime.timedelta(days=startDay)
finishDate = startDate - datetime.timedelta(days=finishDay)

# %%
with open('./json/series.json', 'r') as file:
    seriesJson = json.load(file)['series']
prefixCodes = [serie['serie']['prefixCode'] for serie in seriesJson]
seriesNames = [serie['serie']['name'] for serie in seriesJson]
seriesDict = dict(zip(seriesNames, prefixCodes))
# %%
# Carpetas
allReportsFolder = './reports'
makeFolder(allReportsFolder)
dateString = re.sub(r':', '_', todaysDate.ctime())[4:]
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
# Búsqueda de fecha
dateQuery = {'createdAt': {
    '$lt': startDate, '$gte': finishDate
}}
# %%
for key in seriesDict.keys():
    prefix = seriesDict[key]
    seriesRegEx = re.compile(prefix)
    regExQuery = {'qrCode': seriesRegEx}

    fullQuery = {'$and': [
        dateQuery,
        regExQuery
    ]}
    seriesDocumentsCount = DB2.registerstotals.count_documents(fullQuery)
    if seriesDocumentsCount == 0:
        print(
            f'No existen registros en este periodo en la serie {key} con prefijo {prefix}')
        continue
    seriesDocuments = DB2.registerstotals.find(fullQuery)
    allTestInfo = []
    testDataframes = []
    for test in seriesDocuments:
        qrCode = test['qrCode']
        registerNumber = test['count']
        validity = test['control'].upper()
        date = getLocalTime(test['createdAt']).ctime()
        testInfo = [key, qrCode, registerNumber,
                    validity, date]
        headers = ['Envío', 'Código QR', 'Count', 'Valid', 'Date']
        [testInfo.append(marker['result'].upper())
            for marker in test['marker']]
        [testInfo.append(disease['result'].upper())
            for disease in test['disease']]
        [headers.append(marker['name'].upper())
            for marker in test['marker']]
        [headers.append(disease['name'].upper())
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
            error = aP.doFullProcess(
                imageDetails[0], figsize=6, folder=fullPath, show=True)
            if error:
                print(
                    f'Ocurrió un error con el registro {registerNumber} del qr {qrCode}')
            originalImageName = 'original.png'
            fullPathOriginalImage = ''.join(
                [fullPath, qrCode, '-', str(registerNumber), '/', originalImageName])
            plt.imsave(fullPathOriginalImage,
                       BGR2RGB(imageDetails[0]['image']))
        else:
            print(
                f'El registro {registerNumber} del qr {qrCode} no tiene imágenes')
            pathNotFoundImage = ''.join(
                [fullPath, qrCode, '-', str(registerNumber)])
            makeFolder(pathNotFoundImage)
        testInfo.append(imagesExist)
        headers.append('Imágenes')
        allTestInfo.append(testInfo)
    testDataframe = pd.DataFrame(allTestInfo, columns=headers)
    testDataframe.set_index('Envío', inplace=True)
    testDataframes.append(testDataframe)
    seriesDataframe = pd.concat(testDataframes)

    # Resumen de información
    totalTests += len(seriesDataframe)
    totalValidTests += len(
        seriesDataframe[seriesDataframe['Valid'] == 'VALID'])
    totalInvalidTests += len(
        seriesDataframe[seriesDataframe['Valid'] == 'INVALID'])
    totalPositives += len(
        seriesDataframe[seriesDataframe['TB'] == 'POSITIVE'])
    totalNegatives += len(
        seriesDataframe[seriesDataframe['TB'] == 'NEGATIVE'])
    totalTestsWithImages += len(
        seriesDataframe[seriesDataframe['Imágenes'] == 'Sí'])
    totalTestsNoImages += len(
        seriesDataframe[seriesDataframe['Imágenes'] == 'No'])
    if startRow == 0:
        seriesDataframe.to_excel(writer, sheet_name='Sheet1',
                                 startrow=startRow)
    else:
        seriesDataframe.to_excel(writer, sheet_name='Sheet1',
                                 startrow=startRow, header=False)
    startRow += len(list(seriesDocuments)) + 2

# %% Agregar tabla de resumen
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
                         startrow=len(seriesDataframe) + 3,
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
