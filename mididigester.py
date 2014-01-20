#!/usr/bin/env python
# encoding: utf-8
"""MIDI Digester

"""

from math import pow
from datetime import datetime
import os
import argparse

import echonest.remix.audio as audio
from echonest.remix.support.midi.MidiOutFile import MidiOutFile


def to_midi(input_filename, output_filename):
    """
    Created by Brian Whitman on 2008-11-25.
    Copyright (c) 2008 __MyCompanyName__. All rights reserved.
    """
    a = audio.LocalAudioFile(input_filename).analysis
    midi = MidiOutFile(output_filename)
    midi.header()
    midi.start_of_track()
    midi.tempo(int(60000000.00 / 60.0)) # 60 BPM, one Q per second, 96 ticks per Q, 96 ticks per second.)
    BOOST = 30 # Boost volumes if you want

    # Do you want the channels to be split by timbre or no?
    splitChannels = True

    for seg_index in xrange(len(a.segments)):
        s = a.segments[seg_index]

        if(splitChannels):
            # Figure out a channel to assign this segment to. Let PCA do the work here... we'll just take the sign of coeffs 1->5 as a 4-bit #
            bits = [0,0,0,0]
            for i in xrange(4):
                # Can't use the first coeff because it's (always?) positive.
                if(s.timbre[i+1]>=0): bits[i] =1
            channel = bits[0]*8 + bits[1]*4 + bits[2]*2 + bits[3]*1
        else:
            channel = 0

        # Get the loudnesses in MIDI cc #7 vals for the start of the segment, the loudest part, and the start of the next segment.
        # db -> voltage ratio http://www.mogami.com/e/cad/db.html
        linearMaxVolume = int(pow(10.0,s.loudness_max/20.0)*127.0)+BOOST
        linearStartVolume = int(pow(10.0,s.loudness_begin/20.0)*127.0)+BOOST
        if(seg_index == len(a.segments)-1): # if this is the last segment
            linearNextStartVolume = 0
        else:
            linearNextStartVolume = int(pow(10.0,a.segments[seg_index+1].loudness_begin/20.0)*127.0)+BOOST
        whenMaxVolume = s.time_loudness_max

        # Count the # of ticks I wait in doing the volume ramp so I can fix up rounding errors later.
        tt = 0

        # take pitch vector and hit a note on for each pitch at its relative volume. That's 12 notes per segment.
        for note in xrange(12):
            volume = int(s.pitches[note]*127.0)
            midi.update_time(0)
            midi.note_on(channel=channel, note=0x3C+note, velocity=volume)
        midi.update_time(0)

        # Set volume of this segment. Start at the start volume, ramp up to the max volume , then ramp back down to the next start volume.
        curVol = float(linearStartVolume)

        # Do the ramp up to max from start
        ticksToMaxLoudnessFromHere = int(96.0 * whenMaxVolume)
        if(ticksToMaxLoudnessFromHere > 0):
            howMuchVolumeToIncreasePerTick = float(linearMaxVolume - linearStartVolume)/float(ticksToMaxLoudnessFromHere)
            for ticks in xrange(ticksToMaxLoudnessFromHere):
                midi.continuous_controller(channel,7,int(curVol))
                curVol = curVol + howMuchVolumeToIncreasePerTick
                tt = tt + 1
                midi.update_time(1)

        # Now ramp down from max to start of next seg
        ticksToNextSegmentFromHere = int(96.0 * (s.duration-whenMaxVolume))
        if(ticksToNextSegmentFromHere > 0):
            howMuchVolumeToDecreasePerTick = float(linearMaxVolume - linearNextStartVolume)/float(ticksToNextSegmentFromHere)
            for ticks in xrange(ticksToNextSegmentFromHere):
                curVol = curVol - howMuchVolumeToDecreasePerTick
                if curVol < 0:
                    curVol = 0
                midi.continuous_controller(channel, 7 ,int(curVol))
                tt = tt + 1
                midi.update_time(1)

        # Account for rounding error if any
        midi.update_time(int(96.0*s.duration)-tt)

        # Send the note off
        for note in xrange(12):
            midi.note_off(channel=channel, note=0x3C+note)
            midi.update_time(0)

    midi.update_time(0)
    midi.end_of_track()
    midi.eof()


class Digest(object):
    def __init__(self, audio_file, output_dir, limit):
        self.output_dir = output_dir
        self.limit = limit
        self.audio_files = []
        self.process(audio_file)

    def process(self, audio_file, depth=0):
        print '\nDoing #{}'.format(depth)
        self.audio_files.append('"{}"'.format(audio_file))
        midi_file = '{}/midi-{}.mid'.format(output_dir, depth)
        to_midi(audio_file, midi_file)
        depth += 1
        audio_file_pre_trim = '{}/audio-{}-pre-trim.wav'.format(output_dir, depth)
        audio_file = '{}/audio-{}.wav'.format(output_dir, depth)
        os.system('timidity --volume-compensation -EFreverb=d -Ow -o {} {}'.format(audio_file_pre_trim, midi_file))
        # Trim silence off the end
        os.system('sox {} {} silence 1 0.1 0.1% reverse silence 1 0.1 0.1% reverse'.format(audio_file_pre_trim, audio_file))
        if depth <= self.limit:
            self.process(audio_file, depth=depth)
        else:
            files = ' '.join(self.audio_files)
            os.system('sox {} {}/final.wav'.format(files, output_dir))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('audio_file')
    parser.add_argument('--limit', '-l', dest='limit', default=10)
    args = parser.parse_args()

    output_dir = 'output/{}'.format(datetime.utcnow().strftime('%Y%m%d_%H%M%S'))
    os.system('mkdir -p {}'.format(output_dir))

    Digest(args.audio_file, output_dir, int(args.limit))
