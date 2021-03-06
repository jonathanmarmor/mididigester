# MIDI Digester

![](http://media.tumblr.com/f6e4c701b922ab81d2e7cd271759c734/tumblr_inline_mw2b22oWMs1qj7ql5.png)

[Hear a demo!](https://soundcloud.com/jonathanmarmor/groundhog)

The [Echo Nest Remix API](http://echonest.github.io/remix/) comes with a demo, [enToMIDI](https://github.com/echonest/remix/blob/master/examples/midi/enToMIDI.py) by [Brian Whitman](http://notes.variogr.am/), which attempts to transcribe any audio file using only Remix's audio analysis data, and spits out a MIDI file. The purpose of the EN audio analysis data is to provide a summary of the music, not to do the source separation necessary for an accurate transcription. This means the resulting MIDI file usually doesn't sound much like the input.

MIDI Digester is a [very small script](https://github.com/jonathanmarmor/mididigester) that runs audio through enToMIDI, renders the resulting MIDI using [timidity](http://timidity.sourceforge.net/), runs the resulting audio through enToMIDI, renders the resulting MIDI using timidity, runs the resulting audio through enToMIDI, renders the resulting MIDI using timidity, runs the resulting audio through enToMIDI, renders the resulting MIDI using timidity, runs the resulting audio through enToMIDI, renders the resulting MIDI using timidity, runs the resulting audio through enToMIDI, renders the resulting MIDI using timidity, etc, as many times as you want. Each repetition strips away more of the original musical material and accumulates the sound of enToMIDI.

Check out [this demo](https://soundcloud.com/jonathanmarmor/groundhog) which "digests" a 7.66 second excerpt of the traditional bluegrass tune "The Groundhog" played by the same Quicktime piano synthesizer as was used for the original performance.


## Install Dependencies

Install numpy and The Echo Nest Remix API Python library:

    pip install -r requirements.txt

Install ffmpeg:

    brew install ffmpeg
    sudo ln -s `which ffmpeg` /usr/local/bin/en-ffmpeg

## Run it

    ./mididigester <input wav audio file> [<recursion depth>]
