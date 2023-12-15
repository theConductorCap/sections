"""
Description:
This Python script defines a MiDiWriter class that interfaces with MIDI functionalities through the rtmidi library. It interprets gesture predictions from a neural network and associates them with MIDI channels and data to produce musical output. The script orchestrates the real-time generation of MIDI events based on neural network predictions and their associated musical attributes.

Classes and Methods:
- MiDiWriter: Class that coordinates the interpretation of neural network gesture predictions to generate MIDI events.
    - __init__(): Initializes the MiDiWriter instance with various parameters.
    - generate_midi_data(): Generates new MIDI data based on control parameters.
    - start_play_loop(): Starts the play loop for MIDI event generation.
    - update_playControl(): Updates the control flags for MIDI playback.
    - play_loop(): Manages the continuous loop for MIDI playback based on metronome timing and control flags.
    - refreshMidi(): Refreshes MIDI data based on updated control attributes.
    - reorder_held_notes(): Reorders held notes based on the specified order.
    - garbageMan(): Cleans up prediction data based on a specified memory size.
    - getPredictions(): Collects gesture predictions from the neural network for MIDI interpretation.
    - conductor(): Orchestrates the process of gathering and sending MIDI data based on control parameters and neural network predictions.

Inner Class:
- MidiControl: Inner class that encapsulates MIDI control attributes and methods.
    - __init__(): Initializes MidiControl instances with MIDI-related attributes.
    - changeRate(): Modifies the MIDI rate based on the specified rate value.
    - getBeatMillis(): Calculates the duration of a beat in milliseconds based on the specified rate.
    - checkConditions(): Checks conditions based on gesture thresholds for control behavior.
    - gestureThreshold(): Checks whether a specific gesture meets a threshold within the prediction data.
    - gestureTransition(): Checks transitions between two gestures with associated thresholds.

Functionality:
- The MiDiWriter class serves as a bridge between neural network gesture predictions and MIDI event generation.
- It utilizes multiple methods and control attributes to interpret and convert predicted gestures into MIDI data.
- The script incorporates methods for updating control parameters, managing MIDI data generation based on predictions, and orchestrating MIDI playback according to specified conditions.
- Inner class MidiControl encapsulates individual MIDI control attributes and methods for handling MIDI-related operations based on gesture predictions and control parameters.


"""


# Import standard library modules
from re import U
import time
import threading
from threading import Thread
import random

# Import third-party modules
import numpy as np
import rtmidi
from scipy import signal

# Import local modules
from metronome import Metronome
import buildMidi
from midiPlayer import MidiPlayer
from midiArp import MidiArp

### Almost there! 
### This module takes the gestures classes predicted by the neural network and associates them with OSC channeles and data.
### Then it sends the data on to the VST to make sweet music.

class MiDiWriter:

    def __init__(self, *, predictions=[], port_name=1, channel=0, cc_num=75, bpm=60, rate='w', ToFByte=-1, playControl = []):
        self.midiOut = rtmidi.MidiOut()
        self.midiIn = rtmidi.MidiIn()
        self.midiPortOut = port_name
        self.bpm = bpm
        self.predictions = predictions
        self.ToFEnable = 1
        self.memorySize = 1000 #How many samples to save before purging
        self.memorySizeMin = 100 #How many predictions to keep on purge
        self.ToFByte = ToFByte
        self.available_MiDiPortsOut = self.midiOut.get_ports()
        self.controlList = []
        self.available_MiDiPortsIn = self.midiIn.get_ports()
        self.metro = Metronome(bpm)
        self.play_loop_started = False
        self.playControl = playControl
        self.writerON = 0
        self.writerRate = rate
        self.midi_data_list = []
        self.busy = 0
        self.midiArp = MidiArp(midiIn_port_index = 2) #Need to add this to GUI

    def generate_midi_data(self):
        # Logic to generate new MIDI data
        self.refreshMidi()
        
    def start_play_loop(self):
        if not self.play_loop_started:
            # self.refreshMidi()  # Refresh MIDI data before starting the loop
            self.metro.startFlag = True
            self.metro.doneFlag = True
            play_thread = threading.Thread(target=self.play_loop, args=())
            play_thread.start()
            self.play_loop_started = True
            
    def update_playControl(self):
        self.playControl = []
  
        
        # Extracting control.startFlag attribute for each object using list comprehension
        self.playControl = [control.startFlag for control in self.controlList]

        # Printing the array of control.startFlag attributes
       # #print(self.playControl)

    def play_loop(self):
     
        while self.metro.startFlag:
            self.refreshMidi()
            # #print("Indices where elements are not zero:", non_zero_indices)
            self.metro.startFlag = self.writerON
            if self.writerON:
                self.update_playControl()
                if self.metro.doneFlag == 1:
                    threads = []
                    for i, (midi_player, midi_data) in enumerate(zip(self.midi_players, self.midi_data_list)):
                        threads.append(threading.Thread(target=midi_player.play_beat, args=(midi_data, self.playControl[i])))
                    for thread in threads:
                        thread.start()
                    for thread in threads:
                        thread.join()


    def refreshMidi(self):
        self.midiArp.update_Midi()  # Update MIDI information from midiArp just once for all controls
        
        time.sleep(0.03)
        self.midiArp.update_Midi()
    
        for control in self.controlList:
            if control.startFlag == 1:
                self.midiArp.order = control.direction
                self.midiArp.octave = control.octave
            arpNote = self.midiArp.update_Midi()  # Update MIDI information from midiArp just once for all controls

            control.changeRate(self.writerRate)
            control.midiBuilder.rate = control.beatLenStr
            control.midiBuilder.rate = control.beatLenStr
            control.midiBuilder.shape = control.waveform
            control.midiBuilder.newTof = control.controlValue

            # Update midiInput for each control from midiArp
            control.midiInput = self.midiArp.current_Midi
            control.midiBuilder.midiMessage = control.midiInput
            #print(f"refreshMidi notes {control.midiInput}")
            

            control.midiResults = control.midiBuilder.build_midi()
    
        self.midi_data_list = [control.midiResults for control in self.controlList]
        self.midi_players = [MidiPlayer(self.midiOut, self.metro.getTimeTick(midi_data), midi_data) for control, midi_data in zip(self.controlList, self.midi_data_list)]
        

    def reorder_held_notes(self, order):
        if order == 0:
            # Sort notes in ascending order
            self.midiArp.held_notes = set(sorted(self.midiArp.held_notes))
        elif order == 1:
            # Sort notes in descending order
            self.midiArp.held_notes = set(sorted(self.midiArp.held_notes, reverse=True))
        elif order == 2:
            # Shuffle notes randomly
            self.midiArp.held_notes = set(random.sample(self.midiArp.held_notes, len(self.midiArp.held_notes)))
        else:
            print(f"Could not find {self.direction} in available ports. Opening the first port.")
            #self.midiOut.open_port(1)
                  
    def garbageMan(self):
        length = len(self.predictions)
        if length > self.memorySize:
            self.predictions = [self.predictions[i] for i in range(length - self.memorySizeMin, length)]

    def getPredictions(self, prediction):
        #print()
        print('getPredictions()')
        # Called in socketClient after prediction has been made 
        # Hands prediction data to the OSCWriter
        self.predictions.append(prediction)
        self.conductor()
        self.garbageMan()      #Reset predictions when it goes above "self.memorySize"


    def conductor(self):
        print()
        print('conductor()')
  
        if not self.play_loop_started:  # Check if the play_loop has not started yet
            if self.writerON == True:
                # self.refreshMidi()
                self.metro.startFlag = True
                self.metro.doneFlag = True
                play_thread = threading.Thread(target=self.play_loop, args=())
                play_thread.start()
                self.play_loop_started = True  # Set the flag to True after starting play_loop
            
        ##Conducts the process of gathering and sending data
        #Called once per prediction loop
        #Add as many controles as you need to get the effects you want
        # Eventually I will write a control generator so you can create controles and conditions            
       
        self.ToFEnable = 1    #By default TOF is enabled
        #print(f'control List: {self.controlList}')
        for control in self.controlList:
            # control.startFlag = True
            # midi_player = MidiPlayer(self.midiOut, time_slice=self.metro.getTimeTick(control.midiResults), midi_data = control.midiResults)
            
            #2 Check conditions
            print(f'threadToggle: {control.threadToggle}')
            control.predictions = self.predictions     
            control.checkConditions()
            control.controlValue = self.ToFByte 
            #print(f'control enabled?: {control.updateFlag}')
            self.ToFEnable = 1 
            if control.updateFlag:
            
   
            # control.controlCounters[control.channel]  += 1 #Check the conditions then update the loop
            
                #3 Toggle ToFEnable / get ToFByte
                #TOF should be enabled all the time
                self.ToFEnable = 1   #control.ToFEnable
                # if self.ToFEnable:
                #     print(f'ToFByte: {self.ToFByte}')
                #     if self.ToFByte > 0 and self.ToFByte < 128:   #Make sure we have a valid ToF value
                #         control.controlValue = self.ToFByte    #ToF supplies the control value 
                #         # control.midiBuilder.newTof = control.controlValue
        self.garbageMan()
      


    ##############################################################################################################
    # ###           MidiControl
    # ############################################################################################################    
    class MidiControl:
        def __init__(self, *, controlLabel='', midiOut=None, ToFEnable=1, updateFlag=0, predictions=[], conditionType=0, conditionData=[[0,3], [1,3]], channel=None, controlNum=None, midiLoopCount = 0, rate=None, waveform=None, minimum=None, maximum=None, direction=None, controlType = 0, bpm=0, midiMessage=60, startFlag=0, octave=0, midiInput=[]):
            #Removed attributes:  value=-1, 
            
            self.midiLoopCount = midiLoopCount #Precious value fed in each time the loop runs
            self.controlLabel = controlLabel
            self.midiOut = midiOut
            self.bpm = bpm
            self.channel = channel
            self.controlNum = controlNum
            self.controlType = controlType  #0 modulate, 1 arpeggiate, 2 notes
            self.updateFlag = updateFlag
            #attributes provided by GUI
            self.rate = rate
            self.waveform = waveform
            self.mimimum = minimum
            self.maximum = maximum
            self.direction = direction
            ##ConditionType determines what methods will be used to determine when and which attributes to change
            #Parameters for condition checcking methods will be passed in conditionData[]
            ###Condition Type definitions:
             ## 0 - gestureThreshold(gesture, threshold) 
            #       checks for a gesture (conditionData[x][0]) 
            #       held for a threshold (conditionData[x][1])
            ## 1 
            self.conditionType = conditionType 
            self.conditionData = conditionData   ##
            #self.value = value
            self.predictions = predictions
            self.ToFEnable = ToFEnable #IF 1 TOF sensor is enabled when control conditions are met
            self.beatLenStr = 'w'
            self.beatMillis = self.getBeatMillis()
            self.velocity = 64  #default to halfway
            self.controlValue = 0 #default to zero so we can tell if there is a change
            self.note = 60 # default to middle C
            self.onNotOff = 0 #off by default
            self.midiMessage = midiMessage
            self.invert = 1 #1 or -1 only!
            #self.shape = 0 # 0 = sin; 1 = saw; 2 = square
            self.modLenS = 16 #The modulation duration in seconds
            self.min_val = 0
            self.max_val = 127
            self.period = 1
            self.thread = None
            # self.controllerType = controllerType
            self.threadToggle = 0 #toggle this within the thread to see what it is doing
            #self.max_duration = max_duration
            self.midiBuilder = buildMidi.MidiBuilder(dataType=self.controlType, midiMessage=self.midiMessage, ch=self.channel, velocity=self.velocity, rate=self.beatLenStr)
            self.midiResults = self.midiBuilder.build_midi()
            self.startFlag = startFlag
            
            #midiArp Attributes
            self.octave = octave
            #self.order = order
            self.midiInput = midiInput
              
        def changeRate(self, rate):  
            newRate = self.controlValue
            if newRate == 0:
                self.beatLenStr = rate
                #print(newRate)
            elif(newRate < 10):
                self.midiBuilder.rate = 's'
                self.beatLenStr = 's'
            elif( 10 < newRate and newRate < 20):
                self.midiBuilder.rate = 'e'
                self.beatLenStr = 'e'
            elif( 20 < newRate and newRate < 30):
                self.midiBuilder.rate = 'q'
                self.beatLenStr = 'q'
            elif( 30 < newRate and newRate < 40):
                self.midiBuilder.rate = 'h'
                self.beatLenStr = 'h'
            elif(40 < newRate):
                self.midiBuilder.rate = 'w'
                self.beatLenStr = 'w'
               
            #print(self.beatLenStr)
                
        def getBeatMillis(self):
        #beatMillis is 1000 * (noteFactor * bps) 
        # bps = 60 / self.bpm  
            if self.beatLenStr == 'w':
                # 1000 * (4 * 60/self.bpm) = self.beatMillis
                # eg. 1000 * 4 * (60/ 60 bpm) = 4000ms
                beatMillis = 4000 * (60/float(self.bpm))
            elif self.beatLenStr == 'h':
                # 1000 * (2 * 60/self.bpm) = self.beatMillis
                # eg. 1000 * 2 * (60/ 90 bpm) = 1333 ms
                beatMillis = 2000 * (60/float(self.bpm))
            elif self.beatLenStr == 'q':
                # 1000 * (1 * 60/self.bpm) = self.beatMillis
                # eg. 1000 * 1 * (60/ 120 bpm) = 500ms
                beatMillis = 1000 * (60/float(self.bpm))
            elif self.beatLenStr == 'e':
                # 1000 * (1 * 60/self.bpm) = self.beatMillis
                # eg. 1000 * 1 * (60/ 60 bpm) = 2000ms
                beatMillis = 500 * (60/float(self.bpm))
            elif self.beatLenStr == 's':
                # 1000 * (1 * 60/self.bpm) = self.beatMillis
                # eg. 1000 * 1 * (60/ 60 bpm) = 2000ms
                beatMillis = 250 * (60/float(self.bpm))
            else:
                beatMillis = 0

            return beatMillis #returns miliseconds / beat
   
        def checkConditions(self):
            ## Checks the updated predictions list for conditions on each control
            ## Called once for each control in OSCWriter.conductor
            print()
            print('checkConditions(self)')
            match int(self.conditionType):
                case 0:
                     ## ConditionType 0: Hold
                        # gestureThreshold(gesture, threshold) 
                        # [[ON POSITION, ON THRESHOLD], [OFF POSITION, OFFTHRESHOLD]]
                    if self.onNotOff == 1: #if on check if we need to turn it off
                        self.startFlag = 1
                        
                        #When Control is ON it uses the second list in conditionData to set gesture and threshold
                        #Set 
                        if self.gestureThreshold(self.conditionData[1][0], self.conditionData[1][1], 0) == 0:
                        #self.controlValue = self.conditionData[2]
                            self.updateFlag = 1
                            self.startFlag = 1
                        else:
                            self.updateFlag = 0
                            self.startFlag = 0
                    else: #When control is not activated...
                        self.startFlag = 0
                         #When Control is OFF it uses the first list in conditionData to set gesture and threshold
                        if self.gestureThreshold(self.conditionData[0][0], self.conditionData[0][1], 0) == 0:
                        #self.controlValue = self.conditionData[2]
                            self.updateFlag = 1
                            self.startFlag = 1
                        else:
                            self.updateFlag = 0
                            self.startFlag = 0
                            
                case 1:
                     ## ConditionType 1: Transition
                        # gestureThreshold(gesture, threshold) 
                        # [
                        # [[BEGIN ON POSITION, BEGIN ON THRESHOLD], [END ON POSITION, END ON THRESHOLD]], 
                        # [[BEGIN OFF POSITION, BEGIN OFF THRESHOLD], [END OFF POSITION, END OFF THRESHOLD]
                        # ]
                    if self.onNotOff == 1: #if on check if we need to turn it off
                        self.startFlag = 1
                        #gestureTransition(self, gesture1, threshold1, gesture2, threshold2, startIdx):
                        #When Control is ON it uses the second list in conditionData to set gesture and threshold
                        if self.gestureThreshold(self.conditionData[1][0][0], self.conditionData[1][0][0], self.conditionData[1][1][0], self.conditionData[1][1][0], 0) == 0:
                            
                        #self.controlValue = self.conditionData[2]
                            self.updateFlag = 1
                            self.startFlag = 1
                        else:
                            self.updateFlag = 0
                            self.startFlag = 0
                    else:
                        self.startFlag = 0
                         #When Control is OFF it uses the first list in conditionData to set gesture and threshold
                        if self.gestureThreshold(self.conditionData[0][0][0], self.conditionData[0][0][0], self.conditionData[0][1][0], self.conditionData[0][1][0], 0) == 0:
                        #self.controlValue = self.conditionData[2]
                            self.updateFlag = 1
                            self.startFlag = 1
                        else:
                            self.updateFlag = 0
                            self.startFlag = 0
                            
                case _:
                    ## ConditionType 0: Hold 
                    # gestureThreshold(gesture, threshold) 
                    #       checks for a gesture (conditionData[0]) 
                    #       held for a threshold (conditionData[1])
                    #       writes conditionData[3] to self.value
                    if self.onNotOff == 1: #if on check if we need to turn it off
                        self.startFlag = 1
                        
                        #When Control is ON it uses the second list in conditionData to set gesture and threshold
                        if self.gestureThreshold(self.conditionData[1][0], self.conditionData[1][1], 0) == 0:
                        #self.controlValue = self.conditionData[2]
                            self.updateFlag = 1
                            self.startFlag = 1
                        else:
                            self.updateFlag = 0
                            self.startFlag = 0
                    else:
                        self.startFlag = 0
                            #When Control is OFF it uses the first list in conditionData to set gesture and threshold
                        if self.gestureThreshold(self.conditionData[0][0], self.conditionData[0][1], 0) == 0:
                        #self.controlValue = self.conditionData[2]
                            self.updateFlag = 1
                            self.startFlag = 1
                        else:
                            self.updateFlag = 0
                            self.startFlag = 0

#####################################################################################      
#Condition checking methods - called in checkConditions() based on switch case result
##################################################################################### 

        def gestureThreshold(self, gesture, threshold, startIdx):
            print("gestureThreshold")
            #startIdx counts back from the last element in the list
            # print(f"gesture: {gesture}")
            # print(f"Value: {threshold}")
            # print(f"self.predictions: {self.predictions}")
            ## conditionType = 0
            #       checks for a gesture (conditionData[0]) 
            #       held for a threshold (conditionData[1])
            #       writes conditionData[3] to self.value
            
            #Get index of starting point
            lenPred = len(self.predictions)
            #print(f"Predictions Length: {lenPred}")
            if lenPred < threshold:
                #startIdx = startIdx
                return -1
            else:
                loopIdx =  lenPred-(startIdx + threshold)

            #limit noise
            noisebudget = int(threshold/10) #All one in ten errors (for 90% neural network accuracy)
            noiseCount = 0
            for i in range(loopIdx,lenPred):
                #print(f"self.predictions[i]: {self.predictions[i]}")
                if self.predictions[i] != gesture:
                    noiseCount += 1
                    if noiseCount >= noisebudget:
                        return -1
            self.ToFEnable = 1    
            return 0
        
        def gestureTransition(self, gesture1, threshold1, gesture2, threshold2, startIdx):
            if self.gestureThreshold(gesture1, threshold1, startIdx) == 0:
                if self.gestureThreshold(gesture2, threshold2, startIdx + threshold1) == 0:
                    return 0
                else:
                    return -1
            else:
                return -1 

