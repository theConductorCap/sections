"""
Description:
This Python script defines a MidiBuilder class that facilitates the creation of MIDI messages. It includes functionalities to generate MIDI note data, MIDI control change data,
and MIDI control time of flight (Tof) data. The script uses various attributes and methods to build MIDI messages based on the control type selected in the GUI, 
such as MIDI channel, note values, velocity, modulation shapes, control change values, etc.

Special thanks to Jor van der Poel's tutorial on Udemy for descibing how to implement Midi CC modulation https://www.udemy.com/course/learning-python-with-ableton-live/
Variables:

- Rate: Class holding different note rates - whole, half, triplet, quarter, eighth, sixteenth.
- MidiBuilder: Class responsible for constructing MIDI messages with various parameters:
    - dataType: Type of MIDI data (0 for note data, 1 for creating Midi mod control changes, 2 for MidiCC messages using the Tof data).
    - midiMessage: MIDI message data (note values or control change values).
    - ch: MIDI channel.
    - note: MIDI note.
    - velocity: MIDI note velocity.
    - shape: Modulation shape for control change data (sine, saw, square).
    - signal_invert: Flag to invert the signal.
    - midiCC_ch: MIDI control change channel.
    - min_val: Minimum value for control change data.
    - max_val: Maximum value for control change data.
    - deltaToF: Delta time of flight for control Tof data.
    - oldTof: Old time of flight for control Tof data.
    - newTof: New time of flight for control Tof data.
    - rate: Rate of MIDI note data (whole, half, triplet, quarter, eighth, sixteenth).
    - midiCCnum: MIDI control change number.
    - threshold: Threshold value for generating delta time of flight array.

Functions/Methods:
- modulation_shape(): Generates a modulation waveform based on specified shapes (sine, saw, square).
- convert_range(): Converts the range of values from one scale to another.
- generate_deltaTof_array(): Generates an array of delta time of flight based on threshold and new/old time of flight values.
- multiply_rate(): Converts the rate of notes to numeric values for calculations.
- build_midi(): Constructs MIDI messages based on specified data types and parameters.
- MIDIControlChange: Inner class to create MIDI control change messages.
    - get_midi_cc(): Returns MIDI control change messages.
- MIDINoteMessage: Inner class to create MIDI note messages.
    - get_midi(): Returns MIDI note messages.

Note: The script also includes commented-out code demonstrating the usage of MidiBuilder for different types of MIDI data construction.
"""

import numpy as np
from scipy import signal
from rtmidi.midiconstants import CONTROL_CHANGE
import matplotlib.pylab as plt
import time


class Rate:
    whole = 'w'
    half = 'h'
    triplet = 't'
    quarter = 'q'
    eighth = 'e'
    sixteenth = 's'
    
class MidiBuilder:
    def __init__(self, dataType=0, midiMessage=[], ch=0, note=0, velocity=0, shape=0, signal_invert=0, midiCC_ch=0, min_val=0, max_val=127, deltaToF=0, oldTof=0, newTof=0, rate=Rate.whole, midiCCNum=75.):
        self.dataType = dataType
        self.midiMessage = midiMessage
        self.ch = ch
        self.note = note
        self.velocity = velocity
        self.shape = shape
        self.signal_invert = signal_invert
        self.midiCC_ch = midiCC_ch
        self.min_val = min_val
        self.max_val = max_val
        self.deltaToF = deltaToF
        self.oldTof = oldTof
        self.newTof = newTof
        self.rate = rate
        self.midiCCnum = midiCCNum
        self.threshold = 1  # Adjust this threshold as needed


    def modulation_shape(self):
        x = np.arange(0, 1 / self.multiply_rate(self.rate), 0.01)

        y = 1
        sig_invert = 1

        if self.signal_invert:
            sig_invert = -1

        if self.shape == 'sine' or 0:  # 'sine'
            y = sig_invert * np.sin(2 * self.multiply_rate(self.rate) * np.pi * x)
        elif self.shape == 'saw' or 1:  # 'saw'
            y = sig_invert * signal.sawtooth(2 * self.multiply_rate(self.rate) * np.pi * x)
        elif self.shape == 'square' or 2:  # 'square'
            y = sig_invert * signal.square(2 * self.multiply_rate(self.rate) * np.pi * x)
        # else:
        #     #print("That wave is not supported")

        return y

    def convert_range(self, value, in_min, in_max, out_min, out_max):
        l_span = in_max - in_min
        r_span = out_max - out_min
        scaled_value = (value - in_min) / l_span
        scaled_value = out_min + (scaled_value * r_span)
        return np.round(scaled_value)

    def generate_deltaTof_array(self):
            deltaArray = []

            if abs(self.newTof - self.oldTof) > self.threshold:
                if self.newTof > self.oldTof:
                    deltaArray = list(range(self.oldTof, self.newTof + 1))
                elif self.newTof < self.oldTof:
                    deltaArray = list(range(self.oldTof, self.newTof - 1, -1))

            self.oldTof = self.newTof
            return deltaArray

    def multiply_rate(self, rate):
        if rate == Rate.whole:
            return 1
        elif rate == Rate.half:
            return 2
        elif rate == Rate.triplet:
            return 3
        elif rate == Rate.quarter:
            return 4
        elif rate == Rate.eighth:
            return 8
        elif rate == Rate.sixteenth:
            return 16
        else:
            return 1  # Default value for an unknown note value

    def build_midi(self):
        midi_array = []

        if self.midiMessage is None:
            midi_array =  []

        if self.dataType in [1, '1']:  # MIDI note data
            if isinstance(self.midiMessage, int):
                for _ in range(self.multiply_rate(self.rate)):
                    note = int(self.midiMessage)
                    note_on = self.MIDINoteMessage(ch=self.ch, note=note, velocity=self.velocity)
                    midi_array.append(note_on.get_midi())

                    note_off = self.MIDINoteMessage(ch=self.ch, note=note, velocity=0)
                    midi_array.append(note_off.get_midi())
            else:
                for _ in range(self.multiply_rate(self.rate)):
                    for note in self.midiMessage:
                        note_on = self.MIDINoteMessage(ch=self.ch, note=note, velocity=self.velocity)
                        midi_array.append(note_on.get_midi())

                        note_off = self.MIDINoteMessage(ch=self.ch, note=note, velocity=0)
                        midi_array.append(note_off.get_midi())

        elif self.dataType in [0, '0']:  # MIDI control change data
            waveform = self.modulation_shape()
            waveform = self.convert_range(waveform, -1.0, 1.0, 0, 127)
            waveform = self.convert_range(waveform, 0, 127, self.min_val, self.max_val)
            for _ in range(self.multiply_rate(self.rate)):
                for value in waveform:
                    midiCC = self.MIDIControlChange(channel=self.ch, control_number=self.midiCCnum, control_value=value)
                    midi_array.append(midiCC.get_midi_cc())

        elif self.dataType in [2, '2']:  # MIDI control Tof data
            tof_delta_array = self.generate_deltaTof_array()
            for value in tof_delta_array:
                midiCC = self.MIDIControlChange(control_number=self.midiCCnum, channel=self.ch, control_value=value)
                midi_array.append(midiCC. get_midi_cc())
                
        elif self.dataType in [3, '3']:
            midi_array = []

        return midi_array  # Moved the return statement outside the if-elif-else block


    class MIDIControlChange:
        def __init__(self, control_number, control_value, channel=0):
            self.control_number = control_number
            self.control_value = control_value
            self.channel = channel

        def get_midi_cc(self):
            return [CONTROL_CHANGE |  int(self.channel), int(self.control_number),  int(self.control_value)]

    class MIDINoteMessage:
        def __init__(self, ch=0, note=0, velocity=0):
            self.ch = ch
            self.note = note
            self.velocity = velocity

        def get_midi(self):
            noteON = [int(self.ch) + 0x90, int(self.note), int(self.velocity)]
            noteOFF = [int(self.ch) + 0x80, int(self.note), int(self.velocity)]
            return noteON

# def __init__():
#     # # Creating instances of MidiBuilder class
    
#     # # Builder for MIDI note data
#     # builder1 = MidiBuilder(dataType=0, midiMessage=[60, 62, 64], ch=0, velocity=64)
    
#     # # Builder for MIDI control change data
#     # builder2 = MidiBuilder(dataType=1, shape=0, signal_invert=0, midiCC_ch=1, min_val=0)
    
#     # # Builder for MIDI control Tof data
#     # builder3 = MidiBuilder(dataType=2, midiCC_ch=2, oldTof=65, newTof=75)
    
#     # # Printing the results
    
#     # #print("Builder 1 - MIDI Note Data:")
#     # result1 = builder1.build_midi()
#     # for midi in result1:
#     #     #print(midi)
    
#     # #print("\nBuilder 2 - MIDI Control Change Data:")
#     # result2 = builder2.build_midi()
#     # for midi in result2:
#     #     #print(midi)
    
#     # #print("\nBuilder 3 - MIDI Control Tof Data:")
#     # result3 = builder3.build_midi()
#     # for midi in result3:
#     #     #print(midi)

