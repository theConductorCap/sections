#   Python Socket client
#   Created May 1 2023 by Joel Legassie
#   
#  Functionality
#  Connect to server and send test byte
#  Receive 24 bytes data and decode into 3x1 vector
#  Decodes binary code in 12 bit twos complement into 16 bit signed integers
#  Organizes samples into packets of packetSize corresponding to a handPosition
#  Writes packets to files cumulatively - binary and human readable (CSV)
#  Generates plot images of each packet

import socket  
import numpy as np
import struct
import time
import threading
from threading import Thread
import matplotlib.pyplot as plt 
import os.path 
import NeuralNetwork
import dill   
import subprocess
import csv      

class GetData:
    
    def __init__(self, *, host="192.168.1.75", port=80, packetSize=1, numSensors=4, pathPreface='data/test', labelPath="Test", label=0, getTraining=True):
        self.host = host
        self.port = port
        self.ssid = "TheConductor"
        self.pswd = "NoneShallPass"
        self.packetSize = packetSize
        self.numSensors = numSensors
        self.packetData = np.zeros([1, self.packetSize * self.numSensors * 3]) #one packet of data corresponding to a handPosition - 3 axis * number of sensors times the number of samples per handPosition
        #self.packetArr = np.zeros([1, self.packetSize * self.numSensors * 3]) #An array of packets (handPositions) used while collecting data for training
        self.packetCount = 0
        self.packetDone = 0
        self.pathPreface = pathPreface 
        self.labelPath = labelPath
        self.label = label
        self.getTraining = getTraining
        #self.packetLimit = packetLimit
        self.predictions = []
        self.plotTimer = int(time.time() * 1000)   #Used to make timed plots of input data for plots
        self.plotCounter = 0 #counts how many plots have been made
        self.dataTx = struct.pack("=B", 255)     #Used to determine what data packet to get from the ESP32 (ie. time of flight data or no) (255 [OxFF] is no ToF, 15 [0x0F] is yes ToF)
        self.extraRxByte = 0   #Use to add to the socket RX index to collect the ToF byte when it exists
        self.ToFByte = -1 #Holds the ToF sensor data value
        self.y = []
        self.dataGot = 0   #data received flag
        self.sockRecursionCount = 0
        self.sock = socket.socket()
        self.sockConnection = 0

        #On dataStream init try to connect to The Conductor on AP network, if not carry on
        connectTries = 0
        #Try the last connection
        cntList = self.getloggedCSV("networks.csv")


########UNcomment below for live wifi connection...
    
        # if cntList[0][0] != '-1':
        #     cntListLen = len(cntList)
        #     print(f'cntListLen: {cntListLen}')
        #     self.host = cntList[cntListLen-2][2]
        #     self.port = int(cntList[cntListLen-2][3])

        # while connectTries < 1:
        #     print("Trying to make a socket connection")
        #     #disable connect on start up to test GUI
        #     connectTries += 1
        #     if self.makeSockConnection(self.host, self.port) == -1:
        #         connectTries += 1
        #         time.sleep(1)
        #     else:
        #         print("Connected to The Conductor!")
        #         break
        
        # if connectTries == 1:
        #     print("Can't connect to the Conductor")


    def makeSockConnection(self, host, port):        #self.sock.close()
        print()
        print("makeSockConnection()")
        print(f'dataTx: {self.dataTx}')
        print(f'host {host}')
        print(f'port: {port}')
       
        hostLen = len(host)
        if not host[hostLen-1].isdigit():
            print('Please enter a valid IP address')
            return -1

        self.sock = socket.socket()
        #self.sock.setblocking(False)
        #print(f'socket: {self.sock.getpeername}')
        #print(f'socket Type: {self.sock.type()}')
        try:
            self.sock.connect((host, port))
            print(f'socket: {self.sock.getpeername}')

        except socket.timeout as err:
            print(f"TCP/IP Socket Timeout Error {self.sockRecursionCount}: {err}")
            self.sockConnection = 0
            self.sockRecursionCount += 1
            return -1

        except socket.error as err:
            print(f"TCP/IP Socket Error: {err}")
            self.sockConnection = 0
            self.sockRecursionCount += 1
            return -1
            #self.sock.close()
            #self.socket.create_connection((self.host, self.port), timeout=2)
            #self.sock.connect((host, port), timeout=2)
        
        print(f'socket: {self.sock.getpeername}')
        self.sockRecursionCount = 0
        self.sockConnection = 1
        return 1
    
    def checkPriorConnection(self, network):
        priorNetworks = self.getloggedCSV("networks.csv")
        for i in range(len(priorNetworks)):
            if len(priorNetworks[i]) > 3:
                if priorNetworks[i][0] == network:
                    print("We have a match - update password infos")
                    return 1, priorNetworks[i][1]
                else:
                    print("Network not found please provide a password")
                    return -1, '-1'
    
    def getNetworks(self):
        #Get list of network from the air
        SSIDList = []
        networks = subprocess.check_output(["netsh", "wlan", "show", "network"])
        networks = networks.decode("utf-8","ignore")
        networks = networks.replace("\r,","")
        ls = networks.split('\n')
        ls = ls[4:]

        counter = 0
        while counter < (len(ls)):
            if counter % 5 == 0:
                #print(ls[counter])
                if len(ls[counter]) > 9:
                    ls[counter] = ls[counter][9:]
                    print(f'Network {counter}: {ls[counter]}')
                    SSIDList.append(ls[counter])
            counter += 1
        return SSIDList
    
    def getloggedCSV(self, pathSuffix):
        networkPath = self.pathPreface + '/' + pathSuffix #"/networks.csv"
        if os.path.exists(networkPath):
            with open(networkPath, 'r') as csvfile:
                networkList = list(csv.reader(csvfile, delimiter=","))
                print(f'networkList; {networkList}')
            return networkList
        else:
            return [['-1']]

    # def logCSVRow(self, pathSuffix, csvRowList, *, append=True):
    #     print()
    #     print(f'logCSVRow()')
    #     if append == True:
    #         mode = 'a'
    #     else:
    #         mode = 'w'
    #     networkPath = self.pathPreface + '/' + pathSuffix #"/networks.csv"
        
    #     print(f'CSV writer path: {networkPath}')
    #     if networkPath != -1:
    #         if os.path.exists(networkPath):
    #             print(f"file exists")
    #             with open(networkPath, mode, newline='') as csvfile:
    #                 csvWrite = csv.writer(csvfile)
    #                 csvWrite.writerow(csvRowList)
    #                 #[self.ssid, self.pswd, self.host, self.port]
    #     else:
    #         print(f"Creating new file")
    #         with open(networkPath, 'w', newline='') as csvfile:
    #             csvWrite = csv.writer(csvfile)
    #             csvWrite.writerow(csvRowList)


    def promptServer(self, dataTx, host, port, rcount):
        print()
        print("promptServer")
        print(f'dataTx: {dataTx}')
        # print(f'host {host}')
        # print(f'port: {port}')            

        print(f'Socket peer name: {self.sock.getpeername()}')

        #Check socket connection and send prompt to the server        
        try:   
            self.sock.send(dataTx)    
            
        except socket.timeout as err:
            print(f"TCP/IP Socket Timeout Error {self.sockRecursionCount}: {err}")
            self.sock.close()
            self.sock = socket.socket()
            #self.socket.create_connection((self.host, self.port), timeout=2)
            self.sock.connect((host, port))
            #self.sock.send(self.dataTx)
            if rcount < 5:
                rcount += 1
                if self.promptServer(dataTx, host, port, rcount) == 1:
                    return 1
            else:
                print(f'Fatal Error: SocketBroken')
                #print(f"TCP/IP Socket Error: {err}")
                print(f"Failed transmission: {dataTx}, length: {len(dataTx)}")
                self.sockRecursionCount = 0
                return -1
            
        except socket.error as err:
            print(f"TCP/IP Socket Error: {err}")
            self.sock.close()
            self.sock = socket.socket()
            #self.socket.create_connection((self.host, self.port), timeout=2)
            self.sock.connect((host, port))
            if rcount < 5:
                rcount += 1
                if self.promptServer(dataTx, host, port, rcount) == 1:
                    #print(f"Sent Data after {rcount + 1} tries")
                    self.host = host
                    self.port = port
                    return 1
            else:
                print(f'Fatal Error: SocketBroken')
                #print(f"TCP/IP Socket Error: {err}")
                print(f"Failed transmission: {dataTx}, length: {len(dataTx)}")
                self.sockRecursionCount = 0
                return -1

        #print(f"Sent Data after {rcount + 1} tries")
        self.host = host
        self.port = port
        return 1


    def processData(self, binaryData):
        print()
        print(f'processData()')
        print(f'binaryData: {binaryData}')

        #packetStartMS = int(time() * 1000)
        #global processCount

        def formatData(binaryData, sensorIndex):
            print(f'sensor: {sensorIndex}')
            print()
            #print(f'binaryData: {binaryData}')
            #Parse binary data and recombine into ints
            #X Axis

            print(f'sensor: {sensorIndex}')
            print(f'XIndex: {0 + (sensorIndex * 3 * self.numSensors)}')
            print(f'self.sock.getpeername(): {self.sock.getpeername()}')

            XAccTuple = struct.unpack("=b", binaryData[0 + (sensorIndex * 3)])  ##MSB is second byte in axis RX; Just a nibble
            XAcc = XAccTuple[0]
            #XAcc = float(int(binaryData[0 + (sensorIndex * 3 * self.numSensors)]),0)
            print(f'XAcc Raw: {XAcc}')
            if self.getTraining is False:
                self.packetData[0, (3 * sensorIndex)] = XAcc / 127   #Scale to 0-127 for prediction
            else:
                self.packetData[0, (3 * sensorIndex)] = XAcc         #Will scale values while compiling data for training

            #Y Axis
            YAccTuple = struct.unpack("=b", binaryData[1 + (sensorIndex * 3)])
            YAcc = YAccTuple[0]
            print(f'YAcc Raw: {YAcc}')
            if self.getTraining is False:
                self.packetData[0, 1 + (3 * sensorIndex)] = YAcc / 127
            else:       
                self.packetData[0, 1 + (3 * sensorIndex)] = YAcc

            #Z Axis
            ZAccTuple = struct.unpack("=b", binaryData[2 + (sensorIndex * 3)])
            ZAcc = ZAccTuple[0]
            print(f'ZAcc Raw: {ZAcc}')
            if self.getTraining is False:
                self.packetData[0, 2 + (3 * sensorIndex)] = ZAcc / 127
            else:
                self.packetData[0, 2 + (3 * sensorIndex)] = ZAcc

            #print(f"self.dataTx: {self.dataTx}")
            # TOF sensor
            if self.dataTx[0] == 0x0F and sensorIndex == self.numSensors - 1:  #If ToF is enabled and we are on the last sensor - get the ToF byte
                ToFTuple = struct.unpack("=b", binaryData[(self.numSensors * 3)])   #ToF data is the last byte
                self.ToFByte = ToFTuple[0]
                print(f"self.ToFByte: {self.ToFByte}")
            else:
                #reset ToFByte
                self.ToFByte = -1
        
        for i in range(self.numSensors):
            formatData(binaryData, i)
    
    def receiveBytes(self):
        #Checks the connection to the servers, sends the prompt and then receives numSensors * 3 bytes
        #Collects one sample and returns the data as a byte array
        count = 0
        #sock = socket.socket()
        print("receiveBytes()")
        print(f'dataTx: {self.dataTx}')  
        #dataTx = struct.pack("=B", 34)  
        #print("Sending prompt to server")
        #print(f'dataTx: {dataTx}') 
        if self.promptServer(self.dataTx, self.host, self.port, 0) == 1:
            print("Prompt Success") 
        else:       
            print("Failed Prompt")
            return -1   
        
        #Now receive the response
        #y = self.sock.recv(numSensors * 3)
        #print(f'y at the start: {self.y}')
        self.y = [] #Reset y
        a = 0
        errorCount = 0
        #sampleRxStartMS = int(time.time() * 1000)
        while a < ((self.numSensors * 3 + self.extraRxByte)):                #iterate through the number of sensors * the number of bytes per sample
            #print(f'while loop a')
            try:
                self.y.append(self.sock.recv(1))
                #print(f'Received 1')
            except socket.error as err:
                print(f"TCP/IP Socket RX Error: {err}")
                #print(f"Failed transmission: {self.dataTx}, length: {len(self.dataTx)}")
                print(f"Unable to reach client with socket: Retrying...")
                #Close and reopen the connection
    
                # while errorCount < 2:      #If you get ten connection errors in a row close and reopen the socket
                #     #Close and reopen the connection
                #     # self.sock.close()
                #     # self.sock.connect((self.host, self.port))
                #     a -= 1     #Ask for a resend (decrement data index)
                #     errorCount += 1
                if self.promptServer(self.dataTx, self.host, self.port, 0) == -1:
                    print(f'Fatal Error: SocketBroken')
                    #a -= 1
                    #print(f"TCP/IP Socket Error: {err}")
                    print(f"Failed transmission: {self.dataTx}, length: {len(self.dataTx)}")
                    return -1
            a += 1 
        
        #sock.close()
        self.dataGot = 1
        print(f"self.y returned: {self.y}")
        return self.y
    
    def socketSendStr(self, message):
        print()
        print(f'socketSendStr()')
        response0 = []

        #Send the prompt to get ESP32 ready to receive text
        self.dataTx = struct.pack("=B", 34)
        #self.promptServer(self.dataTx, self.host, self.port)
        print(f'self.dataTx (0x22): {self.dataTx}')
        response0 = self.receiveBytes()
        print(f"Got response0: {response0}")
        print(f'response0[0]: {response0[0]}')
        print(f'response0[1]: {response0[1]}')

        first = struct.unpack("=B", response0[0]) 
        second = struct.unpack("=B", response0[1]) 
        first = first[0]
        second = second[0]

        if first == 0xFF and second == 0x0F:
            print(f'Server is ready sending length of the message to server: {len(message)}')
            self.dataTx = message.encode()
            print(f"Encoded message: {self.dataTx}")
            if self.promptServer(self.dataTx, self.host, self.port, 0):
                return 1
            else:
                return -1     

    # def receiveBytes(self):
    #     print()
    #     print(f'receiveBytes(self)')
    #     #Signals the server then receives a byte from the sample
        
    #     sock = socket.socket()
    #     sock.connect((self.host, self.port))
    #     print()
    #     print("Connected to server")
    #     try:
    #         sock.send(self.dataTx)
    #         #print("Sent Data")
    #     except:
    #        sock.connect((self.host, self.port))
    #        #print("Socket Reconnected")
    #        sock.send(self.dataTx)
    #     # print(f'sockname: {sock.getsockname()}')
    #     # print(f'sockpeer: {sock.getpeername()}')
    #     #y = []
    #     #time.sleep(0.01)
    #     #y = sock.recv(18)
    #     a = 0
    #     errorCount = 0
    #     #sampleRxStartMS = int(time.time() * 1000)
    #     while a < ((self.numSensors * 3) + self.extraRxByte):                #iterate through the number of sensors * the number of bytes per sample
    #         #print(f'while loop a')
    #         try:
    #             self.y.append(sock.recv(1))
    #             #print(f'Received 1')
    #         except ConnectionError:
    #             print(f"Unable to reach client with socket: Retrying")
    #             #Close and reopen the connection
    #             if errorCount < 10:      #If you get ten connection errors in a row close and reopen the socket
    #                 #Close and reopen the connection
    #                 sock.close()
    #                 sock = socket.socket()
    #                 sock.connect((self.host, self.port))
    #                 a -= 1     #Ask for a resend (decrement data index)
    #                 errorCount += 1
    #                 sock.send(self.dataTx)
    #             else:
    #                 print(f'Fatal Error: SocketBroken')
    #                 return -1
    #         a += 1 
    #     sock.close()
    #     self.dataGot = 1
    #     #print(f"self.y: {self.y}")
    #     return self.y
    
    #print(f'Sample Received - One byte')

    def getSample(self): #recvCount counts samples in a packet in training mode; in prediction mode it is the index for the circular buffer
        print()
        print('getSample()')
        packetStartMS = 0 

            #Sends one byte from dataPacket and asks for more
            #while recvCount < self.packetSize:
        sampleRxStartMS = int(time.time() * 1000)
        dataThread = Thread(target=self.receiveBytes)
        dataThread.start()
                #y = self.receiveBytes()
                #print(f'Receive Bytes')

        #while threading.active_count() > 1:
            #print(f'threading.active_count(): {threading.active_count()}')
        dataThread.join()

        sampleRxStopMS = int(time.time() * 1000)
        sampleRxTimeMS = sampleRxStopMS - sampleRxStartMS
        print(f'Sample receive time in ms: {sampleRxTimeMS}')

        #print(f'self.y loop: {self.y}')
                
        #print(f'Start preocessData() thread for sample: {recvCount}' )
        if len(self.y) == 0:
            print("No data received reset socket connection")
            while self.sockRecursionCount < 4:
                self.sock.close()
                if self.makeSockConnection(self.host, self.port) == -1:
                    time.sleep(1)
                else:
                    print("Reconnected to The Conductor!")  
        else:    
            self.processData(self.y)
        
        self.y = []  #Reset y so that it doesn't get too full...

        #Prediction mode      
    def predictSample(self):

        NNINput = np.roll(self.packetData, (3 * self.numSensors)*(self.packetSize - 1))  #roll the packetData circular array to put them in the right order

        #print(f'Input to NN (rolled): {NNINput}')
        print(f'Making Prediction...') 
        prediction = NeuralNetwork.realTimePrediction(NNINput, self.pathPreface)
                    #print(f'prediction: {prediction}')

        return prediction            

    def prepTraining(self):    #Prep the packet for training
        print()
        print('prepTraining')
        print(f'self.label: {self.label}')
        #print(f'self.packetData: {self.packetData}') 

        #scale the data to +-1
        for i in range(self.packetData.shape[1]):
            self.packetData[0,i] = self.packetData[0,i] / 127
        print(f'self.packetData.shape: {self.packetData.shape}')
        #Get ground truth labels
        packetTruth = np.zeros([1,], dtype=int)
        #print(f'packetTruth.shape: {packetTruth.shape}')
        packetTruth[0] = self.label
        #print(f'packetTruth: {packetTruth}')

        #Write to files
        self.writetoBinary(self.packetData, packetTruth)
        self.writetoCSV(self.packetData, packetTruth)

    def writetoBinary(self,trainingData, packetTruth):
        print()
        print('writetoBinary()')
        print(f'trainingData for write: {trainingData}')
        #Write data to .npy file (binary) -- faster
        dataPath = self.pathPreface + '/' + self.labelPath + '.npy'
        truthPath = self.pathPreface + '/' + self.labelPath + '_truth.npy'

        #Data
        if os.path.exists(dataPath):
            tmpArr = np.load(dataPath,allow_pickle=False)
            #print(f'tmpArr from file: {tmpArr}')
            tmpArr = np.append(tmpArr,trainingData, axis=0)
            np.save(dataPath, tmpArr, allow_pickle=False)
            # print(f'dataPacket shape (Binary): {tmpArr.shape}')
            # print(f'dataPacket saved (Binary): {tmpArr}')
            
        else: 
            np.save(dataPath, trainingData, allow_pickle=False)
            # print(f'dataPacket shape (Binary): {trainingData.shape}')
            # print(f'dataPacket saved (Binary): {trainingData}')

        #Truth
        print(f'truth path: {truthPath}')
        if os.path.exists(truthPath):
            tmpArr = np.load(truthPath,allow_pickle=False)
            print(f'Binary truths from file: {tmpArr}')
            tmpArr = np.append(tmpArr,packetTruth)
            np.save(truthPath, tmpArr, allow_pickle=False)
            print(f'packetTruth appended and saved (Binary): {tmpArr}')
        else: 
            np.save(truthPath, packetTruth, allow_pickle=False)
            print(f'packetTruth saved (Binary): {packetTruth}')

    def writetoCSV(self, trainingData, packetTruth):
        print()
        print('writetoCSV()')
        print(f'trainingData for write: {trainingData}')
        #Write data to .csv file (text) - human readable
        #print(f'CSV write training data')
        dataPath = self.pathPreface + '/' + self.labelPath + '.csv'
        truthPath = self.pathPreface + '/' + self.labelPath + '_truth.csv'
        
        #Data - 2D array axis 0 (rows) are handPositions, axis 1 (cols) are features within a handPosition
        if os.path.exists(dataPath):
            tmpArr = np.loadtxt(dataPath,dtype=float, delimiter=',', ndmin=2)       
            #print(f'tmpArr.shape 1: {tmpArr.shape}')
            #print(f'tmpArr: {tmpArr}')          
            
            tmpArr = np.append(tmpArr,trainingData, axis=0)                  #Append trainingData to tmpArr
            #print(f'tmpArr.shape 2 (CSV): {tmpArr.shape}')
            #print(f'tmpArr (CSV): {tmpArr}')

            np.savetxt(dataPath, tmpArr, fmt="%f", delimiter=",") 
            # print(f'dataPacket appended and saved (CSV): {tmpArr}')
        else: 
            #tmpArr = np.reshape(trainingData, (trainingData.shape[0] * 4, 4))   #Reshape to a 2-D array
            np.savetxt(dataPath, trainingData, fmt="%f", delimiter=",")
            # print(f'dataPacket appended and saved (CSV): {trainingData}')
            # print(f'dataPacket shape: {trainingData.shape}')
        
        #Truth - 1D Array of same length as data
        if os.path.exists(truthPath):
            tmpArr = np.loadtxt(truthPath,dtype=int, delimiter=',')
            tmpArr = np.append(tmpArr,packetTruth) 
            np.savetxt(truthPath, tmpArr, fmt="%d", delimiter=",")
            #print(f'packetTruth appended and saved (CSV): {tmpArr}')
            #print(f'packetTruth shape: {tmpArr.shape}')
        else: 
             np.savetxt(truthPath, packetTruth, fmt="%d", delimiter=",")
             #print(f'packetTruth appended and saved (CSV): {packetTruth}')
             #print(f'dataPacket shape: {packetTruth.shape}')


#Useful matplot function for when packet size is above 1 
    # def plotAcc(self):

    #     _,axs = plt.subplots(self.numSensors,3, figsize=(12,8))
        
    #     #Axis labels
    #     axs[0][0].set_title('X Axis')
    #     axs[0][1].set_title('Y Axis')
    #     axs[0][2].set_title('Z Axis')
        
    #     for i in range(self.numSensors):
    #         # Sensor labels
    #         axs[i][0].set_ylabel(f'Sensor {i}')

    #         #Data
    #         XList = [[],[]]
    #         for j in range(self.packetSize):
    #             XList[0].append(self.packetData[0, 0 + (i * 3) + (j * self.numSensors * 3)])
    #             XList[1].append(j)
    #             #print(f'XList{j}: {XList}')
    #         axs[i][0].plot(XList[1], XList[0])

    #         YList = [[],[]]
    #         for j in range(self.packetSize):
    #             YList[0].append(self.packetData[0, 1 + (i * 3) + (j * self.numSensors * 3)])
    #             YList[1].append(j)
    #             #print(f'YList{j}: {YList}')
    #         axs[i][1].plot(YList[1], YList[0])

    #         ZList = [[],[]]
    #         for j in range(self.packetSize):
    #             ZList[0].append(self.packetData[0, 2 + (i * 3) + (j * self.numSensors * 3)])
    #             ZList[1].append(j)
    #             #print(f'ZList{j}: {ZList}')
    #         axs[i][2].plot(ZList[1], ZList[0])

    #     if self.getTraining:    
    #         figPath = self.pathPreface + self.labelPath + str(self.packetCount) + '_' + str(self.label) + '.png'
    #         plt.savefig(figPath)
    #     else:
    #         figPath = self.pathPreface + "PredPlots/" + str(self.plotCounter) + '.png'
            
    #         plt.savefig(figPath)

    #     #plt.show()   
    #     plt.close         

# def createTrainingData(*, pathPreface='data/data', labelPath="test", label=0, packetLimit=1, packetSize=1, numSensors=4):
#     trgData = GetData(packetSize=packetSize, pathPreface=pathPreface, labelPath=labelPath, label=label, getTraining=True, packetLimit=packetLimit, numSensors=numSensors)
#     trgData.socketLoop(0)

# def main():
    
#     #Get Data for training
#     # createTrainingData(pathPreface="data/packet5Avg20/training00_noMove", packetLimit=20, label=0, packetSize=5, numSensors=2)
#     # createTrainingData(pathPreface="data/packet5Avg20/training00_noMove_Test", packetLimit=2, label=0, packetSize=5, numSensors=2)

#     # createTrainingData(pathPreface="data/packet5Avg20/training01_upandDown", packetLimit=20, label=1, packetSize=5, numSensors=2)
#     # createTrainingData(pathPreface="data/packet5Avg20/training01_upandDown_Test", packetLimit=2, label=1, packetSize=5, numSensors=2)

#     # createTrainingData(pathPreface="data/packet5Avg20/training02_inandOut", packetLimit=20, label=2, packetSize=5, numSensors=2)
#     # createTrainingData(pathPreface="data/packet5Avg20/training02_inandOut_Test", packetLimit=2, label=2, packetSize=5, numSensors=2)
    
#     #Testing
#     #createTrainingData(pathPreface="data/test/test", packetLimit=10, label=0, packetSize=5, numSensors=2)

#     # model = NeuralNetwork.Model.load("data/AccModel01Dill")
#     # parameters = model.get_parameters()
#     # print(f'Model: {parameters}')
    

# if __name__ == "__main__": main()