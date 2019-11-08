import datetime
import json
import os
import re
import sys
from collections import OrderedDict

import matplotlib
import pandas as pd
import pymongo
from matplotlib import pyplot as plt

from ImageFunctions.ImageProcessing.colorTransformations import BGR2RGB
from ImageFunctions.ReadImages import readImage as rI
from ImageFunctions.ShowProcess import showProcesses as sP
from QueryUtilities import qrQuery

scriptPath = os.path.dirname(os.path.abspath(__file__))
os.chdir(scriptPath)


# %%
URI2 = 'mongodb+srv://findOnlyReadUser:RojutuNHqy@clusterfinddemo-lwvvo.mongodb.net/datamap?retryWrites=true'
DB2 = qrQuery.cloudMongoConnection(URI2)

imagesURI = 'mongodb+srv://findOnlyReadUser:RojutuNHqy@clusterfinddemo-lwvvo.mongodb.net/datamap?retryWrites=true'
imagesDB = pymongo.MongoClient(URI2)['datamap']
# %%
todaysDate = datetime.datetime.now()
startDay = 0
finishDay = 1
startDate = todaysDate - datetime.timedelta(days=startDay)
finishDate = startDate - datetime.timedelta(days=finishDay-startDay)

# %%
with open('./json/series.json', 'r') as file:
    seriesJson = json.load(file)['series']
prefixCodes = [serie['serie']['prefixCode'] for serie in seriesJson]
seriesNames = [serie['serie']['name'] for serie in seriesJson]
seriesDict = dict(zip(seriesNames, prefixCodes))
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
# Búsqueda de fecha
dateQuery = {'createdAt': {
    '$lt': startDate, '$gte': finishDate
}}
# %%
seriesDataframes = []
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
        date = qrQuery.getLocalTime(test['createdAt']).ctime()
        generalInfo = [('Envío', key),
                       ('Código QR', qrCode),
                       ('Registro No.', registerNumber),
                       ('Validez', test['control'].upper()),
                       ('Fecha', date)]
        proteinInfo = [(marker['name'].upper(), marker['result'].upper())
                       for marker in test['marker']]
        diseaseInfo = [(disease['name'].upper(), disease['result'].upper())
                       for disease in test['disease']]
        imageTestQuery = {
            'filename': qrCode,
            'count': registerNumber
        }
        imageDetails = rI.customQuery(
            imagesDB.imagestotals, imageTestQuery)
        imagesExist = 'Sí' if len(imageDetails) > 0 else 'No'
        if len(imageDetails) > 0:
            fig = sP.showClusterProcess(
                imageDetails['file'], 12, 4, (7, 8), show=True, returnFig=True)
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
                       BGR2RGB(imageDetails['file']))
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
    seriesDataframe = pd.DataFrame(allTestInfo)
    seriesDataframes.append(seriesDataframe)

try:
    fullDataframe = pd.concat(seriesDataframes, sort=False)
except ValueError:
    print('No se encontró ningún registro en esta búsqueda')
    sys.exit(0)
fullDataframe.set_index('Envío', inplace=True)
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
startRow += seriesDocumentsCount + 2

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
