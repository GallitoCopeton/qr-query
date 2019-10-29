import numpy as np
import cv2
import sorts as srt

def perspectiveTransform(img, points, offset, binary = False):
    if(binary):
        height,width = img.shape
    else:
        height,width,ch = img.shape
    #print("Width: " + str(width) + " Height: " + str(height))
    #X and Y coordinates of every point with offset
    pts1 = getPointsPerspective(points, offset)
    pts2 = np.float32([[0,0],[width, 0], [0, height], [width, height]])
    M = cv2.getPerspectiveTransform(pts1,pts2)
    dst = cv2.warpPerspective(img, M, (width, height))
    return dst

#http://docs.opencv.org/trunk/da/d6e/tutorial_py_geometric_transformations.html
def getPointsPerspective(points, offset):
    return np.float32([[points[0][0][0] - offset, points[0][0][1] - offset],
            [points[1][0][0] + offset, points[1][0][1] - offset],
            [points[2][0][0] - offset, points[2][0][1] + offset],
            [points[3][0][0] + offset, points[3][0][1] + offset]])

def getIndTest(img, cntInd):
    return perspectiveTransform(img, srt.sortPoints(cntInd), 5)

def getTestSquare(img, externalContours, binary = False):
    maxCnt = max(externalContours, key = cv2.contourArea)
    return perspectiveTransform(img, srt.sortPoints(maxCnt), 5, binary)

