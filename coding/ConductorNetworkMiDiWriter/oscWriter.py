import socketClient
import NeuralNetwork
import numpy as np
import pythonosc
import os.path
import dill
import socket
import struct
import time
import threading
from threading import Thread


### Almost there! 
### This module takes the gestures classes predicted by the neural network and associates them with OSC addresses and data.
### Then it sends the data on to the VST to make sweet music.

class OSCWriter:

    def __init__(self, *, host="127.0.0.1", port="4000",predictions=[]):
        self.host = host
        self.port = port
        self.predictions = predictions
        self.ToFEnable = 0
        self.memorySize = 10000 #How many samples to save before purging
        self.memorySizeMin = 100 #How many predictions to keep on purge

    class Address:
        def __init__(self, *, address="/", ToFEnable=0, updateFlag=0, predictions=[], conditionType=0, conditionData=[], value=-1):
            self.address = address
            self.updateFlag = updateFlag
            self.conditionType = conditionType 
            ## 0 - checkHoldGesture(gesture, threshold) 
            #       checks for a gesture (conditionData[0]) 
            #       held for a threshold (conditionData[1])
            #       writes conditionData[3] to self.value
            self.conditionData = conditionData   ##
            self.value = value
            self.predictions = predictions
            self.ToFEnable = ToFEnable #IF 1 TOF sensor is enabled when address conditions are met

        
        def checkConditions(self):
            ## Checks the updated predictions list for conditions on each address
            ## Called once for each address in OSCWriter.conductor
            match self.conditionType:
                case 0:
                    if self.checkHoldGesture(self.conditionData[0], self.conditionData[1]) == 0:
                        self.value = self.conditionData[2]
                        self.updateFlag = 1

            return self.ToFEnable

        ## Methods to check conditions

        def checkHoldGesture(self, gesture, threshold):
            # print("checkHoldGesture")
            # print(f"gesture: {gesture}")
            # print(f"Value: {threshold}")
            # print(f"self.predictions: {self.predictions}")
            ## conditionType = 0
            #       checks for a gesture (conditionData[0]) 
            #       held for a threshold (conditionData[1])
            #       writes conditionData[3] to self.value
            if self.value == self.conditionData[2]:
                #No need to update if the value is already set
                return - 1
            lenPred = len(self.predictions)
            #print(f"Predictions Length: {lenPred}")
            if lenPred < threshold:
                startIdx = 0
            else:
                startIdx = lenPred-threshold

            for i in range(startIdx,lenPred):
                #print(f"self.predictions[i]: {self.predictions[i]}")
                if self.predictions[i] != gesture:
                    return -1
            self.ToFEnable = 1    
            return 0

    def getPredictions(self, prediction):
        # Called in socketClient after prediction has been made 
        # Hands prediction data to the OSCWriter
        self.predictions.append(prediction)
        self.conductor()
        self.garbageMan()      #Reset predictions when it goes above "self.memorySize"

    def sendOSC(self, value, address):
        print("sendOSC")
        # print(f"value: {value}")
        # print(f"address: {address}")
        # print(f"self.host: {self.host}")
        # print(f"self.host: {type(self.host)}")
        # print(f"self.host: {self.port}")
        # print(f"self.host: {type(self.port)}")
        # OSCsock = socket.socket()
        # OscAddress = self.host + address
        # #OSCsock.connect((OscAddress, self.port))
        # print("Connected to server")
        # print(f"Address: {OscAddress}")
        # print(f"Value: {value}")
        #print()

        # #try:
        # OSCsock.send(value);
       
        # OSCsock.close()

    def garbageMan(self):
        length = len(self.predictions)
        if length > self.memorySize:
            newPredict = []
            for i in range(length - self.memorySizeMin, length):
                newPredict[i] = self.predictions[i]
            
            self.predictions = newPredict

    ##TODO create makeAddress method

    def conductor(self):
        ##Conducts the process of gathering and sending data
        #Add as many addresses as you need to get the effects you want
        # Eventually I will write a address generator so you can create addresses and conditions        

        #1. Define Addresses
        address00 = self.Address(address="/address00", predictions=self.predictions, conditionType=0, conditionData=[0,3,127.0])
        
        #2 Create Address list
        addressList = [address00]
   
        for address in addressList:
            #2 Check conditions
            address.checkConditions()
            
            if address.updateFlag:

                #3 Toggle ToFEnable
                if address.ToFEnable:
                    self.ToFEnable = 1

        #         #4 Send the data
        #         OSCThread = Thread(target=self.sendOSC, args=(address.value, address.address,))
        #         OSCThread.start()
        
        # while threading.active_count() > 1:    #wait for the last threads to finish processing
        #     #print(f'threading.active_count(): {threading.active_count()}')
        #     OSCThread.join()
           

    

# def main():

# if __name__ == "__main__": main()