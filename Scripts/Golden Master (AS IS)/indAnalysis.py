import json
import math

import cv2
import numpy as np
import pandas as pd
from matplotlib import pyplot as plt

import preProcessing as pP
import readImage as rI


def readMask(url="../../Imagenes/mask_inv.png", size=90):
    mask = rI.readLocal(url)
    mask = resizeFixed(mask, size)
    mask = pP.contourBinarization(mask, 3, 3, 75, 4, inverse=False, mean=True)
    return mask


def resizeFixed(img, size=90):
    return cv2.resize(img, (size, size), interpolation=cv2.INTER_LINEAR)


def resizeAll(listImgs, size=90):
    if(isinstance(listImgs, str)):  # If string received
        return listImgs
    listResizedImgs = []
    for i in listImgs:
        listResizedImgs.append(resizeFixed(i, size))
    return listResizedImgs


def andOperation(img, mask):
    return cv2.bitwise_and(img, img, mask=mask)

# http://docs.opencv.org/3.0-beta/doc/py_tutorials/py_imgproc/py_morphological_ops/py_morphological_ops.html


def erosionDilation(imgBin, kSize):
    kernel = np.ones((kSize, kSize), np.uint8)
    erosion = cv2.erode(imgBin, kernel, iterations=1)
    return cv2.dilate(erosion, kernel, iterations=2)


def closing(imgBin, kSize):
    kernel = np.ones((kSize, kSize), np.uint8)
    erosion = cv2.erode(imgBin, kernel, iterations=1)
    return cv2.dilate(erosion, kernel, iterations=1)


def opening(imgBin, kSize):
    kernel = np.ones((kSize, kSize), np.uint8)
    dilate = cv2.dilate(imgBin, kernel, iterations=1)
    return cv2.erode(dilate, kernel, iterations=1)


def colorSegmentation(img, statsColor):  # Stats Hue and Saturation

    # Invert image BGR
    imgBGR_inv = ~img

    # Transform input inverse image to HSV
    imgHSV_inv = cv2.cvtColor(imgBGR_inv, cv2.COLOR_BGR2HSV)

    # Define boundaries for inRange
    cyan_cluster_mean = statsColor['H_mean']  # Mean
    cmean = cyan_cluster_mean
    cyan_cluster_std = statsColor['H_std']  # Standard Deviation
    # MPercentile 15
    non_cyan_exclude_saturation = statsColor['S_25_percentile']
    if(non_cyan_exclude_saturation < 0):
        non_cyan_exclude_saturation = 0  # Zero exception
    exc_sat_low = non_cyan_exclude_saturation
    non_cyan_exclude_value = 255
    exc_val_high = non_cyan_exclude_value
    percentage_of_cyan = 65
    cyan_cluster_dev = (3 * cyan_cluster_std / 100) * percentage_of_cyan
    cdev = cyan_cluster_dev

    # Make inRange operation
    mask3 = cv2.inRange(imgHSV_inv, np.array(
        [cmean-cdev, exc_sat_low, 10]), np.array([cmean+cdev, 255, exc_val_high]))

    # Closing operation
    mask3 = closing(mask3, 3)

    # Opening operation
    mask3 = opening(mask3, 3)

    # And operation between mask and img
    andOp = andOperation(img, mask3)
    ret, andOpbin = cv2.threshold(
        pP.BGR2gray(andOp), 1, 255, cv2.THRESH_BINARY)
    countPixels = cv2.countNonZero(andOpbin) / 50
    return (andOp, andOpbin, countPixels)  # color, binary, count

# Get control statistics


def controlStats(img, maskPath="../../Imagenes/mask3.png", maskSize=90, diab=False):
    stats = dict()
    mask3 = readMask(maskPath, size=maskSize)
    control = ~(andOperation(img, mask3))
    controlHSV = cv2.cvtColor(control, cv2.COLOR_BGR2HSV)

    h, s, v = cv2.split(controlHSV)
    if(diab):
        h = h.flatten()[(h.flatten() >= 5) & (h.flatten() <= 250)]
    else:
        h = h.flatten()[(h.flatten() >= 50) & (h.flatten() <= 150)]

    s = s.flatten()[s.flatten() >= 15]
    v = v.flatten()[v.flatten() >= 10]
    # print("H: " + str(len(h)) + ", S: " + str(len(s)) + ", V: " + str(len(v)))
    channels = ['H', 'S', 'V']
    chVal = [h, s, v]
    for i, ch in enumerate(channels):
        stats[ch + '_mean'] = np.mean(chVal[i])
        stats[ch + '_median'] = np.median(chVal[i])
        stats[ch + '_std'] = np.std(chVal[i])
        stats[ch + '_25_percentile'] = np.percentile(chVal[i], 25)
    return stats

# Get control statistics


def grayControlStats(img, maskPath="../../Imagenes/mask3.png", maskSize=90):
    img = pP.BGR2gray(img)
    stats = dict()
    mask3 = readMask(maskPath, size=maskSize)
    control = andOperation(img, mask3)
    # c = control.flatten()[(control.flatten() >= 5) & (control.flatten() <= 255)]
    c = control.flatten()[(control.flatten() >= 15)
                          & (control.flatten() <= 235)]
    stats['G_mean'] = np.mean(c)
    stats['G_median'] = np.median(c)
    stats['G_std'] = np.std(c)
    stats['G_25_percentile'] = np.percentile(c, 25)
    return stats


def colorStatsXMarker(img):
    statsMeasures = ['Mean', 'Median', 'Std', 'Percentile25']
    statsXMarker = dict()
    statsH, statsS = controlStats(img)
    statsH, statsS = controlStats(img)
    for i, h in enumerate(statsH):
        statsXMarker['H_' + statsMeasures[i]] = h
        statsXMarker['S_' + statsMeasures[i]] = statsS[i]
    return statsXMarker

# https://www.learnopencv.com/blob-detection-using-opencv-python-c/


def blobDetect(img):
    # Setup SimpleBlobDetector parameters.
    params = cv2.SimpleBlobDetector_Params()

    # Change thresholds
    params.thresholdStep = 10
    params.minThreshold = 50
    params.maxThreshold = 220

    # Change repeatability
    params.minRepeatability = 2

    # Distance between blobs
    params.minDistBetweenBlobs = 10

    # Filter by Area.
    params.filterByArea = True
    params.minArea = 25
    params.maxArea = 5000

    # Filter by color
    params.filterByColor = True
    params.blobColor = 0

    # Filter by Circularity
    params.filterByCircularity = False
    params.minCircularity = 8.0000001192092896e-001
    params.maxCircularity = 3.4028234663852886e+038

    # Filter by Convexity
    params.filterByConvexity = False
    params.minConvexity = 0.05
    params.maxConvexity = 1.5

    # Filter by Inertia
    params.filterByInertia = True
    params.minInertiaRatio = 0.01
    params.maxInertiaRatio = 3.4028234663852886e+038

    # Create a detector with the parameters
    detector = cv2.SimpleBlobDetector_create(params)

    # Keypoints
    return detector.detect(img)


def drawBlobs(img, keypoints):
    return cv2.drawKeypoints(img, keypoints, np.array([]),
                             (0, 0, 255), cv2.DRAW_MATCHES_FLAGS_DRAW_RICH_KEYPOINTS)


def isEmpty(imgBinary):
    rows, cols = imgBinary.shape
    totalPx = rows * cols
    whitePx = cv2.countNonZero(imgBinary)
    percentage = ((totalPx - whitePx) * 100) / totalPx
    return (percentage < 35)


def blobAnalysis(imgBin, keypoints):
    if(not isEmpty(imgBin)):
        if(len(keypoints) > 2):
            return 'P'
        if(len(keypoints) < 2):
            return 'N'
        else:
            return 'I'
    else:
        return 'E'


def areaAnalysis(imgBin, keypoints, area, nmarker):
    # ths = [26,30,36,26,35,22]
    # ths = [45,48,47,36,35,30]
    ths = [45, 48, 45, 37, 35, 35]
    if(not isEmpty(imgBin)):
        # Un sólo blob siempre es negativo
        if (area < ths[nmarker]) or (len(keypoints) < 2):
            return 'N'
        else:
            return 'P'
    else:
        return 'E'

# Deprecate


def areaAnalysis2(imgBin, blobs, area, markerName):
    thresholds = {
        'ESAT6': 45,
        'CFP10': 48,
        'RV1681': 45,
        'P24': 37,
        'GP120': 35,
        'Control': 35,
    }
    # Un sólo blob siempre es negativo
    if len(blobs) <= 1:
        return 'N'
    else:
        if area < thresholds[markerName]:
            return 'N'
        else:
            return 'P'


def whitePixelsTotal(image):
    return cv2.countNonZero(image)


def quadrantAreaAnalysis(images):
    whitePixelsQuadrant = {}
    if len(images) > 4:
        images = imageQuadrantSplit(images)
    for i, image in enumerate(images):
        whitePixels = cv2.countNonZero(image)
        whitePixelsQuadrant['areaQ{}'.format(i+1)] = whitePixels
    return whitePixelsQuadrant


def quadrantBlobAnalisys(images, bgrImages):
    measurementsDict = {
        'blobs': 0
    }
    if len(images) > 4:
        images = imageQuadrantSplit(images)
        bgrImages = imageQuadrantSplit(bgrImages)
    kernelOpen = np.ones((3, 3), np.uint8)

    for i, image in enumerate(images):
        # Data reset
        distance = 0
        quadrantArea = 0
        quadrantPerimeter = 0
        verticalDiag = 0
        horizontalDiag = 0
        # Open it once more to reduce noisy blobs
        imageOpen = cv2.morphologyEx(
            image, cv2.MORPH_OPEN, kernelOpen)
        # Find contours and sort by the biggest
        contours, hierarchy = cv2.findContours(
            imageOpen, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
        # If you find a single contour and it has more than 4 coordinates
        if len(contours) > 0 and len(contours[0]) > 4:
            contours = max(contours, key=cv2.contourArea)
            # Data extraction preparation => START

            # Max and min points
            extLeft = tuple(contours[contours[:, :, 0].argmin()][0])
            extRight = tuple(contours[contours[:, :, 0].argmax()][0])
            extTop = tuple(contours[contours[:, :, 1].argmin()][0])
            extBot = tuple(contours[contours[:, :, 1].argmax()][0])
            # Extract centroid of blob
            sideOfImage = image.shape[0]
            moments = cv2.moments(contours)
            centroidX = int(moments['m10']/moments['m00'])
            centroidY = int(moments['m01']/moments['m00'])
            if i == 0:
                fullImageCenterX = sideOfImage
                fullImageCenterY = sideOfImage
            elif i == 1:
                fullImageCenterX = 0
                fullImageCenterY = sideOfImage
            elif i == 2:
                fullImageCenterX = sideOfImage
                fullImageCenterY = 0
            elif i == 3:
                fullImageCenterX = 0
                fullImageCenterY = 0

            # Data extraction preparation => FINISH
            # Data extraction => START

            # Distance between blob and center of image in pixels
            distance = math.sqrt(
                (centroidX - fullImageCenterX)**2 + (centroidY - fullImageCenterY)**2)
            # Length of vertical diagonal in pixels
            verticalDiag = math.sqrt(
                (extBot[0] - extTop[0])**2 + (extBot[1] - extTop[1])**2)
            # Length of vertical diagonal in pixels
            horizontalDiag = math.sqrt(
                (extLeft[0] - extRight[0])**2 + (extLeft[1] - extRight[1])**2)
            quadrantArea = cv2.contourArea(contours)
            quadrantPerimeter = cv2.arcLength(
                contours, closed=True)

            # Data extraction => FINISH
            # Data storage
            measurementsDict['distanceQ{}'.format(i+1)] = distance
            measurementsDict['areaQ{}'.format(i+1)] = quadrantArea
            measurementsDict['perimeterQ{}'.format(i+1)] = quadrantPerimeter
            measurementsDict['verticalDiagQ{}'.format(i+1)] = verticalDiag
            measurementsDict['horizontalDiagQ{}'.format(i+1)] = horizontalDiag
            measurementsDict['blobs'] += 1
        # If the contour condition was not met, make every value of the dict 0
        else:
            measurementsDict['distanceQ{}'.format(i+1)] = distance
            measurementsDict['areaQ{}'.format(i+1)] = quadrantArea
            measurementsDict['perimeterQ{}'.format(i+1)] = quadrantPerimeter
            measurementsDict['verticalDiagQ{}'.format(i+1)] = verticalDiag
            measurementsDict['horizontalDiagQ{}'.format(i+1)] = horizontalDiag
            measurementsDict['blobs'] += 0
    return measurementsDict


def tbDiagnostic(xmarker1, xmarker2, xmarker3):  # ESAT6, CFP10, RV1681
    if (xmarker1 == 'P' or xmarker2 == 'P' or xmarker3 == 'P'):
        return 'P'
    elif(xmarker1 == 'N' and xmarker2 == 'N' and xmarker3 == 'N'):
        return 'N'
    else:
        return 'I'


def areaEstimation(keypoints):
    areaTotal = 0
    for kp in keypoints:
        areaTotal += kp.size
    return areaTotal


def createNestedDataframes(markers, stats, data):
    dataFrames = []
    for i, marker in enumerate(markers):
        markerName = []
        for stat in stats:
            markerName.append(marker)
        arrays = [markerName, stats]
        tuples = list(zip(*arrays))
        index = pd.MultiIndex.from_tuples(tuples)
        if data:
            dataFrames.append(pd.DataFrame(data[:, i:i+2], columns=index))
        else:
            dataFrames.append(pd.DataFrame(columns=index))
        i += 3
    return dataFrames


def createQuadrantDataframes(markers, quadrants, stats, data):
    dataFrames = []
    requiredLength = len(quadrants) * len(stats)
    for i, marker in enumerate(markers):
        quadrantsArray = np.array(
            quadrants*(int(requiredLength/len(quadrants))))
        quadrantsArray.sort()
        statsArray = np.array(stats*(int(requiredLength/len(stats))))

        arrays = [quadrantsArray, statsArray]
        tuples = list(zip(*arrays))
        index = pd.MultiIndex.from_tuples(tuples)
        if data is not None:
            dataFrames.append(pd.DataFrame(
                data[i:i+requiredLength, :], columns=index))
        else:
            dataFrames.append(pd.DataFrame(columns=index))
        i += requiredLength + 1
    return dataFrames


def imageQuadrantSplit(img):
    halfWidth = int(img.shape[0]/2)
    halfHeight = int(img.shape[1]/2)
    if len(img.shape) == 3:
        firstQuadrant = img[0:halfWidth, 0:halfHeight, :]
        secondQuadrant = img[0:halfWidth, halfHeight:, :]
        thirdQuadrant = img[halfWidth:, 0:halfHeight, :]
        fourthQuadrant = img[halfWidth:, halfHeight:, :]
    else:
        firstQuadrant = img[0:halfWidth, 0:halfHeight]
        thirdQuadrant = img[halfWidth:, 0:halfHeight]
        secondQuadrant = img[0:halfWidth, halfHeight:]
        fourthQuadrant = img[halfWidth:, halfHeight:]
    return [firstQuadrant, secondQuadrant, thirdQuadrant, fourthQuadrant]


def hasConvexDefect(binaryMarker):
    hasDefect = False
    kernel = np.ones((5, 5), np.uint8)
    openMarker = cv2.morphologyEx(binaryMarker, cv2.MORPH_OPEN, kernel)
    dilatedMarker = cv2.morphologyEx(
        openMarker, cv2.MORPH_DILATE, kernel)
    distTransMarker = cv2.distanceTransform(
        dilatedMarker, cv2.DIST_L2, 5)
    _, sureForegroundMarker = cv2.threshold(
        distTransMarker, .19*distTransMarker.max(), 255, cv2.THRESH_BINARY)
    sureForegroundMarker = sureForegroundMarker.astype(np.uint8)
    xContours, _ = cv2.findContours(
        sureForegroundMarker, 2, cv2.CHAIN_APPROX_SIMPLE)
    xContour = max(xContours, key=cv2.contourArea)
    hull = cv2.convexHull(xContour, returnPoints=False)
    defects = cv2.convexityDefects(xContour, hull)
    def sortFunc(defect): return defect[0][3]
    defects = sorted(defects, key=sortFunc, reverse=True)[0:4]
    points = []
    for i in range(len(defects)):
        s, e, f, d = defects[i][0]
        far = tuple(xContour[f][0])
        points.append(far)
    sortedPoints = sorted(points, key=lambda x: x[0])
    up, right, left, down = sortedPoints
    vertDist = math.sqrt((up[0]-down[0])**2 + (up[1]-down[1])**2)
    horDist = math.sqrt((right[0]-left[0])**2 + (right[1]-left[1])**2)
    distances = [vertDist, horDist]
    distanceDifference = max(distances)-min(distances)
    if distanceDifference > 2.5:
        hasDefect = True
        return hasDefect, distanceDifference
    else:
        return hasDefect, distanceDifference

def getBackgroundColor(markerGray, percentage):
    h,w = markerGray.shape[:2]
    percentage = int(percentage*h)
    kernel = 3
    corner1 = markerGray[percentage, percentage]
    corner2 = markerGray[percentage, h-percentage]
    corner3 = markerGray[h-percentage, percentage]
    corner4 = markerGray[h-percentage, h-percentage]
    bias = .1
    return np.array([corner1+(corner1*bias), corner2+(corner2*bias), corner3+(corner3*bias), corner4+(corner4*bias)]).mean()