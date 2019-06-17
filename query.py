import imageReader as iR
import pymongo
import cv2
import os
import pandas as pd


def query_qr(qr):
    imgs = iR.readImageLocalV2(qr, path)
    if len(imgs) < 1:
        print('No existen imágenes con ese QR!\n')
    else:
        print('Existen {} imágenes'.format(len(imgs)))
        iR.multiDisp(imgs, rows=3, cols=3)

    listQrs = []
    column_df = ['No. Imagen', 'QR', 'Validez']
    pruebas = list(db2.registerstotals.find({'qrCode': qr}))
    if len(list(pruebas)) > 0:
        for doc in pruebas:
            resultDict = dict()
            resultDict['QR'] = doc['qrCode']
            resultDict['Validez'] = doc['control']
            resultDict['No. Imagen'] = doc['count']
            namesProteins = []
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
        pruebas = list(db1.registerstotals.find({'qrCode': qr}))
        if len(list(pruebas)) > 0:
            for doc in pruebas:
                resultDict = dict()
                resultDict['QR'] = doc['qrCode']
                resultDict['Validez'] = doc['control']
                resultDict['No. Imagen'] = doc['count']
                namesProteins = []
                for marker in doc['marker']:
                    namesProteins.append(marker['name'])
                    header = column_df+namesProteins
                    resultDict[marker['name']] = marker['result']
                listQrs.append(resultDict)
            result_df = pd.DataFrame.from_dict(listQrs)
            result_df = result_df[header]
            result_df = result_df.sort_values(
                by=['No. Imagen'], ascending=True)
            print(result_df.to_string(index=False))
        else:
            print('No existe información de ese QR!')
