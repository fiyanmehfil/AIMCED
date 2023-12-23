# -*- coding: utf-8 -*-
"""AI_MusicGenerationLSTM.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1gCLV7ABzmkXgQ1YivjiO1JzTTG8JnGcA
"""

import urllib
testfile = urllib.request.urlretrieve("https://raw.githubusercontent.com/mochiron-desu/kaggleJSON/main/kaggle.json", "kaggle.json")
! pip install kaggle
! mkdir ~/.kaggle
! cp kaggle.json ~/.kaggle
! chmod 600 ~/.kaggle/kaggle.json
! kaggle datasets download -d imsparsh/lakh-midi-clean

!unzip lakh-midi-clean.zip -d midi-files/

!ls midi-files/Whitney_Houston

from google.colab import drive
drive.mount('/content/drive')

from tensorflow.keras.layers import BatchNormalization

!pip install --upgrade --user keras

import glob
import pickle
import numpy
import shutil
import os
from datetime import date
from music21 import converter, instrument, note, chord, stream
from keras.models import Sequential
from keras.layers import Dense
from keras.layers import Dropout
from keras.layers import LSTM
from keras.layers import Activation
from keras.layers import BatchNormalization as BatchNorm
from keras import utils

from keras.callbacks import ModelCheckpoint
from keras.callbacks import EarlyStopping

"""+++##Training

###Function Declaration for Training.
Check list
- Check the output directory
- Check the midi directory
- If new ds then remove tthe load weights
"""

def get_notes():
    """ Get all the notes and chords from the midi files in the ./midi_songs directory """
    notes = []

    for file in glob.glob("/content/midi-files/Whitney_Houston/*.mid"):
        midi = converter.parse(file)

        print("Parsing %s" % file)

        notes_to_parse = None

        try: # file has instrument parts
            s2 = instrument.partitionByInstrument(midi)
            notes_to_parse = s2.parts[0].recurse()
        except: # file has notes in a flat structure
            notes_to_parse = midi.flat.notes

        for element in notes_to_parse:
            if isinstance(element, note.Note):
                notes.append(str(element.pitch))
            elif isinstance(element, chord.Chord):
                notes.append('.'.join(str(n) for n in element.normalOrder))

    with open('/content/drive/MyDrive/output/notes', 'wb') as filepath:
        pickle.dump(notes, filepath)

    return notes

def prepare_sequences(notes, n_vocab):
    """ Prepare the sequences used by the Neural Network """
    sequence_length = 100

    # get all pitch names
    pitchnames = sorted(set(item for item in notes))

     # create a dictionary to map pitches to integers
    note_to_int = dict((note, number) for number, note in enumerate(pitchnames))

    network_input = []
    network_output = []

    # create input sequences and the corresponding outputs
    for i in range(0, len(notes) - sequence_length, 1):
        sequence_in = notes[i:i + sequence_length]
        sequence_out = notes[i + sequence_length]
        network_input.append([note_to_int[char] for char in sequence_in])
        network_output.append(note_to_int[sequence_out])

    n_patterns = len(network_input)

    # reshape the input into a format compatible with LSTM layers
    network_input = numpy.reshape(network_input, (n_patterns, sequence_length, 1))
    # normalize input
    network_input = network_input / float(n_vocab)

    network_output = utils.to_categorical(network_output)

    return (network_input, network_output)

def create_network(network_input, n_vocab):
    """ create the structure of the neural network """
    print(f"NETWORK INPUT:{network_input.shape[1]},{network_input.shape[2]}")
    print(f"NVOCAB:{n_vocab}")
    model = Sequential()
    model.add(LSTM(
        512,
        input_shape=(network_input.shape[1], network_input.shape[2]),
        recurrent_dropout=0.3,
        return_sequences=True
    ))
    model.add(LSTM(512, return_sequences=True, recurrent_dropout=0.3,))
    model.add(LSTM(512))
    model.add(BatchNorm())
    model.add(Dropout(0.3))
    model.add(Dense(256))
    model.add(Activation('relu'))
    model.add(BatchNorm())
    model.add(Dropout(0.3))
    model.add(Dense(n_vocab))
    model.add(Activation('softmax'))
    model.compile(loss='categorical_crossentropy', optimizer='rmsprop')

    return model

def train(model, network_input, network_output):
    """ train the neural network """
    filepath = "/content/drive/MyDrive/Weights/weights-improvement-{epoch:02d}-{loss:.4f}-bigger.hdf5"
    checkpoint = ModelCheckpoint(
        filepath,
        monitor='loss',
        verbose=0,
        save_best_only=True,
        mode='min'
    )
    # earlystopping=EarlyStopping(
    #     monitor='loss',
    #     patience=2,
    #     verbose=1,
    #     mode="min",
    # )

    # Call Backs with Early Stopping
    # callbacks_list = [checkpoint,earlystopping]

    #Call Backs without early stopping
    callbacks_list = [checkpoint]

    model.load_weights("/content/drive/MyDrive/Weights/weights-improvement-10-2.8704-bigger.hdf5")

    model.fit(network_input, network_output, epochs=200, batch_size=128, callbacks=callbacks_list)

"""###Model preprocessing."""

notes = get_notes()
n_vocab = len(set(notes))
network_input, network_output = prepare_sequences(notes, n_vocab)

"""###Model Training"""

model = create_network(network_input, n_vocab)

train(model, network_input, network_output)

import numpy as np
from sklearn.metrics import confusion_matrix, accuracy_score

# Assuming you have the necessary data loaded and preprocessed for prediction
# If not, you'll need to provide input data for prediction

# Assuming you have a model already created and trained
# If not, you'll need to load the model

# Make predictions
predictions = model.predict(network_input)
predicted_classes = np.argmax(predictions, axis=1)
true_classes = np.argmax(network_output, axis=1)

# Calculate confusion matrix
confusion = confusion_matrix(true_classes, predicted_classes)

# Calculate accuracy
accuracy = accuracy_score(true_classes, predicted_classes)

print("Confusion Matrix:")
print(confusion)
print(f"Accuracy: {accuracy * 100:.2f}%")

# Identify the type of neural network
# Based on the provided code, it's a recurrent neural network (RNN) specifically using LSTM layers.

# epoch 9 at 6:09 pm 28-Oct-2022
# epoch 27 at 8:44 pm 28-Oct-2022
# epoch 35 at 9:58 pm 28-Oct-2022
# epoch 42 at 10:58 pm 28-Oct-2022

"""##Midi Generation

###Output Function Declaration
"""

!pip install pydub

!sudo apt-get install fluidsynth

!wget https://www.dropbox.com/s/4x27l49kxcwamp5/GeneralUser_GS_1.471.zip

!unzip /content/GeneralUser_GS_1.471.zip

import os
from pydub import AudioSegment

def midi_to_mp3(midi_file, soundfont, mp3_file):
    # Convert MIDI to WAV using fluidsynth
    wav_file = mp3_file.replace('.mp3', '.wav')
    os.system(f'fluidsynth -ni {soundfont} {midi_file} -F {wav_file} -r 44100')

    # Convert WAV to MP3 using pydub
    audio = AudioSegment.from_wav(wav_file)
    audio.export(mp3_file, format='mp3')

    # Remove temporary WAV file
    os.remove(wav_file)

# Example usage:
midi_file = "/content/drive/MyDrive/output/test_output-2023-11-01.mid"
soundfont = '/content/GeneralUser GS 1.471/GeneralUser GS v1.471.sf2'
mp3_file = 'output.mp3'
midi_to_mp3(midi_file, soundfont, mp3_file)

!pip install midi2audio

!midi2audio "/content/drive/MyDrive/output/test_output-2023-11-01.mid" output.wav

#@title Default title text
def prepare_sequences(notes, pitchnames, n_vocab):
    """ Prepare the sequences used by the Neural Network """
    # map between notes and integers and back
    note_to_int = dict((note, number) for number, note in enumerate(pitchnames))

    sequence_length = 100
    network_input = []
    output = []
    for i in range(0, len(notes) - sequence_length, 1):
        sequence_in = notes[i:i + sequence_length]
        sequence_out = notes[i + sequence_length]
        network_input.append([note_to_int[char] for char in sequence_in])
        output.append(note_to_int[sequence_out])

    n_patterns = len(network_input)

    # reshape the input into a format compatible with LSTM layers
    normalized_input = numpy.reshape(network_input, (n_patterns, sequence_length, 1))
    # normalize input
    normalized_input = normalized_input / float(n_vocab)

    return (network_input, normalized_input)

def create_network(network_input, n_vocab):
    """ create the structure of the neural network """
    model = Sequential()
    model.add(LSTM(
        512,
        input_shape=(network_input.shape[1], network_input.shape[2]),
        recurrent_dropout=0.3,
        return_sequences=True
    ))
    model.add(LSTM(512, return_sequences=True, recurrent_dropout=0.3,))
    model.add(LSTM(512))
    model.add(BatchNorm())
    model.add(Dropout(0.3))
    model.add(Dense(256))
    model.add(Activation('relu'))
    model.add(BatchNorm())
    model.add(Dropout(0.3))
    model.add(Dense(n_vocab))
    model.add(Activation('softmax'))
    model.compile(loss='categorical_crossentropy', optimizer='rmsprop')

    # Load the weights to each node
    weight_location = "/content/drive/MyDrive/Weights/weights-improvement-10-2.8704-bigger.hdf5" #@param {type:"string"}
    model.load_weights(weight_location)

    return model

def generate_notes(model, network_input, pitchnames, n_vocab):
    """ Generate notes from the neural network based on a sequence of notes """
    # pick a random sequence from the input as a starting point for the prediction
    start = numpy.random.randint(0, len(network_input)-1)

    int_to_note = dict((number, note) for number, note in enumerate(pitchnames))

    pattern = network_input[start]
    prediction_output = []

    # generate n notes
    no_notes = 100 #@param {type:"integer"}
    verboseFlag = 0 #@param {type:"slider", min:0, max:1, step:1}
    for note_index in range(no_notes):
        prediction_input = numpy.reshape(pattern, (1, len(pattern), 1))
        prediction_input = prediction_input / float(n_vocab)

        prediction = model.predict(prediction_input, verbose=verboseFlag)
        # LINE_UP = '\033[1A'
        # LINE_CLEAR = '\x1b[2K'
        # print(note_index)
        # print(LINE_UP, end=LINE_CLEAR)

        index = numpy.argmax(prediction)
        result = int_to_note[index]
        prediction_output.append(result)

        pattern.append(index)
        pattern = pattern[1:len(pattern)]

    return prediction_output

def create_midi(prediction_output):
    """ convert the output from the prediction to notes and create a midi file
        from the notes """
    offset = 0
    output_notes = []

    # create note and chord objects based on the values generated by the model
    for pattern in prediction_output:
        # pattern is a chord
        if ('.' in pattern) or pattern.isdigit():
            notes_in_chord = pattern.split('.')
            notes = []
            for current_note in notes_in_chord:
                new_note = note.Note(int(current_note))
                new_note.storedInstrument = instrument.Piano()
                notes.append(new_note)
            new_chord = chord.Chord(notes)
            new_chord.offset = offset
            output_notes.append(new_chord)
        # pattern is a note
        else:
            new_note = note.Note(pattern)
            new_note.offset = offset
            new_note.storedInstrument = instrument.Piano()
            output_notes.append(new_note)

        # increase offset each iteration so that notes do not stack
        offset += 0.5

    midi_stream = stream.Stream(output_notes)

    midi_stream.write('midi', fp='test_output.mid')
    path="/content/drive/MyDrive/output/test_output-"+str(date.today())+".mid"
    isExist = os.path.exists(path)
    titleIterator=1
    while (isExist):
        path="/content/drive/MyDrive/output/test_output-" + str(date.today()) +"-"+ str(titleIterator) + ".mid"
        isExist = os.path.exists(path)
        titleIterator+=1

    midi_stream.write('midi', fp=path)

!pip install tqdm

pip install pickle5

"""###Load Notes to train Model"""

import pickle
with open('/content/drive/MyDrive/output/notes', 'rb') as filepath:
    notes = pickle.load(filepath)

"""###Get all pitch Names and the lenght of notes

"""

# Get all pitch names
pitchnames = sorted(set(item for item in notes))
# Get all pitch names
n_vocab = len(set(notes))

"""###Prepare the network and model for generation"""

import numpy
network_input, normalized_input = prepare_sequences(notes, pitchnames, n_vocab)
model = create_network(normalized_input, n_vocab)

"""###Generate notes and output the Midi files"""

for i in range(1,10):
  prediction_output = generate_notes(model, network_input, pitchnames, n_vocab)
  create_midi(prediction_output)

# @title Default title text
import os
from pydub import AudioSegment

def midi_to_mp3(midi_file, soundfont, mp3_file):
    # Convert MIDI to WAV using fluidsynth
    wav_file = mp3_file.replace('.mp3', '.wav')
    os.system(f'fluidsynth -ni {soundfont} {midi_file} -F {wav_file} -r 44100')

    # Convert WAV to MP3 using pydub
    audio = AudioSegment.from_wav(wav_file)
    audio.export(mp3_file, format='mp3')

    # Remove temporary WAV file
    os.remove(wav_file)

# Example usage:
midi_file = "/content/drive/MyDrive/output/test_output-2023-11-02.mid"
soundfont = '/content/GeneralUser GS 1.471/GeneralUser GS v1.471.sf2'
mp3_file = 'output.mp3'
midi_to_mp3(midi_file, soundfont, mp3_file)

pip install pretty_midi

!midi2audio "/content/drive/MyDrive/output/test_output-2023-11-02.mid" output.wav

import os
import subprocess
from pydub import AudioSegment
from IPython.display import Audio

# Input MIDI file path
midi_file = '/content/drive/MyDrive/output/test_output-2023-11-02-20.mid'

# SoundFont file path
soundfont_file = 'FluidR3_GM.sf2'  # Replace with the path to your SoundFont file

# Output WAV file path
wav_file = 'output.wav'

# Convert MIDI to WAV using FluidSynth
fluidsynth_command = [
    'fluidsynth',
    '-ni',
    soundfont_file,
    midi_file,
    '-F',
    wav_file
]
subprocess.run(fluidsynth_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

# Specify the sampling rate of the audio (if known)
sampling_rate = 44100  # You can replace this with the correct sampling rate if known

# Display the generated WAV audio with the specified sampling rate
display(Audio(wav_file, rate=sampling_rate))

print(f'MIDI file converted to {wav_file}')

import os
import subprocess
from pydub import AudioSegment
from IPython.display import Audio, display
from google.colab import files  # Import the 'files' module for downloading

# Input MIDI file path
midi_file = '/content/drive/MyDrive/output/test_output-2023-11-02-19.mid'

# SoundFont file path
soundfont_file = 'FluidR3_GM.sf2'  # Replace with the path to your SoundFont file

# Output WAV file path
wav_file = 'output.wav'

# Convert MIDI to WAV using FluidSynth
fluidsynth_command = [
    'fluidsynth',
    '-ni',
    soundfont_file,
    midi_file,
    '-F',
    wav_file
]
subprocess.run(fluidsynth_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

# Specify the sampling rate of the audio (if known)
sampling_rate = 44100  # You can replace this with the correct sampling rate if known

# Display the generated WAV audio with the specified sampling rate
display(Audio(wav_file, rate=sampling_rate))

# Provide a download link for the WAV file
files.download(wav_file)

print(f'MIDI file converted to {wav_file}')

import librosa
import numpy as np

# Define the path to your audio file
audio_file = wav_file

# Load the audio file
y, sr = librosa.load(audio_file)

# Extract pitch (chroma feature)
chroma = librosa.feature.chroma_stft(y=y, sr=sr)
chroma_mean = np.mean(chroma, axis=1)

# Extract timbre (tonnetz feature)
tonnetz = librosa.feature.tonnetz(y=y, sr=sr)
tonnetz_mean = np.mean(tonnetz, axis=1)

# Extract intensity (root mean square energy)
rmse = np.sqrt(np.mean(y**2))

# Extract rhythm (tempo and beat frames)
tempo, beat_frames = librosa.beat.beat_track(y=y, sr=sr)
beat_frames_mean = np.mean(beat_frames)

# Mood classification criteria
moods = {
    'Happy': {
        'Chroma': 'High',
        'Intensity': 'Medium',
        'Timbre': 'Medium',
        'Pitch': 'Very High',
        'Rhythm': 'Very High',
    },
    'Exuberant': {
        'Chroma': 'High',
        'Intensity': 'High',
        'Timbre': 'Medium',
        'Pitch': 'High',
        'Rhythm': 'High',
    },
    'Energetic': {
        'Chroma': 'Medium',
        'Intensity': 'Very High',
        'Timbre': 'Medium',
        'Pitch': 'Medium',
        'Rhythm': 'High',
    },
    'Frantic': {
        'Chroma': 'High',
        'Intensity': 'High',
        'Timbre': 'Very High',
        'Pitch': 'Low',
        'Rhythm': 'Very High',
    },
    'Sad': {
        'Chroma': 'Medium',
        'Intensity': 'Medium',
        'Timbre': 'Very Low',
        'Pitch': 'Very Low',
        'Rhythm': 'Low',
    },

    'Calm': {
        'Chroma': 'Very Low',
        'Intensity': 'Very Low',
        'Timbre': 'Very Low',
        'Pitch': 'Medium',
        'Rhythm': 'Very Low',
    }
}

def classify_mood(features):
    best_matching_mood = 'Unknown'
    best_matching_criteria_count = 0

    for mood, criteria in moods.items():
        matching_criteria_count = sum(
            criteria[feature] == 'Very High' if features[feature] > 0.5 else
            criteria[feature] == 'High' if features[feature] > 0.3 else
            criteria[feature] == 'Medium' if features[feature] > 0.2 else
            criteria[feature] == 'Low' if features[feature] <= 0.2 else
            criteria[feature] == 'Very Low' if features[feature] <= 0.1 else
            0
            for feature in features
        )

        if matching_criteria_count > best_matching_criteria_count:
            best_matching_mood = mood
            best_matching_criteria_count = matching_criteria_count

    return best_matching_mood

# Classify the mood
features = {
    'Chroma': chroma_mean.mean(),
    'Intensity': rmse,
    'Timbre': tonnetz_mean.mean(),
    'Pitch': chroma_mean.mean(),
    'Rhythm': tempo,
}
mood = classify_mood(features)
print(f'Mood: {mood}')

print("Pitchnames:", pitchnames)