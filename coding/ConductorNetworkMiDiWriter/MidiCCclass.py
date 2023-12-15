import threading
from xml.sax.xmlreader import InputSource
import rtmidi
import time
from rtmidi.midiconstants import CONTROL_CHANGE
from scipy import signal
import sys
import numpy as np


# Sample class
class MidiModulationPlayer:
    def __init__(self, port_name=0, channel=0, cc_num=75, bpm=30, rate='w', min_val=80, max_val=127, shape="sine"):
        self.midiout = rtmidi.MidiOut()
        available_ports = self.midiout.get_ports()
        if available_ports:
            self.midiout.open_port(1)
        else:
            print(f"Could not find {port_name} in available ports. Opening the first port.")
            self.midiout.open_port(1)
   
        self.port_name = port_name
        self.channel = channel
        self.cc_num = cc_num
        self.bpm = bpm
        self.rate = rate
        self.min_val = min_val
        self.max_val = max_val
        self.shape = shape
        self.print_event = threading.Event()
        self.print_event.set()
        self.lock = threading.Lock()


        self.period = float(input("Enter period: "))
        self.beatMilis = float(input("Enter max duration: "))
        self.signal_invert = input("Invert the signal? (True/False): ").lower() in ['true', 't', 'yes', 'y']
        self.play_thread = threading.Thread(target=self.play_modulation_loop, args=(shape, period, max_duration, signal_invert))
        self.play_thread.start()

        #self.update_parameters(port_name, channel, cc_num, bpm, rate, min_val, max_val, shape)



    def update_parameters(self,port_name, channel, cc_num, bpm, rate, min_val, max_val, shape):
        with self.lock:
            self.port_name = port_name
            self.channel = channel
            self.cc_num = cc_num
            self.bpm = bpm
            self.rate = rate
            self.min_val = min_val
            self.max_val = max_val
            self.shape = shape

    def print_parameters_loop(self):
        while True:
            while self.print_event.is_set():
                with self.lock:
                    print(f"Channel: {self.channel}, CC Num: {self.cc_num}, BPM: {self.bpm}, Rate: {self.rate}, Min Val: {self.min_val}, Max Val: {self.max_val}, Shape: {self.shape}")
                time.sleep(1)
                
    def play_modulation(self, y, max_duration):
        pause_duration = max_duration / y.size
        for v in y:
            beatStart = int(time() * 1000)
            beatStop = beatStart + pause_duration
            v = self.convert_range(v, -1.0, 1.0, 0, 127)
            v = self.convert_range(v, 0, 127, self.min_val, self.max_val)
            # print(f"Mod: {v}")
            mod = ([CONTROL_CHANGE | self.channel, self.cc_num, v])
            self.midiout.send_message(mod)
            beatNow = int(time() * 1000)
            while beatNow < beatStop:
                time.sleep(beatStop - beatNow)
            
    def modulation_shape(self, shape, period, max_duration, signal_invert):
        x = np.arange(0, max_duration, 0.01)
        y = 1
        sig_invert = 1

        if signal_invert:
            sig_invert = -1

        if shape == 'sine':
            y = sig_invert * np.sin(2 * np.pi / period * x)
        elif shape == 'saw':
            y = sig_invert * signal.sawtooth(2 * np.pi / period * x)
        elif shape == 'square':
            y = sig_invert * signal.square(2 * np.pi / period * x)
        else:
            print("That wave is not supported")
            sys.exit()

        return y
    
    def getBeatMillis(self, duration):
        #beatMillis is 1000 * (noteFactor * bps) 
        # bps = 60 / self.bpm 
        
        if duration == 'w':
            # 1000 * (4 * 60/self.bpm) = self.beatMillis
            # eg. 1000 * 4 * (60/ 60 bpm) = 4000ms
            self.beatMillis = 4000 * (60/self.bpm)
        elif duration == 'h':
            # 1000 * (2 * 60/self.bpm) = self.beatMillis
            # eg. 1000 * 2 * (60/ 90 bpm) = 1333 ms
            self.beatMillis = 2000 * (60/self.bpm)
        elif duration == 'q':
             # 1000 * (1 * 60/self.bpm) = self.beatMillis
            # eg. 1000 * 1 * (60/ 120 bpm) = 500ms
            self.beatMillis = 1000 * (60/self.bpm)
        elif duration == 'e':
            # 1000 * (1 * 60/self.bpm) = self.beatMillis
            # eg. 1000 * 1 * (60/ 60 bpm) = 2000ms
            self.beatMillis = 500 * (60/self.bpm)
        elif duration == 's':
            # 1000 * (1 * 60/self.bpm) = self.beatMillis
            # eg. 1000 * 1 * (60/ 60 bpm) = 2000ms
            self.beatMillis = 250 * (60/self.bpm)
        else:
            return -1

        return 1 #returns time is miliseconds

    def play_modulation_loop(self, shape, period, max_duration, signal_invert):
        if self.getBeatMillis():
            modulation = self.modulation_shape(shape, period, max_duration, signal_invert)
            while True:
                self.play_modulation(modulation, dur)

    def convert_range(self, value, in_min, in_max, out_min, out_max):
        l_span = in_max - in_min
        r_span = out_max - out_min
        scaled_value = (value - in_min) / l_span
        scaled_value = out_min + (scaled_value * r_span)
        return np.round(scaled_value)

# Function to take user input and update the data
def get_user_input(obj):
    while True:
        command = input("Enter 'start' to start printing, 'stop' to stop printing, 'play' to play modulation, or 'update' to update parameters: ")
        if command == "start":
            obj.print_event.set()
        elif command == "stop":
            obj.print_event.clear()
            # if(play_thread):
            #     if play_thread.is_alive():
            #         play_thread.join()
        elif command == "play":
            shape = input("Enter modulation shape (sine/saw/square): ")
            period = float(input("Enter period: "))
            max_duration = float(input("Enter max duration: "))
            signal_invert = input("Invert the signal? (True/False): ").lower() in ['true', 't', 'yes', 'y']
            play_thread = threading.Thread(target=obj.play_modulation_loop, args=(shape, period, max_duration, signal_invert))
            play_thread.start()
        elif command == "update":
            port_name = input("Enter port number")
            channel = int(input("Enter new channel: "))
            cc_num = int(input("Enter new cc_num: "))
            bpm = input("Enter new bpm: ")
            rate = input("Enter new rate: ")
            min_val = int(input("Enter new min_val: "))
            max_val = int(input("Enter new max_val: "))
            shape = input("Enter new shape: ")
            obj.update_parameters(port_name, channel, cc_num, bpm, rate, min_val, max_val, shape)
        else:
            print("Invalid command.")

# Create an instance of the class
my_object = MidiModulationPlayer()

# Create a thread that calls the function with the object as an argument
input_thread = threading.Thread(target=get_user_input, args=(my_object,))
print_thread = threading.Thread(target=my_object.print_parameters_loop)

# Start both threads
input_thread.start()
print_thread.start()

# Join both threads to the main thread
input_thread.join()
print_thread.join()

def main():
    midi00 = MidiModulationPlayer(port_name=0, channel=0, cc_num=75, bpm=30, rate='w', min_val=80, max_val=127, shape="sine")

if __name__ == "__main__": main()

# Testing Checklist
# 1. Test that you can send MIDI messages with default InputSource (default settings)
# 2. port_name update port name to match your midi port number
#3.  channel test switching channels 1-16 make sure all channels fuction correctly
# 4. cc_num  test diffrent midi cc numbers and verify if your able to match them
# 5. bpm: modify  bpm while mod is playing, verify speed of modulation changes
# 6. rate modufy rate through all values (w, h, q, e, s)
# 7. min_val modify min value, see what happens when its higher than max value
# 8. max_val do same test as min_val 
# 9. cycle through diffrent shapes (sine, saw, square) 

# Try to document everything thats going wrong
# I need to figure out how to stop multiple threads being created for a single midi CC