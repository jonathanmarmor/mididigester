# MIDI Digester

The Echo Nest Remix API comes with a demo, enToMIDI by Brian Whitman [1], which attempts to transcribe any audio file using only Remix’s audio analysis data, resulting in a MIDI file. The purpose of the EN audio analysis data is to provide a summary of the data, not to do the source separation necessary for an accurate transcription. This means the resulting MIDI file usually doesn’t sound much like the input.

MIDI Digester is a very small script [2] that runs audio through enToMIDI, plays back the resulting MIDI using Quicktime and its built in piano synthesizer, records the audio with sax, then repeats the process as many times as you want. Each repetition strips away more of the original musical material and accumulates the sound of enToMIDI.

The demo [3] of this script uses a 6 second MIDI version of the traditional bluegrass tune “The Groundhog” played by the same Quicktime piano synthesizer as input audio.

[1] https://github.com/echonest/remix/blob/master/examples/midi/enToMIDI.py

[2] https://github.com/jonathanmarmor/mididigester

[3] https://soundcloud.com/jonathanmarmor/groundhog

Blog post: http://jonathanmarmor.com/post/66595252364/mididigester
