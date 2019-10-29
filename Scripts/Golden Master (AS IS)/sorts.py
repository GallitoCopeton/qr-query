import operator

def sortPointsContours(cnt):
    sortedList = []
    for c in cnt: 
        #print("from: " + str(c))
        sortedList.append(sortPoints(c))
    #print("to: " + str(sortedList))
    return sortedList

def sortPoints(p): #Sort list left to right, up to bottom
    #order using y
    p = sorted(p, key=lambda x: x[0][1])
    #If x1 > x2, x1 is right 
    if(p[0][0][0] > p[1][0][0]): #(INDEX j = point, k = always 0, l = coordinate, x = 0, y = 1)
        swap(p, 0, 1)
    if(p[2][0][0] > p[3][0][0]):
        swap(p, 2, 3)
    return p

def printPoints(p):
    for x in p:
        print(x)
        
def swap(list_point, a, b):
    tempA = list_point[a].copy()
    list_point[a] = list_point[b].copy()
    list_point[b] = tempA

## Individual Tests
def sortTests(cntsTests):
    sortedList = []
    sortPointsContours(cntsTests)
    for i,c in enumerate(cntsTests):
        #Value of x first point
        if(operator.mod(i,2) == 0 and (cntsTests[i][0][0][0] < cntsTests[i+1][0][0][0])): 
            swap(cntsTests, i, i+1)
        #sortedList.insert(0, c)
    return reverseListTests4Squares(cntsTests)

def reverseListTests(cntsTests):
    swap(cntsTests, 0, 5)
    swap(cntsTests, 1, 4)
    swap(cntsTests, 2, 3)
    
def reverseListTests4Squares(cntsTests):
    swap(cntsTests, 1, 2)
    swap(cntsTests, 0, 3)