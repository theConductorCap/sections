"""
Description:
This Python script defines a Metronome class that synchronizes MIDI events to a global clock. It calculates time delays for array-type MIDI commands based on beats per minute (BPM) and handles starting/stopping the metronome. Additionally, it offers functionality to calculate time slices for MIDI events and determine subdivision counts based on note values.

Class and Methods:
- Metronome: Class representing a metronome for MIDI event synchronization.
    - __init__(): Initializes the Metronome instance with parameters:
        - bpm: Beats per minute (default: 60).
        - startFlag: Flag indicating the start state of the metronome (default: False).
        - BPM_millis: Time in milliseconds per beat for the metronome (default: 0).
        - doneFlag: Flag indicating the completion of a time interval (default: 0).
    - timer_function(): Thread function to simulate a metronome ticking at specified intervals.
    - startMetro(): Starts or stops the metronome based on the offONState parameter.
    - getTimeTick(): Calculates the time slice for MIDI events based on the BPM and MIDI array length.
    - getSubdivisionCount(): Determines the subdivision count based on note values.

Functionality:
- The Metronome class handles the initialization of metronome parameters such as BPM, start/stop flags, and time calculations.
- It provides methods to start or stop the metronome, using threading to simulate metronome ticks at specific intervals based on BPM.
- The getTimeTick() method calculates time slices for MIDI events, taking into account the BPM and MIDI array length, or a default time slice if the array is None.
- The getSubdivisionCount() method determines the subdivision count based on different note values (whole, half, triplet, quarter, eighth, sixteenth).

Note: The script does not include an __init__ block for execution as it is designed to be imported and utilized in another Python file or program.
"""


import time
import threading
import buildMidi


class Metronome:
    def __init__(self, bpm=60, startFlag=False, BPM_millis=0, doneFlag = 0):
        self.bpm = bpm
        self.startFlag = startFlag
        self.stopFlag = False
        self.BPM_millis = BPM_millis
        self.doneFlag = doneFlag

    def timer_function(self, interval):
        while not self.stopFlag:
            print(f"Timer: {interval} seconds")
            time.sleep(interval)
            self.doneFlag = 1

    def startMetro(self, offONState):
        self.startFlag = offONState
        self.BPM_millis = (60 / self.bpm) * 1000
        if self.startFlag:
            timer_thread = threading.Thread(target=self.timer_function, args=(self.BPM_millis / 1000,))
            timer_thread.start()
            print("Metronome started.")
        else:
            self.stopFlag = True
            print("Metronome stopped.")

    def getTimeTick(self, midiArray = []):
  
        if midiArray == None:
            timeSlice = (60 / self.bpm) * 1000
        else:
            midiCount = len(midiArray)
            self.BPM_millis = (60 / self.bpm) * 1000
            if(midiCount == 1):
                timeSlice = self.BPM_millis/((midiCount))
            else:
                timeSlice = self.BPM_millis/((midiCount-1))
        return timeSlice

    @staticmethod
    def getSubdivisionCount(noteVal):
        if noteVal == 'w':
            return 1
        elif noteVal == 'h':
            return 2
        elif noteVal == 't':
            return 3
        elif noteVal == 'q':
            return 4
        elif noteVal == 'e':
            return 8
        elif noteVal == 's':
            return 16
        else:
            return 1  # Default value for an unknown note value

