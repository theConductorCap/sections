# The Conductor
---

- [The Conductor](#the-conductor)
  - [Socket Client](#socket-client)
  - [Neural Network](#neural-network)
  - [MIDI Generation Software](#midi-generation-software)
    - [MidiWriter](#midiwriter)
    - [MidiBuilder](#midibuilder)
  - [Metronome](#metronome)
  - [MidiArp](#midiarp)
- [Legal Disclamer](#legal-disclamer)



## Socket Client

The file socketClient.py is responsible for collecting data from The Conductor's microconroller via WiFi and formats it for the neural network. 

There is one class called get data, which is instantiated on start up in uxWindowDev.py with the name dataStream.

Methods
    - processData() Takes raw bytes from WiFi and formats it into an array for the neural network
    - receiveBytes() Prompts The Conductor's microcontroller for data and receives that data as raw bytes
    - socketLoop() Orchestrates the process of receiving and processing data, and sends data to the neural network, and sends neural network results to the MidiWriter.
    - prepTraining() Compiles saved accelerometer data from log files into a set of randomized samples for training the neural network.
    - writetoCSV() A helper method that writes arbitrary data to a csv file
    - plotAcc() Plots incoming accelerometer data (not implemented)
    - createTrainingData() A helper method that creates a simple data set for testing the neural network.

## Neural Network

This file is responsible for the running the neural network. It is based on code samples from Harrison Kinsley & Daniel Kukieła’s Neural Networks From Scratch in Python. 

See the book or the github repository (https://github.com/Sentdex/nnfs) for more information or troubleshooting.


## MIDI Generation Software

This section covers the MIDI generation files in the conductor application. This is responsible for taking gesture data and generating MIDI messages from the predictions. The main class that handles MIDI data is the MidiWriter. 

### MidiWriter

MidiWriter is instantiated in uxWindowDev.py as writer where predictions from the nural network are passed to the writer called from ux.py. When the MIDI controls are configured inside the GUI the configuration file controls.csv is used to create midi controls inside the writer. 

writer.controlList takes the configuration of each control and initalizes the MIDI controls as writer.MidiControl(control paramiters)

When the Go button is pressed inside the GUI the writer begins playing MIDI by setting the flag writer.writerON and begins the MIDI input handeling for the arpeggiator with self.writer.midiArp.start_processing_thread(). 

The flag is reset when the stop button is pressed and the arpegiattor is also stopped with self.writer.midiArp.start_processing_thread().


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

### MidiBuilder

This Python script defines a MidiBuilder class that facilitates the creation of MIDI messages inside midiWriter.py. It includes functionalities to generate MIDI note data, MIDI control change data,
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

## Metronome

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

Note: The script does not include an __init__ block for execution as it is designed to be imported and utilized in midiWriter.py.

## MidiArp

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
- 

# Legal Disclamer
DISCLAIMER: The code in this repository is provided "as is" without warranty of any kind, express or implied, including but not limited to the warranties of merchantability, fitness for a particular purpose and noninfringement. In no event shall the authors or copyright holders be liable for any claim, damages or other liability, whether in an action of contract, tort or otherwise, arising from, out of or in connection with the code or the use or other dealings in the code.

 