import os
import appsProcess as aP

import cv2

def makeFolder(folderName):
    if not os.path.isdir(folderName):
        os.mkdir(folderName)
        
def doFullProcess(image, figsize=9, save=True, show=False, folder='./'):

    
    folderName = ''.join([folder, '/', image['qr'], '-', str(image['count']), '/'])
    makeFolder(folderName)
    testFull = cv2.cvtColor(image['image'], cv2.COLOR_BGR2RGB)
    try:
        testSite, testSiteEq = aP.getTestSite(testFull)
    except:
        print('Problem with test site')
        return True
    try:
        markers, markersEq = aP.getMarkers(testSite, testSiteEq)
    except:
        print('Problem with markers')
        return True
    markerClusterProcess = aP.markerClusterProcessing(markers)
    markerDirectProcess = aP.markerDirectProcessing(markersEq)
    aP.showBothProcesses(
        testSite, markers, markerClusterProcess, markerDirectProcess, figsize, save, show, folderName)
