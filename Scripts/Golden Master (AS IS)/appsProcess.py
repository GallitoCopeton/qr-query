import cv2
import numpy as np
from matplotlib import pyplot as plt

import indAnalysis as inA
import perspective as pPe
import preProcessing as pP
import sorts as srt

mask = inA.readMask(url='./assets/mask_inv.png')


def getTestSite(image):
    testResized = pP.resizeImg(image, 728)
    testBin = pP.contourBinarization(
        testResized, 3, 7, 85, 2, inverse=True, mean=False)
    cardContours = pP.findTreeContours(testBin)
    for contour in cardContours:
        orderedContour = srt.sortPoints(contour)
        cardBin = pPe.perspectiveTransform(
            testBin, orderedContour, -5, binary=True)
        qrAndTestSiteContours = pP.findExternalContours(cardBin)
        if len(qrAndTestSiteContours) == 2:
            card = pPe.perspectiveTransform(
                testResized, orderedContour, -5)
            contour1, contour2 = qrAndTestSiteContours
            area1 = cv2.contourArea(contour1)
            area2 = cv2.contourArea(contour2)
            if area1 > area2:
                testSiteContours = contour1
                qrSiteContours = contour2
            else:
                testSiteContours = contour2
                qrSiteContours = contour1
            testSiteContoursOrdered = srt.sortPoints(testSiteContours)
            qrSiteContoursOrdered = srt.sortPoints(qrSiteContours)
            if qrSiteContoursOrdered[0][0][0] > testSiteContoursOrdered[0][0][0] and qrSiteContoursOrdered[2][0][1] > testSiteContoursOrdered[2][0][1]:
                testSite = pPe.perspectiveTransform(
                    card, testSiteContoursOrdered, offset=5)
                testSiteEq = pP.equalizeHistogram(testSite)
    return testSite, testSiteEq



def getMarkers(testSite, testSiteEq):
    height, width = testSite.shape[:2]
    markersContoursEq = pP.findTreeContours(pP.contourBinarization(
        testSiteEq, 3, 7, 85, 2, mean=False), 115000)
    if len(markersContoursEq) == 5 or len(markersContoursEq) == 7:
        markersContoursEq = markersContoursEq[1:]
    markersEq = []
    markers = []
    if(len(markersContoursEq) == 4 or len(markersContoursEq) == 6):
        srt.sortTests(markersContoursEq)
        for i, markerContour in enumerate(markersContoursEq):
            # Equalizado
            markerEq = pPe.getIndTest(testSiteEq, markerContour)
            markersEq.append(markerEq)
            # No equalizado
            marker = pPe.getIndTest(testSite, markerContour)
            markers.append(marker)
    markersEq = inA.resizeAll(markersEq)
    markers = inA.resizeAll(markers)
    return markers, markersEq


def markerClusterProcessing(markers):
    criteria = (cv2.TERM_CRITERIA_MAX_ITER, 10000, 1000)
    k = 4
    attempts = 40
    markersRecon = []
    markersBin = []
    markersTrans = []
    markersNot = []
    for marker in markers:
        # CLUSTER (Loki) ==> START
        clusterRecon = pP.clusterReconstruction(marker, criteria, k, attempts)
        clusterGray = cv2.cvtColor(clusterRecon, cv2.COLOR_BGR2GRAY)
        t = inA.getBackgroundColor(clusterGray, percentage=.25)
        _, clusterBin = cv2.threshold(clusterGray, t, 255, cv2.THRESH_BINARY)
        clusterMasked = inA.andOperation(clusterBin, mask)
        dilateKernel = cv2.getStructuringElement(cv2.MORPH_CROSS, (2, 2))
        openKernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2, 2))
        erodeKernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2, 2))
        clusterTrans = cv2.morphologyEx(
            clusterMasked, cv2.MORPH_ERODE, erodeKernel)
        clusterTrans = cv2.morphologyEx(
            clusterTrans, cv2.MORPH_DILATE, dilateKernel)
        clusterTrans = cv2.morphologyEx(
            clusterTrans, cv2.MORPH_OPEN, openKernel)
        clusterNot = cv2.bitwise_not(clusterTrans)
        # CLUSTER (Loki) ==> FINISH
        markersRecon.append(clusterRecon)
        markersBin.append(clusterBin)
        markersTrans.append(clusterTrans)
        markersNot.append(clusterNot)
    return [markersRecon, markersBin, markersTrans, markersNot]


def markerDirectProcessing(markersEq):
    markersBin = []
    markersTrans = []
    markersNot = []
    for markerEq in markersEq:
        # PRODUCTION AREAS (Xplora) ==> START
        markerBin = pP.contourBinarizationOtsu(
            markerEq, 3, 3, 45, 3, Gs=0, inverse=False, mean=True)
        markerMasked = inA.andOperation(markerBin, mask)
        markerTrans = inA.erosionDilation(markerMasked, 3)
        markerNot = cv2.bitwise_not(markerTrans)
        # PRODUCTION AREAS (Xplora) ==> FINISH
        markersBin.append(markerBin)
        markersTrans.append(markerTrans)
        markersNot.append(markerNot)
    return [markersEq, markersBin, markersTrans, markersNot]


def showDirectProcess(card: np.ndarray, markers: list, markerProcess: list):
    markersEq, markersBin, markersTrans, markersNot = markerProcess
    iList = np.arange(0, len(markers), 1)
    for (marker, markerEq, markerBin, markerTrans, markerNot, i) in zip(markers, markersEq, markersBin, markersTrans, markersNot, iList):
        # Plots
        fig = plt.figure(figsize=(12, 12), constrained_layout=True)
        gs = fig.add_gridspec(5, 4)
        gridSpecTupple = gs.get_geometry()
        halfHeight = int(gridSpecTupple[0]/2)
        halfWidth = int(gridSpecTupple[1]/2)
        fig.set_facecolor((0.6, 0.6, 0.6))

        plotFullCard = fig.add_subplot(gs[0:halfHeight+1, 0:halfWidth])
        plotMarker = fig.add_subplot(gs[0:halfHeight, 1-halfHeight:])
        plotMarkerEq = fig.add_subplot(gs[4, 0])
        plotMarkerBin = fig.add_subplot(gs[4, 1])
        plotMarkerTrans = fig.add_subplot(gs[4, 2])
        plotMarkerBlobs = fig.add_subplot(gs[4, 3])

        plotFullCard.set_title('Original image')
        plotMarker.set_title('Marker {}'.format(i+1))
        plotMarkerEq.set_title('Equalization')
        plotMarkerBin.set_title('Binarized')
        plotMarkerTrans.set_title('Morph')
        plotMarkerBlobs.set_title('Blobs')

        plotFullCard.set_axis_off()
        plotMarker.set_axis_off()
        plotMarkerEq.set_axis_off()
        plotMarkerBin.set_axis_off()
        plotMarkerTrans.set_axis_off()
        plotMarkerBlobs.set_axis_off()

        plotFullCard.imshow(card)
        plotMarker.imshow(marker)
        plotMarkerEq.imshow(markerEq)
        plotMarkerBin.imshow(markerBin, 'gray')
        plotMarkerTrans.imshow(markerTrans, 'gray')
        plotMarkerBlobs.imshow(markerNot, 'gray')
        plt.show()
        plt.close(fig)


def showClusterProcess(card: np.ndarray, markers: list, markerClusterProcess: list):
    markersRecon, markersBin, markersTrans, markersNot = markerClusterProcess
    iList = np.arange(0, len(markers), 1)
    for (marker, markerRecon, markerBin, markerTrans, markerNot, i) in zip(markers, markersRecon, markersBin, markersTrans, markersNot, iList):
        # Plots
        fig = plt.figure(figsize=(12, 12), constrained_layout=True)
        gs = fig.add_gridspec(5, 4)
        gridSpecTupple = gs.get_geometry()
        halfHeight = int(gridSpecTupple[0]/2)
        halfWidth = int(gridSpecTupple[1]/2)
        fig.set_facecolor((0.6, 0.6, 0.6))

        plotFullCard = fig.add_subplot(gs[0:halfHeight+1, 0:halfWidth])
        plotMarker = fig.add_subplot(gs[0:halfHeight, 1-halfHeight:])
        plotMarkerEq = fig.add_subplot(gs[4, 0])
        plotMarkerBin = fig.add_subplot(gs[4, 1])
        plotMarkerTrans = fig.add_subplot(gs[4, 2])
        plotMarkerBlobs = fig.add_subplot(gs[4, 3])

        plotFullCard.set_title('Original image')
        plotMarker.set_title('Marker {}'.format(i+1))
        plotMarkerEq.set_title('Reconstruction')
        plotMarkerBin.set_title('Binarized')
        plotMarkerTrans.set_title('Morph')
        plotMarkerBlobs.set_title('Blobs')

        plotFullCard.set_axis_off()
        plotMarker.set_axis_off()
        plotMarkerEq.set_axis_off()
        plotMarkerBin.set_axis_off()
        plotMarkerTrans.set_axis_off()
        plotMarkerBlobs.set_axis_off()

        plotFullCard.imshow(card)
        plotMarker.imshow(marker)
        plotMarkerEq.imshow(markerRecon)
        plotMarkerBin.imshow(markerBin, 'gray')
        plotMarkerTrans.imshow(markerTrans, 'gray')
        plotMarkerBlobs.imshow(markerNot, 'gray')
        plt.show()
        plt.close(fig)


def showBothProcesses(card: np.ndarray, markers: list, markerDirectProcess: list, markerClusterProcess: list, figsize=5, save=False, show=True, folderName='./'):
    markersEq, markersBin, markersTrans, markersNot = markerDirectProcess
    clustersRecon, clustersBin, clustersTrans, clustersNot = markerClusterProcess
    iList = np.arange(0, len(markers), 1)
    for (marker, clusterRecon, clusterBin, clusterTrans, clusterNot, markerEq, markerBin, markerTrans, markerNot, i) in zip(markers, clustersRecon, clustersBin, clustersTrans, clustersNot, markersEq, markersBin, markersTrans, markersNot, iList):
        fig = plt.figure(figsize=(figsize,figsize), constrained_layout=True)
        gs = fig.add_gridspec(6, 4)
        gridSpecTupple = gs.get_geometry()
        halfHeight = int(gridSpecTupple[0]/2)
        halfWidth = int(gridSpecTupple[1]/2)
        fig.set_facecolor((0.6, 0.6, 0.6))

        plotFullCard = fig.add_subplot(gs[0:halfHeight+1, 0:halfWidth])
        plotMarker = fig.add_subplot(gs[0:halfHeight, 1-halfHeight:])
        plotClusterRecon = fig.add_subplot(gs[4, 0])
        plotClusterBin = fig.add_subplot(gs[4, 1])
        plotClusterTrans = fig.add_subplot(gs[4, 2])
        plotClusterBlobs = fig.add_subplot(gs[4, 3])
        plotMarkerEq = fig.add_subplot(gs[5, 0])
        plotMarkerBin = fig.add_subplot(gs[5, 1])
        plotMarkerTrans = fig.add_subplot(gs[5, 2])
        plotMarkerBlobs = fig.add_subplot(gs[5, 3])

        plotFullCard.set_title('Original image')
        plotMarker.set_title('Marker {}'.format(i+1))
        plotClusterRecon.set_title('Equalization')
        plotClusterBin.set_title('Binarized')
        plotClusterTrans.set_title('Morph')
        plotClusterBlobs.set_title('Blobs')
        plotMarkerEq.set_title('Reconstruction')
        plotMarkerBin.set_title('Binarized')
        plotMarkerTrans.set_title('Morph')
        plotMarkerBlobs.set_title('Blobs')
            
        plotFullCard.set_axis_off()
        plotMarker.set_axis_off()
        plotClusterRecon.set_axis_off()
        plotClusterBin.set_axis_off()
        plotClusterTrans.set_axis_off()
        plotClusterBlobs.set_axis_off()
        plotMarkerEq.set_axis_off()
        plotMarkerBin.set_axis_off()
        plotMarkerTrans.set_axis_off()
        plotMarkerBlobs.set_axis_off()
        
        if show:
            plotFullCard.imshow(card)
            plotMarker.imshow(marker)
            plotClusterRecon.imshow(clusterRecon)
            plotClusterBin.imshow(clusterBin, 'gray')
            plotClusterTrans.imshow(clusterTrans, 'gray')
            plotClusterBlobs.imshow(clusterNot, 'gray')
            plotMarkerEq.imshow(markerEq)
            plotMarkerBin.imshow(markerBin, 'gray')
            plotMarkerTrans.imshow(markerTrans, 'gray')
            plotMarkerBlobs.imshow(markerNot, 'gray')
            plt.show()
        if save:
            fig.savefig(folderName+str(i)+'.png')
        plt.close(fig)
