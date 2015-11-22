import sys
from pylab import *
from scipy.stats import mode
from itertools import takewhile
import wave
import math
import scipy
import random

import numpy as np
import matplotlib.pyplot as plt

#GLOBALS TO EDIT HASH OUTPUT
time_size = 1
freq_bin_low = 4
freq_bin_high = 3
power_tolerance = 0
freq_split_val = 1000
# number of tokens used to compare fingerprints
THRESHOLD = 0.5

# Each song has a fingerprint, and in each fingerprint we have an 'id' and 'hash' array associated with it.
class Fingerprint:
    '''An object to store all data related to audio fingerprints.'''

    # This is the constructor.
    def __init__(self, audio_data):
        '''Initializes a Fingerprint object with an empty list and
            empty string.

            @return Fingerprint'''
        self.hash = []
        self.id = ""
        if audio_data != "":
            self._get_hash(audio_data)

    def plot_fing(self):
        '''Visually plots which tokens are being hashed together.
           Used mainly for testing purposes.'''
        p = zip(*self.hash)[0]
        t = zip(*self.hash)[1]
        p = zip(*p)
        plt.clf()
        plt.scatter(t,p[0])
        for i in range(0,len(self.hash)):
            plt.plot([t[i],t[i]+p[2][i]],[p[0][i],p[1][i]])
        plt.show()

    def hash_len(self):
        '''Returns number of hash tokens stored in the Fingerprint object.

           @return int'''
        return len(self.hash)

    def hash_list(self):
        '''Returns the entire list of hash tokens stored in the object

           @return tuple list'''
        return self.hash

    def get_id(self):
        '''Returns the id associated with the audio fingerprint.

           @return string'''
        return self.id

    def set_id(self,song_id):
        '''Sets the id for the audio fingerprint.

           @param string the id to be set'''
        self.id = song_id

    def find(self, test_token):
        ''' Finds token in Fingerprint object corresponding to the test_token
            provided.

            @param tuple hash token that needs to be searched for within object
            @return tuple'''
        # need to add tolerance to ensure accurate matching on inexact tokens
        for token in self.hash:
            if token[0] == test_token:
                return token
        return None

    def get_hash_token(self, index):
        '''Returns hash token at position index within hash list.

           @param int index from which hash token is desired
           @return tuple'''
        return self.hash[index]

    def _get_hash(self, audio_data):
        '''Produces list of hash tokens from audio file.

           @param string the audio from which the fingerprint represents'''
        #turn off divide by zero error in specgram
        ignored_states = np.seterr(divide='ignore')

        #Extract sound data into time series data
        constellation = []
        spf = wave.open(audio_data,'r')
        sound_info = spf.readframes(-1)
        sound_info = np.fromstring(sound_info, 'Int16')
        f = spf.getframerate()
        if spf.getnchannels() == 1:
            f = f/2

        #Run spectrogram on data
        Pxx, freqs, bins, im = plt.specgram(sound_info, NFFT = 4096, Fs = 2*f, scale_by_freq=True,sides='default')
        if spf.getsampwidth() == 2:
            Pxx = Pxx[0:(len(Pxx)/2)]
            freqs = freqs[0:len(Pxx)]

        # plt.show()
        
        #Prepare to find the max in each grid region
        powers = zip(*Pxx)
        batch_size = int(math.floor(time_size/bins[0]))
        batch = 0

        #find higher resolution cutoff
        freq_split_bin = int(math.ceil(freq_split_val/freqs[1]))
        freq_batch_low = int(math.ceil(freq_split_bin/freq_bin_low))
        freq_batch_high = int(math.ceil((len(freqs)-freq_split_bin)
            /freq_bin_high))

        #iterate over each vertical sample to find max powers
        while batch < len(bins):
            vert_sample = zip(*powers[batch:(batch+batch_size)])
            avg_power = sum(map(sum,vert_sample))/(len(freqs)*batch_size)

            #find max power for each frequency bin
            max_freqs = [(bins[x.index(max(x))+batch], max(x))
                         for x in vert_sample]

            #find max power inside of grid sample
            horiz = 0
            while horiz < len(freqs):
                if horiz <= freq_split_bin:
                    grid_sample = zip(*max_freqs[horiz:(horiz+freq_batch_low)])
                    max_power = max(grid_sample[1])
                else:
                    grid_sample = zip(*max_freqs[horiz:(horiz+freq_batch_high)])
                    max_power = max(grid_sample[1])

                #filter out max values below power threshold
                if ((max_power > (avg_power*power_tolerance))
                        and (horiz + freq_batch_high < len(freqs))):
                    max_index = grid_sample[1].index(max_power)
                    #store frequency and bin number
                    constellation.append((grid_sample[0][max_index],
                                            freqs[max_index+horiz]))
                if horiz < freq_split_bin:
                    horiz += freq_batch_low
                else:
                    horiz += freq_batch_high

            #sort the list by increasing time
            batch += batch_size

        #filter out 0 frequencies
        constellation = [x for x in constellation if x[1] != 0.0]

        #sort constellation in time
        constellation = sorted(constellation)

        #print constellation to log
        # f = open('log.txt', 'w')
        # for x in constellation:
        #     f.write(str(x))
        # f.close()

        # print "CONSTELLATION READOUT"
        # print str(constellation)

        #Below plots versus spectrogram for testing
        spf.close()
        self._fast_hash(constellation)

    def _fast_hash(self, constellation):
        '''Creates the hash tokens for the fingerprint.

           @param tuple the constellation map tuples'''

        '''These variables dictate the dimensions of the target area
           relative to the anchor point.'''
        min_t = 2*time_size
        max_t = 2*time_size + .5
        max_f = 1000
        min_f = -max_f

        number_of_points = len(constellation)

        def target_map(anchor, rest):
            '''Generates hash tokens out anchor and rest of points.'''
            (t1,f1) = anchor
            def within_bounds((t1,f1), (t2,f2)):
                '''determines whether point2 is within the target area
                   of point1.'''
                return (((t1+min_t) <= t2 <= (t1+max_t))
                    and ((f1+min_f) <= f2 <= (f1+max_f)))

            '''returns list of points within the anchor point's target area.
               itertools.takewhile assures that the loop stops when points
               are temporally beyond the target area.'''
            target_area = ([point for point in
                takewhile(lambda (t,f): t <= t1+max_t, rest)
                if within_bounds(anchor, point)])

            '''iterates through target points, appending hashes to the
               hash list.'''
            for (t2,f2) in target_area:
                self.hash.append(((round(f1),round(f2),round(t2-t1,3)),
                    (round(t1,3))))
                #self.hash.append(((f1,f2,t2-t1),t1))

        '''Main loop: iterates through constellation map, calling target_map
           function each point (as anchor point) and the remaining points.'''
        for n in range(number_of_points-1):
            anchor = constellation[n]
            rest = constellation[(n+1):]
            target_map(anchor,rest)

        random.shuffle(self.hash)
        
        #Plot the hash tokens
        # self.plot_fing()

def compare(sample_fingerprint,library_fingerprint):
    '''Compares two fingerprints and determines how likely it is that they
           are derived from the same song.

           @param Fingerprint the sample's fingerprint
           @param Fingerprint the fingerprint of a likely match from the database
           @return tuple'''

    '''compares two fingerprints and returns a number corresponding to
            how well they match.'''
    token_pairs = []
    for x in range(0,sample_fingerprint.hash_len()):
        sample_token = sample_fingerprint.get_hash_token(x)
        library_token = library_fingerprint.find(sample_token[0])
        if library_token != None:
            token_pairs.append((library_token, sample_token))
    if token_pairs == []:
        return None
    else:
        return (analyze(token_pairs), library_fingerprint.get_id())

def analyze(pair_list):
    '''Computes histogram based on time offsets and returns height of
        largest bin.

        @param tuple list'''
    delta = []
    for (library_token, sample_token) in pair_list:
        delta.append(library_token[1] - sample_token[1])
    try:
        rounded_list = [round(n, 2) for n in delta]
        list_mode = mode(rounded_list)
        mode_count = int(list_mode[1][0])
        return (len(delta)*1000 + mode_count)
    except:
        pass
