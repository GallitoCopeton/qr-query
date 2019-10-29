
import numpy as np
import cv2
import perspective as pPe
import sorts as srt

# Find Biggest Square


def resizeImg(img, width):
    height_res = img.shape[0]
    width_res = img.shape[1]
    scale = (height_res*width)/width_res
    return cv2.resize(img, (width, int(scale)), interpolation=cv2.INTER_AREA)


def BGR2gray(img):
    if(isinstance(img, list)):
        return img
    return cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

def BGR2RGB(img):
    return cv2.cvtColor(img, cv2.COLOR_BGR2RGB)


def gaussian(img, k, s):  # image and kernel size
    return cv2.GaussianBlur(img, (k, k), s)


def median(img, k):  # image and kernel size
    return cv2.medianBlur(img, k)


def binarize(img, th1, th2, inverse=False, mean=True):  # image and threshold max and min
    if(inverse):
        thBin = cv2.THRESH_BINARY_INV
    else:
        thBin = cv2.THRESH_BINARY

    if(mean):
        gray = cv2.adaptiveThreshold(img, 255, cv2.ADAPTIVE_THRESH_MEAN_C,
                                     thBin, th1, th2)
    else:
        gray = cv2.adaptiveThreshold(img, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                     thBin, th1, th2)
    return gray


def otsuBinarize(img, th1, th2, inverse=False, mean=True):
    return cv2.threshold(img, 0, 255, cv2.THRESH_BINARY+cv2.THRESH_OTSU)

# image kernel Gaussian, kernel Median, threshold max and min binarization


def contourBinarization(img, Gkernel, Mkernel, th1, th2, Gs=0, inverse=True, mean=True):
    if(isinstance(img, list)):
        return img
    gray = BGR2gray(img)
    gray = gaussian(gray, Gkernel, Gs)
    if(not mean):
        gray = median(gray, Mkernel)
    return binarize(gray, th1, th2, inverse, mean)

# image kernel Gaussian, kernel Median, threshold max and min binarization


def contourBinarizationOtsu(img, Gkernel, Mkernel, th1, th2, Gs=0, inverse=True, mean=True):
    gray = BGR2gray(img)
    gray = gaussian(gray, Gkernel, Gs)
    if(not mean):
        gray = median(gray, Mkernel)
    ret, th = otsuBinarize(gray, th1, th2, inverse, mean)
    return th


# Hierarchy contours, normally test in pos 5 and qr in pos 3 and 4
def findTreeContours(img, area=20000):
    listPoints = []
    _, cnts, hierarchy = cv2.findContours(
        img, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    for c in cnts:
        # http://docs.opencv.org/3.1.0/dd/d49/tutorial_py_contour_features.html
        epsilon = 0.1*cv2.arcLength(c, True)
        approx = cv2.approxPolyDP(c, epsilon, True)
        if(len(approx) == 4 and cv2.contourArea(approx) > area):
            listPoints.append(approx)
    return listPoints

# Find Test Squareprin


def findExternalContours(img, area=20000):
    listPoints = []
    _, cnts, hierarchy = cv2.findContours(
        img, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    for c in cnts:
        # http://docs.opencv.org/3.1.0/dd/d49/tutorial_py_contour_features.html
        epsilon = 0.1*cv2.arcLength(c, True)
        approx = cv2.approxPolyDP(c, epsilon, True)
        if(len(approx) == 4 and cv2.contourArea(approx) > area):
            listPoints.append(approx)
    return listPoints

# Blur detector


def isBlurry(img):
    laplacian = cv2.Laplacian(BGR2gray(img), cv2.CV_8U).max()
    blur = 1000 / (laplacian + 1)
    if blur < 6:
        return 0  # Not blurry
    else:
        return 1  # Blurry

# Histogram Equalization


def equalizeHistogram(img, claheEq=True):
    # Transform BGR to YUV
    img_yuv = cv2.cvtColor(img, cv2.COLOR_BGR2YUV)
    if claheEq:
        # CLAHE Object(Optional args).
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))

        # Equalize Y channel Histogram
        img_yuv[:, :, 0] = clahe.apply(img_yuv[:, :, 0])
    else:
        # Equalize Y channel Histogram
        img_yuv[:, :, 0] = cv2.equalizeHist(img_yuv[:, :, 0])
    return cv2.cvtColor(img_yuv, cv2.COLOR_YUV2BGR)


def clusterReconstruction(img, criteria, k, attempts):
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    Z = img.reshape((-1, 3))
    Z = np.float32(Z)
    ret, label, centers = cv2.kmeans(
        Z, k, None, criteria, attempts, cv2.KMEANS_RANDOM_CENTERS)
    centers = np.uint8(centers)
    clusterReconstruction = centers[label.flatten()]
    return clusterReconstruction.reshape(
        (img.shape))
