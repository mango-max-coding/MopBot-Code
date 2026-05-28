#upload to Raspberry Pi itself

import serial
import time
import threading
import math
import statistics
from copy import deepcopy
import matplotlib.pyplot as plt
from sys import exit as termin

# Configure the serial connection (change port and baudrate as needed)
ser = serial.Serial(
        port='/dev/ttyUSB0', # Replace with the correct port name
        baudrate=9600
)

# Wait a moment for the connection to establish and clear the buffer
time.sleep(0.1)
ser.flushInput()

prevScore = "n"
prevLeft = 0

print("Serial port opened. Reading data...")


def findDist(p1,p2):
  return math.sqrt((p2[0] - p1[0])**2 + (p2[1] - p1[1])**2)


class Landmark:
    
  def __init__(self):
    self.length = 0
    self.points = []

  def addPair(self, pair):
    self.points.append(pair)
    self.length += 1
    

  def getLength(self):
    return self.length


    

class Scan:


  def __init__(self, thisId):
    self.thisId = thisId
    self.dist = []
    self.thet = []
    self.landmarks = []
    self.pos = [0,0]
    self.rot = 0
    print("New Scan initiated: id "+str(thisId))
    
  def addPair(self, myThet, myDist):
    self.dist.append(myDist)
    self.thet.append(myThet)

  def getPair(self, index):
      return [self.thet[index], self.dist[index]]

  def plot(self):
    print("Attempting to plot...")
    plt.polar(self.thet, self.dist, ".")
    print("Plotted.")

  def removeOutliers(self):
    dist = self.dist
    myLen = len(dist)
    if myLen < 4:
      print("Insufficient data")
    else:
      myStdev = statistics.stdev(dist)
      myMean = statistics.mean(dist)
      z3 = myMean + (myStdev*3)
      
      for i in range(myLen):
        if ((z3)<dist[i]) or (dist[i]<0) or (dist[i]>50):
          self.dist[i] = -10000
          self.thet[i] = -10000

      self.dist = [x for x in self.dist if x != -10000]
      self.thet = [x for x in self.thet if x != -10000]

  def sortData(self):
    try:
      sorted_pairs = sorted(zip(self.thet, self.dist))
      self.thet, self.dist = zip(*sorted_pairs)
      self.thet = list(self.thet)
      self.dist = list(self.dist)
    except Exception:
      self.thet, self.dist = [], []
   
  def toXY(self):
    plotX = []
    plotY = []

    myLen = len(self.thet)
      
    for i in range(myLen):
      plotX.append(math.cos(self.thet[i])*self.dist[i])
      plotY.append(math.sin(self.thet[i])*self.dist[i])
      
    #return [plotX, plotY]
    
    return XYpl(plotX, plotY)

  def pairToXY(self, i):
        try:
          tupX = math.cos(self.thet[i])*self.dist[i]
          tupY = math.sin(self.thet[i])*self.dist[i]
          return [tupX, tupY]
        except Exception:
            return [0, 0]

  def landmark(self):
    self.landmarks = []
    myLen = len(self.thet)
    prevDist = self.thet[0]
        
    for i in range(1, myLen):
      newDist = self.thet[i]

      distRatio = newDist/prevDist if newDist>prevDist else prevDistewDist

      if (distRatio < 1.75) and (len(self.landmarks) > 0):
        self.landmarks[-1].addPair(self.getPair(i))

      else:
        newLandmark = Landmark()
        newLandmark.addPair(self.getPair(i))
        self.landmarks.append(newLandmark)

  def getSecondInRange(self,low,high):
    #self.sortData()
    firstDist = 10000
    secondDist = 10001

    for i in range(len(self.thet)):
      myDist = self.dist[i]
      myThet = self.thet[i]
      if (myThet < high) and (myThet > low):
        if myDist < firstDist:
          secondDist = firstDist
          firstDist = myDist
        elif myDist < secondDist:
          secondDist = myDist


    return secondDist

  def getLeft(self):
    return self.getSecondInRange(2.7,3.8)

  def getFront(self):
    return self.getSecondInRange(1.35,1.95)


  

    
          
        

class XYpl:

  def __init__(self,plotX,plotY):
    self.plotX = plotX
    self.plotY = plotY
    self.thX = 0
    self.thY = 0

  def addPoint(self,myX,myY):
    self.plotX.append(myX)
    self.plotY.append(myY)

  def plot(self,colors):
    plt.plot(self.plotX,self.plotY,".",color=colors)

  def rotate(self, pivX, pivY, angle): #rotates plane - add angles and pivot point coords
    myCos = math.cos(angle)
    mySin = math.sin(angle)
    for i in range(len(self.plotX)):
      myX = self.plotX[i]
      myY = self.plotY[i]
      newX = pivX + ((myX-pivX)*myCos) - ((myY-pivY)*mySin)
      newY = pivY + ((myX-pivX)*mySin) + ((myY-pivY)*myCos)
      self.plotX[i] = newX
      self.plotY[i] = newY #function currently does not affect x, y, or rot - fix
      
  def translate(self, xt, yt): #translates plane - add angles 
    for i in range(len(self.plotX)):
      self.plotX[i] += xt
      self.plotY[i] += yt
      self.thX += xt
      self.thY += yt

  def testOverlap(self, other):
    plotX = self.plotX
    plotY = self.plotY
    otherX = other.plotX
    otherY = other.plotY

    score = 0
      
    for i in range(len(plotX)):
      minDist = 10000

      for j in range(len(otherX)):
        dist = findDist([plotX[i],plotY[i]],[otherX[j],otherY[j]])
        if dist < minDist:
          minDist = dist

      if minDist < 5:
        score += 4
      elif minDist < 10:
        score += 3
      elif minDist < 20:
        score += 2
      elif minDist < 30:
        score += 1

    return score

  def addToXY(self, other):
    for i in range(len(self.plotX)):
      other.addPoint(self.plotX[i],self.plotY[i])

  def findBestTranslate(self, other):


    self.translate(-30,-30)
    posX = -30
    posY = -30
    highScore = 0

    currentCoords = [0,0]

    for x in range(13):
      for y in range(13):
        myScore = self.testOverlap(other)
        if myScore > highScore:
          highScore = myScore
          currentCoords = [posX, posY]
        self.translate(0,5)
        posY += 5
      self.translate(5,-65)
      posX += 5
      posY -= 65

    self.translate(-35,30)
    posX -= 35
    posY += 30

    self.translate(currentCoords[0],currentCoords[1])
    return currentCoords
    
       
    
  
  def findBestRotate(self, other, pivX, pivY):

   scoreList = []

   self.rotate(pivX, pivY, 0.523598)

   for i in range(21):
     scoreList.append(self.testOverlap(other))
     self.rotate(pivX, pivY, -0.0523598)
   
   self.rotate(pivX, pivY, 0.523598)
   
   bestPos = scoreList.index(max(scoreList))-1
   bestRot = 0.523598-(bestPos*0.0523598)
   
   self.rotate(pivX, pivY, bestRot)
   print("Index: ",bestPos)
   print("Actual: ",self.testOverlap(other))
   return bestRot

   
   


recentScan = Scan(-1)
secondScan = None
scanCount = 0
posX = 0
posY = 0  
    
time.sleep(2)
    

def readSer():
  global recentScan
  global scanCount
  while True:
    try:# Read a line from the serial port (reads until a newline '\n' character)
      if ser.in_waiting > 0:
        received_data = ser.readline().decode('utf-8').rstrip()
        print(f"Received: {received_data}")
        if received_data[:5] == "#SCAN":
          recentScan = Scan(scanCount)
          scanCount += 1
          print("New Scan")
          
        if received_data[:6] == "#PAIR ":

          scanRads = float(received_data[6:10:])
          scanDist = int(received_data[11:])
          recentScan.addPair(scanRads, scanDist)
    except serial.SerialException as e:
      print(f"Serial error: {e}")
      time.sleep(0.1)
    except KeyboardInterrupt:
      ser.close()
      termin()


def findInput():
  
  global recentScan
  global scanCount

  ser.write("---".encode("utf-8"))
  ser.write("a".encode("utf-8"))
  ser.write("m".encode("utf-8"))
  time.sleep(10)
  ser.write("b".encode("utf-8"))
  time.sleep(1)
  ser.write("s".encode("utf-8"))
  time.sleep(0.5)
  oldScan = deepcopy(recentScan)
  oldScan.removeOutliers()
  oldScan = oldScan.toXY()
  recentScan = Scan(2)
  ser.write("m".encode("utf-8"))
  time.sleep(10)
  oldScan.plot("black")
  recentScan.removeOutliers()
  xyScan = recentScan.toXY()
  xyScan.translate(0,-38)
  adjustedXY = deepcopy(xyScan)
  print(adjustedXY.findBestTranslate(oldScan))
  print(adjustedXY.findBestRotate(oldScan, 0, -38))
  print(adjustedXY.findBestTranslate(oldScan))
  xyScan.plot("red")
  adjustedXY.plot("green")
  plt.show()

  while True:
    myInput = input("")
    if myInput == "p":
      recentScan.removeOutliers()
      recentScan.sortData()
      xy = recentScan.toXY()
      xy.plot()
      plt.show()
    elif myInput == "/s":
      ser.close()
      termin()
    elif myInput == "/c":
      scanCount += 1
      recentScan = Scan(scanCount)
    ser.write(myInput.encode("utf-8"))


def writeSer(myInput):
  ser.write(myInput.encode("utf-8"))

def goToWall():
  writeSer("n")
  time.sleep(2)
  #Note: recentScan refers to a different scan than before "m" was written in serial
  recentScan.removeOutliers()
  recentScan.sortData()
  if recentScan.getFront()>30:
    writeSer("f")
    time.sleep(0.5)
    writeSer("s")
    return 0
  elif recentScan.getFront()>12:
    writeSer("f")
    time.sleep(0.3)
    writeSer("s")
    return 0
  else:
    return 1
    

def wallFollow(myScan):

  global prevLeft
  global prevScore
  
  leftScore = myScan.getLeft() < 25
  frontScore = myScan.getFront() < 15
    
  if frontScore:
    writeSer("rrrrrrrrr")
    myScan.rot += 0.523598
    return "DEVNOTE: front, so move right"
    prevScore = "r"
  
  elif not leftScore:
    print(prevScore,"prevScore")
    '''if prevScore == "f":
      print("forwarded")
      writeSer("f")
      time.sleep(0.3)
      writeSer("s")
      myScan.pos[0] += 7 * math.cos(myScan.rot)
      myScan.pos[1] += 7 * math.sin(myScan.rot)
      '''
    time.sleep(0.1)
    writeSer("lll")
    writeSer("f")
    time.sleep(0.005*prevLeft)
    writeSer("s")
    myScan.rot += 0.523598
    return "DEVNOTE: not left, so move left"
    prevScore = "l"
    
  else:
    writeSer("f")
    time.sleep(0.5)
    writeSer("s")
    myScan.pos[0] += 15 * math.cos(myScan.rot)
    myScan.pos[1] += 15 * math.sin(myScan.rot)
    return "DEVNOTE: left and not front, so move forward"
    prevScore = "f"
    if myScan.getLeft()+3 < prevLeft:
      writeSer("r")
      myScan.rot -= math.pi/36
    if myScan.getLeft()-3 > prevLeft:
      writeSer("l")
      myScan.rot += math.pi/36 

  prevLeft = getLeft()
    
    

def checkClosure(xyP1, xyP2):
	
  score = xyP1.testOverlap(xyP2)
  if score > 50:
    return True
  else:
    return False

def mainCode2():

  global prevLeft
  global prevScore
  
  global recentScan
  myPos, myRot = [0, 0], math.pi/2
  
  ser.write("---".encode("utf-8"))
  ser.write("a".encode("utf-8"))
  writeSer("n")
  time.sleep(2)
  if recentScan.getLeft() > 25:
    for i in range(10):
        output = goToWall()
        if output:
            break
  ser.write("m".encode("utf-8"))
  time.sleep(10)
  bigScan = deepcopy(recentScan)
  bigScan.removeOutliers
  bigScan = bigScan.toXY()
  robotPoints = XYpl([],[])

  for i in range(10):
    robotPoints.addPoint(myPos[0],myPos[1])
    print(wallFollow(recentScan))
    myPos, myRot = recentScan.pos, recentScan.rot
    print(myPos, myRot)
    recentScan = Scan(scanCount)
    
    writeSer("n")
    time.sleep(2)
    recentScan.pos, recentScan.rot = myPos, myRot
    #Note: recentScan refers to a different scan than before "m" was written in serial
    recentScan.removeOutliers()
    recentScan.sortData()
    currentScan = deepcopy(recentScan)
    myPrev = prevScore
    currentScan = currentScan.toXY()
    currentScan.translate(myPos[0],myPos[1])
    currentScan.rotate(myPos[0],myPos[1],myRot)
    #if myPrev == "f":
        #currTrans = currentScan.findBestTranslate(bigScan) #error correction algs for next 3 lines
        #myPos[0] += currTrans[0]
        #myPos[1] += currTrans[1]
        #myRot +=
        #currentScan.findBestRotate(bigScan, myPos[0], myPos[1])
        #currTrans = currentScan.findBestTranslate(bigScan)
        #myPos[0] += currTrans[0]
        #myPos[1] += currTrans[1]
    #bigScan.plot("black")
    #currentScan.plot("green")
    #robotPoints.plot("purple")
    
    #plt.show(block=False)
    #plt.pause(2)
    #plt.close("all")
    currentScan.addToXY(bigScan)

    


    
    
    
    

def mainCode():

  global recentScan

  ser.write("---".encode("utf-8"))
  ser.write("a".encode("utf-8"))
  ser.write("m".encode("utf-8"))
  time.sleep(10)

  oldScan = deepcopy(recentScan)
  oldScan.removeOutliers()
  oldScan = oldScan.toXY()

  for i in range(3):
    ser.write("b".encode("utf-8"))
    time.sleep(1)
    ser.write("s".encode("utf-8"))
    time.sleep(0.5)
    ser.write("m".encode("utf-8")) #scans
    time.sleep(10)
    recentScan.removeOutliers()
    xyScan = recentScan.toXY()
    xyScan.translate(0,-38*i)
    adjustedXY = deepcopy(xyScan)
    adjustedXY.findBestTranslate(oldScan) #error correction algs for next 3 lines
    adjustedXY.findBestRotate(oldScan, 0, -38)
    adjustedXY.findBestTranslate(oldScan)
    print("xylen:",len(xyScan.plotX))
    print("adjustedxylen:",len(adjustedXY.plotX))
    print("oldScanlen:",len(oldScan.plotX))
    plt.pause(1)
    xyScan.plot("red")
    adjustedXY.plot("green")
    oldScan.plot("black")

    plt.show(block=False)
    plt.pause(10)
    plt.close("all")
    adjustedXY.addToXY(oldScan)

def mainCode3():
  global recentScan
  ser.write("---".encode("utf-8"))
  ser.write("a".encode("utf-8"))
  ser.write("m".encode("utf-8"))
  time.sleep(10)
  recentScan.removeOutliers()
  newScan = recentScan.toXY()
  newScan.plot("blue")
  plt.show()
  

background_thread = threading.Thread(target=readSer)
background_thread.daemon = True 
background_thread.start()

mainCode2()
mainCode3()

'''while 1:
  try:
    findInput()
  except KeyboardInterrupt:
    ser.close()
    termin()'''
  

    
