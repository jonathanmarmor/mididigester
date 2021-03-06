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
    # 60 BPM, one Q per second, 96 ticks per Q, 96 ticks per second.
    midi.tempo(int(60000000.00 / 60.0))
    BOOST = 30  # Boost volumes if you want

    # Do you want the channels to be split by timbre or no?
    split_channels = True

    for seg_index in xrange(len(a.segments)):
        s = a.segments[seg_index]

        if(split_channels):
            # Figure out a channel to assign this segment to.
            # Let PCA do the work here...
            # we'll just take the sign of coeffs 1->5 as a 4-bit
            bits = [0, 0, 0, 0]
            for i in xrange(4):
                # Can't use the first coeff because it's (always?) positive.
                if(s.timbre[i+1] >= 0):
                    bits[i] = 1
            channel = bits[0] * 8 + bits[1] * 4 + bits[2] * 2 + bits[3] * 1
        else:
            channel = 0

        # Get the loudnesses in MIDI cc #7 vals for the start of the segment,
        # the loudest part, and the start of the next segment.
        # db -> voltage ratio http://www.mogami.com/e/cad/db.html
        linear_max_volume = int(pow(10.0, s.loudness_max / 20.0) * 127.0) + BOOST
        linear_start_volume = int(pow(10.0, s.loudness_begin / 20.0) * 127.0) + BOOST
        if(seg_index == len(a.segments) - 1):  # if this is the last segment
            linear_next_start_volume = 0
        else:
            linear_next_start_volume = int(pow(10.0, a.segments[seg_index+1].loudness_begin / 20.0) * 127.0) + BOOST
        when_max_volume = s.time_loudness_max

        # Count the # of ticks I wait in doing the volume ramp so I can fix up
        # rounding errors later.
        tt = 0

        # take pitch vector and hit a note on for each pitch at its relative
        # volume. That's 12 notes per segment.
        # TODO (Jonathan): The dropoff in volume from the loudest to the next
        # loudest is too great
        for note in xrange(12):
            volume = int(s.pitches[note] * 127.0)
            midi.update_time(0)
            midi.note_on(channel=channel, note=0x3C+note, velocity=volume)
        midi.update_time(0)

        # Set volume of this segment. Start at the start volume, ramp up to the
        # max volume, then ramp back down to the next start volume.
        cur_vol = float(linear_start_volume)

        # Do the ramp up to max from start
        ticks_to_max_loudness_from_here = int(96.0 * when_max_volume)
        if(ticks_to_max_loudness_from_here > 0):
            how_much_volume_to_increase_per_tick = float(linear_max_volume - linear_start_volume) / float(ticks_to_max_loudness_from_here)
            for ticks in xrange(ticks_to_max_loudness_from_here):
                midi.continuous_controller(channel, 7, int(cur_vol))
                cur_vol = cur_vol + how_much_volume_to_increase_per_tick
                tt = tt + 1
                midi.update_time(1)

        # Now ramp down from max to start of next seg
        ticks_to_next_segment_from_here = int(96.0 * (s.duration - when_max_volume))
        if(ticks_to_next_segment_from_here > 0):
            how_much_volume_to_decrease_per_tick = float(linear_max_volume - linear_next_start_volume) / float(ticks_to_next_segment_from_here)
            for ticks in xrange(ticks_to_next_segment_from_here):
                cur_vol = cur_vol - how_much_volume_to_decrease_per_tick
                if cur_vol < 0:
                    cur_vol = 0
                midi.continuous_controller(channel, 7 , int(cur_vol))
                tt = tt + 1
                midi.update_time(1)

        # Account for rounding error if any
        midi.update_time(int(96.0 * s.duration) - tt)

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
        self.to_delete = []
        self.original_audio = audio_file
        self.process(audio_file)

    def process(self, audio_file, depth=0):
        print
        print '=' * 10, '#{}'.format(depth), '=' * 10
        self.audio_files.append('"{}"'.format(audio_file))
        midi_file = '{}/midi-{}.mid'.format(self.output_dir, depth)
        to_midi(audio_file, midi_file)
        depth += 1
        audio_file_pre_trim = '{}/audio-{}-pre-trim.wav'.format(self.output_dir, depth)
        os.system('timidity --volume-compensation -EFreverb=d -Ow -o {} {}'.format(audio_file_pre_trim, midi_file))
        audio_file = '{}/audio-{}.wav'.format(self.output_dir, depth)
        # Trim silence
        os.system('sox {} {} silence 1 0.1 0.1% reverse silence 1 0.1 0.1% reverse'.format(audio_file_pre_trim, audio_file))
        self.to_delete.extend([midi_file, audio_file_pre_trim, audio_file])
        if depth <= self.limit:
            self.process(audio_file, depth=depth)
        else:
            # Join the audio files
            audio_to_join = ' '.join(self.audio_files)
            orig_name, _ = os.path.splitext(os.path.basename(self.original_audio))
            os.system('sox {} "{}_{}_depth_{}.wav"'.format(audio_to_join, self.output_dir, orig_name, self.limit))
            # Remove temp files
            os.system('rm {}'.format(' '.join(['"{}"'.format(f) for f in self.to_delete])))
            os.system('rmdir {}'.format(self.output_dir))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('audio_file')
    parser.add_argument('--limit', '-l', dest='limit', default=10)
    args = parser.parse_args()

    output_dir = 'output/{}'.format(datetime.utcnow().strftime('%Y%m%d_%H%M%S'))
    os.system('mkdir -p {}'.format(output_dir))

    Digest(args.audio_file, output_dir, int(args.limit))
