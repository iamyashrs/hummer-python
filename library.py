from fingerprint import *
from query import *
import cPickle as pickle
import os
import shutil
import time
import gc

class Library:
    '''A class designed to retain all information related to the
    music database,
    including all of the song fingerprints as well as the hash table.'''
    def __init__(self):
        '''Initializes object with empty list and empty dict
        for hash table.
        -> songs - array
        -> hash - dict

            @return Library'''
        self.songs = []
        self.hash = {}

    def convert_library(self):
        fp_list = self.songs
        self.songs = {}
        for fp in fp_list:
            self.songs[fp.get_id()] = fp
        for bin, fp_list in self.hash.iteritems():
            self.hash[bin] = [fp.get_id() for fp in fp_list]


    def empty(self):
        '''Checks if database is empty.

            @return bool'''
        return (self.songs == [])

    def get_songs(self):
        '''Returns contents of songs field.

            @return fingerprint list'''
        return self.songs

    def get_hash(self):
        '''Returns hash table asociated with Library object.

            @return dict'''
        return self.hash

    def size(self):
        '''Returns songs stored in library.

            @return int'''
        return len(self.songs)

    def export(self):
        '''Exports library size and list of songs in library to text file.'''
        timestr = time.strftime("%H:%M, %m-%d-%y")
        with open('library_list.txt', 'w') as f:
            f.write('As of '+timestr+', library contains %d songs\n\n' % self.size())
            for fp in self.songs:
                f.write(fp.get_id()+'\n')

    def load(self):
        '''Checks for database file stored in working directory.'''
        try:
            with open('library_file.csv', 'rb') as libfile:
                self.songs = pickle.load(libfile)
            with open('hash_file.csv', 'rb') as hashfile:
                self.hash = pickle.load(hashfile)
        except IOError:
            pass


    def save(self):
        '''Stores current database on disk as csv file and returns
            whether it was successful.'''
        with open('library_file.csv', 'wb+') as libfile:
            pickle.dump(self.songs, libfile, -1)
        with open('hash_file.csv', 'wb+') as hashfile:
            pickle.dump(self.hash, hashfile, -1)

    def add(self,audio_track):
        '''Adds audio tracks to dictionary, one song at a time.

            @param string location of audio file to be imported'''
        fp = Fingerprint(audio_track)
        name = os.path.splitext(audio_track)[0]
        fp.set_id(name)
        (self.songs).append(fp)
        self._append_hash(fp)
        gc.collect()

    def remove(self, unwanted_id):
        '''Removes unwanted song from library.'''
        self.songs = [fp for fp in self.songs if fp.get_id() != unwanted_id]
        for bin in self.hash:
            self.hash[bin] = [fp for fp in self.hash[bin]
            if fp.get_id() != unwanted_id]
        self.save

    def cache(self, clear):
        '''caches data stored in library object.
            Clears library if argument True'''
        size = str(self.size())
        cached_lib = "cache/"+size+"_lib.csv"
        cached_hash = "cache/"+size+"_hash.csv"
        try:
            if clear:
                self.songs = []
                self.hash = {}
                shutil.move('library_file.csv', cached_lib)
                shutil.move('hash_file.csv', cached_hash)
                print("\nLibrary cached and cleared!")
            else:
                shutil.copyfile('library_file.csv', cached_lib)
                shutil.copyfile('hash_file.csv', cached_hash)
                print("\nLibrary successfully cached!")
        except IOError:
            print("Cache failed due to IOError.")

    def _append_hash(self,fingerprint):
        '''Appends all fingerprint hash tokens to the database dict.

            @param Fingerprint song fingerprint to be added to the hash table'''
        fp_tokens = fingerprint.hash_list()
        for token in fp_tokens:
            if (self.hash).has_key(token[0]):
                if fingerprint not in self.hash[token[0]]:
                    self.hash[token[0]].append(fingerprint)
            else:
                self.hash[token[0]] = [fingerprint]
