import datetime
from dateutil import tz
import json
from collections import defaultdict
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, './Helper Scripts')
import qrQuery


def getLocalTime(date):
    fromZone = tz.tzutc()
    date = date.replace(tzinfo=fromZone)
    localTz = tz.tzlocal()
    return date.astimezone(localTz)


# %%
URI2 = 'mongodb+srv://findOnlyReadUser:RojutuNHqy@clusterfinddemo-lwvvo.mongodb.net/datamap?retryWrites=true'
DB2 = qrQuery.cloudMongoConnection(URI2)
# %%
days = 3
todaysDate = datetime.datetime.now()
day = datetime.timedelta(days=days)
yesterdayDate = todaysDate-day
# %%
with open('./json/series.json', 'r') as file:
    seriesJson = json.load(file)['series']
prefixCodes = [serie['serie']['prefixCode'] for serie in seriesJson]
seriesNames = [serie['serie']['name'] for serie in seriesJson]
seriesDict = dict(zip(seriesNames, prefixCodes))
# %%
qr_documents_today = DB2.registerstotals.find(
    ).sort('_id', -1)
seriesCodes = defaultdict(set)
default_header = ['No. Imagen', 'Validez', 'Fecha']

for doc in qr_documents_today:
    qrCode = doc['qrCode']
    qrPrefix = qrCode[0:10]
    if qrPrefix in seriesDict.values():
        seriesCodes[qrPrefix].add(qrCode)

qrSerieInfo = {}
excelName = f'Reporte-{str(todaysDate.date())}-{days}-dias.xlsx'
writer = pd.ExcelWriter(excelName, engine='xlsxwriter')
startRow = 0
totalTests = 0
totalInvalidTests = 0
totalValidTests = 0
totalPositives = 0
totalNegatives = 0
for serie in seriesCodes.keys():
    qrDfs = []
    qrList = list(seriesCodes[serie])
    qrSerieInfo[serie] = {}
    for qrCode in qrList:
        listQrResults = []
        queryTests = {
            'qrCode': qrCode,
            'createdAt': {
                '$lt': todaysDate, '$gte': yesterdayDate
            }
        }
        testsWithQr = DB2.registerstotals.find(queryTests)
        print(list(testsWithQr))
        testsWithQrCount = DB2.registerstotals.count_documents(queryTests)
        if testsWithQrCount == 0:
            print('No hay registros de este QR'+qrCode)
            continue
        allTests = []
        for test in testsWithQr:
            imageNumber = test['count']
            validity = test['control'].upper()
            date = str(getLocalTime(test['createdAt']))[0:-10]
            testInfo = [imageNumber, validity, date]
            headers = ['Count', 'Valid', 'Date']
            [testInfo.append(marker['result'].upper())
             for marker in test['marker']]
            [testInfo.append(disease['result'].upper())
             for disease in test['disease']]
            [headers.append(marker['name'].upper())
             for marker in test['marker']]
            [headers.append(disease['name'].upper())
             for disease in test['disease']]
            allTests.append(testInfo)
        iterables = [[serie], [qrCode]*len(allTests)]
        index = pd.MultiIndex.from_product(iterables)
        tempDf = pd.DataFrame(allTests, index=index, columns=headers)
        tempDf.index.names = ['Serie', 'QR']
        qrDfs.append(tempDf)
    seriesDf = pd.concat(qrDfs)
    totalTests += len(seriesDf)
    totalValidTests += len(seriesDf[seriesDf['Valid'] == 'VALID'])
    totalInvalidTests += len(seriesDf[seriesDf['Valid'] == 'INVALID'])
    totalPositives += len(seriesDf[seriesDf['TB'] == 'POSITIVE'])
    totalNegatives += len(seriesDf[seriesDf['TB'] == 'NEGATIVE'])
    if startRow == 0:
        seriesDf.to_excel(writer, sheet_name='Sheet1',
                          startrow=startRow)
    else:
        seriesDf.to_excel(writer, sheet_name='Sheet1',
                          startrow=startRow, header=False)
    startRow += len(qrList) + 2

# %%
reportHeaders = [
    'Total Tests',
    'Total Valid Tests',
    'Total Invalid Tests',
    'Total Positives',
    'Total Negatives'
]
reportData = [
    totalTests,
    totalValidTests,
    totalInvalidTests,
    totalPositives,
    totalNegatives
]
reportDataframe = pd.DataFrame(reportData, index=reportHeaders, columns=['Cantidad'])
reportDataframe.to_excel(writer, sheet_name='Sheet1',startcol=len(headers)+5)
worksheet = writer.sheets['Sheet1']
worksheet
worksheet.set_column('A:A', 10, None)
worksheet.set_column('B:B', 18, None)
worksheet.set_column('E:E', 25, None)
worksheet.set_column('F:F', 18, None)
worksheet.set_column('G:G', 18, None)
worksheet.set_column('H:H', 18, None)
worksheet.set_column('I:I', 18, None)
worksheet.set_column('J:J', 18, None)
worksheet.set_column('N:N', 18, None)
writer.save()
