"""
Description:
This Python script implements a MIDI arpeggiator (MidiArp) using the rtmidi library. The MidiArp class enables MIDI message processing for arpeggiating notes received from a MIDI input port. The arpeggiator can generate and manage a sequence of MIDI notes by adjusting the octave, order, and handling note events.

Class and Methods:
- MidiArp: Class representing the MIDI arpeggiator.
    - __init__(): Initializes the MidiArp instance with parameters:
        - midiIn_port_index: MIDI input port index (default: 3).
        - octave: Octave value for note manipulation (default: 2).
        - order: Order of note arrangement (default: 0 for ascending).
    - process_messages(): Processes incoming MIDI messages continuously when the arpeggiator is running.
    - _handle_midi_message(): Handles MIDI messages, adding or discarding notes based on note-on/off events.
    - start_processing_thread(): Starts a thread for processing MIDI messages.
    - stop_processing_thread(): Stops the MIDI message processing thread.
    - update_Midi(): Updates the sequence of MIDI notes based on held notes, octave, and order.
    - reorder_Midi(): Reorders the current MIDI notes based on specified order (ascending, descending, or random).
    - change_octave(): Adjusts the octave of the held MIDI notes.
    
Functionality:
- Upon instantiation, MidiArp initializes MIDI input port, holds notes, and sets default parameters.
- It continuously processes MIDI messages in a separate thread.
- The class handles incoming note-on and note-off MIDI messages, updating the held notes accordingly.
- The current sequence of held MIDI notes can be monitored and modified based on octave and order.
- The script demonstrates the functionality by instantiating MidiArp, starting a processing thread, and printing currently held notes in a loop until interrupted by a KeyboardInterrupt (Ctrl+C).
"""


import rtmidi
import threading
import time
import random

class MidiArp:
    def __init__(self, midiIn_port_index=3, octave=2, order=0):
        self.midi_in = rtmidi.MidiIn()
        self.midi_in.open_port(midiIn_port_index)
        self.held_notes = set()
        self.lock = threading.Lock()
        self.is_running = False
        self.octave = octave
        self.order = order
        self.current_Midi = []
        self.midiIn_port_index = midiIn_port_index

    def process_messages(self):
        try:
            while self.is_running:
                msg = self.midi_in.get_message()

                if msg:
                    with self.lock:
                        self._handle_midi_message(msg[0])

                time.sleep(0.001)

                # with self.lock:
                #     self.update_Midi()

        except KeyboardInterrupt:
            pass

        finally:
            self.midi_in.close_port()
            #print("MIDI input port closed.")

    def _handle_midi_message(self, msg):
        status_byte = msg[0]  # Status byte is the first element of the message
        note_value = msg[1]
        velocity = msg[2]

        if status_byte >> 4 == 0x9 and velocity != 0:  # Note-on
            self.held_notes.add(note_value)
        elif status_byte >> 4 == 0x8 or (status_byte >> 4 == 0x9 and velocity == 0):  # Note-off or Note-on with velocity 0
            self.held_notes.discard(note_value)
            
    def start_processing_thread(self):
        # if self.midi_in.is_port_open() == False:
        #      self.midi_in.open_port(self.midiIn_port_index)
        if not self.is_running:
            self.held_notes.clear
            self.current_Midi = []
            # if not self.midi_in.is_port_open:
            #     self.midi_in.open_port(midiIn_port_index)
            thread = threading.Thread(target=self.process_messages)
            self.is_running = True
            thread.start()

    def stop_processing_thread(self):
        self.is_running = False

    def update_Midi(self):
        if self.held_notes:
            
            self.current_Midi = sorted(self.held_notes)
            self.reorder_Midi()
            self.change_octave()
            
        else:
            self.current_Midi = []

    def reorder_Midi(self):
        if self.order == 0 or self.order == 'Up':
            self.current_Midi = sorted(self.current_Midi)
        elif self.order == 1 or self.order == 'Down':
            self.current_Midi = sorted(self.current_Midi, reverse=True)
        elif self.order == 2 or self.order == 'Random':
            random.shuffle(self.current_Midi)
        # else:
        #     #print("Invalid order. Use 0 for ascending, 1 for descending, or 2 for random.")

    def change_octave(self):
        if -2 <= int(self.octave) <= 2:
            self.current_Midi = [note_value + int(self.octave) * 12 for note_value in self.current_Midi]

def __init__():
    midiIn_port_index = 3  # MIDI input port index
    midi_note_manager = MidiArp(midiIn_port_index)  # Creating an instance of MidiArp
    
    # Starting the processing thread
    midi_note_manager.start_processing_thread()

    try:
        # Continuous monitoring of held notes
        while True:
            #print(f"Currently Held Notes: {midi_note_manager.current_Midi}")
            time.sleep(1)

    except KeyboardInterrupt:
        # Stopping the processing thread when interrupted
        midi_note_manager.stop_processing_thread()
