import socket
import struct
import time
import numpy as np

numSensors = 2
y = []


# socketClient.GetData.receiveBytes():
# called in thread in socketClient.GetData.getSample()


Start = int(time.time())

class GetData:
    
    def __init__(self, *, host="192.168.4.1", port=80, packetSize=1, numSensors=4, pathPreface='data/data', labelPath="Test", label=0, getTraining=True):
        self.host = host
        self.port = port
        self.packetSize = packetSize
        self.numSensors = numSensors
        self.packetData = np.zeros([1, self.packetSize * self.numSensors * 3]) #one packet of data corresponding to a gesture - 3 axis * number of sensors times the number of samples per gesture
        #self.packetArr = np.zeros([1, self.packetSize * self.numSensors * 3]) #An array of packets (gestures) used while collecting data for training
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
        self.sock = socket.socket()    # One Socket connection to rule them all
        self.sockRecursionCount = 0
        self.sockConnection = 0
        
        while self.makeSockConnection() == -1:
            print("Trying to make a socket connection")
            time.sleep(2)
        
        print("Connected to The Conductor!")
        
        
    def makeSockConnection(self):        #self.sock.close()
        print()
        print("makeSockConnection()")
        print(f'dataTx: {self.dataTx}')
        print(f'host {self.host}')
        print(f'port: {self.port}')
        try:
            self.sock.connect((self.host, self.port))

        except socket.timeout as err:
            print(f"TCP/IP Socket Timeout Error {self.sockRecursionCount}: {err}")
            return -1

        except socket.error as err:
            print(f"TCP/IP Socket Error: {err}")
            return -1
            #self.sock.close()
            #self.socket.create_connection((self.host, self.port), timeout=2)
            #self.sock.connect((host, port), timeout=2)

        return 1
        
    
    def promptServer(self, dataTx, host, port, rcount):
        print()
        print("promptServer")
        print(f'dataTx: {dataTx}')
        # print(f'host {host}')
        # print(f'port: {port}')            

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
                print(f"Failed transmission: {self.dataTx}, length: {len(self.dataTx)}")
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
                    print(f"Sent Data after {rcount + 1} tries")
                    self.host = host
                    self.port = port
                    return 1
            else:
                print(f'Fatal Error: SocketBroken')
                #print(f"TCP/IP Socket Error: {err}")
                print(f"Failed transmission: {self.dataTx}, length: {len(self.dataTx)}")
                self.sockRecursionCount = 0
                return -1

        print(f"Sent Data after {rcount + 1} tries")
        self.host = host
        self.port = port
        return 1

    def receiveBytes(self, dataTx, host, port):
        #Checks the connection to the servers, sends the prompt and then receives numSensors * 3 bytes
        #Collects one sample and returns the data as a byte array
        count = 0
        #sock = socket.socket()
        print("receiveBytes()")
        print(f'dataTx: {dataTx}')  
        #dataTx = struct.pack("=B", 34)  
        print("Sending prompt to server")
        #print(f'dataTx: {dataTx}') 
        if self.promptServer(dataTx, host, port, 0) == 1:
            print("Prompt Success") 
        else:       
            print("Failed Prompt")
            return -1   
        
        #Now receive the response
        #y = self.sock.recv(numSensors * 3)
        print(f'y at the start: {y}')
        self.y = [] #Reset y
        a = 0
        errorCount = 0
        #sampleRxStartMS = int(time.time() * 1000)
        while a < ((numSensors * 3 + self.extraRxByte)):                #iterate through the number of sensors * the number of bytes per sample
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
        response0 = self.receiveBytes(self.dataTx, self.host, self.port)
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
    
def main():
    
    # print("Hello!")

    dataStream = GetData(numSensors=4, pathPreface='data/test')

    # print("Start 0xFF byte")
    # sampleRxStartMS = int(time.time() * 1000)
    # dataStream.receiveBytes(dataStream.dataTx, dataStream.host, dataStream.port)
    # sampleRxStopMS = int(time.time() * 1000)
    # sampleRxTimeMS = sampleRxStopMS - sampleRxStartMS
    # print(f'Sample receive time in ms: {sampleRxTimeMS}')

    # print("Start 0x0F byte")
    # dataStream.dataTx = struct.pack("=B", 0x0F)
    # dataStream.extraRxByte = 1
    # sampleRxStartMS = int(time.time() * 1000)
    # dataStream.receiveBytes(dataStream.dataTx, dataStream.host, dataStream.port)
    # sampleRxStopMS = int(time.time() * 1000)
    # sampleRxTimeMS = sampleRxStopMS - sampleRxStartMS
    # print(f'Sample receive time in ms: {sampleRxTimeMS}')

    # message = "TELUSWiFi6810" + "__--__" + "aMLu4CR7yf" + "__--__"
    
    # dataStream.extraRxByte = 0
    # dataStream.socketSendStr(message)


    i = 0
    sample100RxStartMS = int(time.time() * 1000)
    while i < 75:
        print()
        print(f'Sample: {i}')
        dataStream.receiveBytes(dataStream.dataTx, dataStream.host, dataStream.port)
        if dataStream.dataTx == 0xFF:
            dataStream.extraRxByte = 1
            dataStream.dataTx = struct.pack("=B", 0x0F)
        elif dataStream.dataTx == 0x0F:
            dataStream.extraRxByte = 1
            dataStream.dataTx = struct.pack("=B", 0xFF)
        i += 1
    sample100RxStopMS = int(time.time() * 1000)
    sample100RxTimeMS = sample100RxStopMS - sample100RxStartMS
    print(f'10 Sample receive time in ms: {sample100RxTimeMS}')


if __name__ == "__main__": main()