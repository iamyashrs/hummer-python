#! /usr/bin/python
import library
from query import *
import os
import time
import gc

music_database = library.Library()

def initialize():
    '''Starts the program'''
    print("\n\nWelcome!")
    auto()
    menu()

def auto():
    '''Tasks to be run automatically each time the program starts up.'''
    music_database.load()
    if music_database.empty():
        print("\nThere is no library in this directory. Please import songs.")
    else:
        num = music_database.size()
        print("\nLibrary loaded! Contains %d songs.\n\n" % num)
    music_database.export()
    menu()

def menu():
    '''Brings up main menu for program.'''
    print("****\n\n")
    print("Please choose an option:")
    print("[1] Match a song from file")
    print("[2] Match a song from microphone")
    print("    --------------------")
    print("[a] Admin panel")
    print("[q] Quit")
    print("\n\n****")
    ans = raw_input()
    if ans == '1':
        match_file()
    elif ans == '2':
        match_live()
    elif ans == 'a':
        admin()
    elif ans == 'q':
        print("****")
        print("\n\n\n**********")
        print(" Oh, bai!")
        print("**********\n\n\n")
        sys.exit()
    else:
        print("Invalid input.")
        print("")
        menu()

def cache_library():
    '''Caches and optionally clears currently stored library.'''
    print("****\n\n")
    if music_database.empty():
        print("Library empty.")
    else:
        print("Library will be cached.")
        print("Do you also want to clear working library? [y/n]")
        print("(Enter 'm' to return to menu)")
        clear_ans = raw_input()
        if clear_ans == 'y':
            music_database.cache(True)
        elif clear_ans == 'n':
            music_database.cache(False)
    music_database.export()
    admin()

def remove_song():
    '''Removes a song from the database.'''
    print("****\n\n")
    print("Enter fingerprint ID (dir/name) to remove from library:")
    print("(Enter 'm' to return to menu)")
    print("\n\n****")
    init_size = music_database.size()
    ans = raw_input()
    if ans == "m" or ans == '':
        print("Saving updated library...")
        music_database.export()
        music_database.save()
        admin()
    else:
        music_database.remove(ans)
    new_size = music_database.size()
    if init_size == new_size:
        print("'"+ans+"' not found.\n")
        remove_song()
    else:
        print("****\n\n")
        print("'"+ans+"' successfully removed")
        print("Library now contains %d songs.\n\n" % new_size)
    remove_song()

def import_dir():
    '''Prompts user to enter location of directory to be imported.
       Every file in that directory is then loaded into the library.'''
    print("****\n\n")
    print("Enter directory to import to library:")
    print("\n\n****")
    ans = raw_input()
    if ans == "m":
        menu()
    if ans == '':
        ans = os.getcwd()
    if os.path.exists(ans):
        start_time = time.time()
        for filex in os.listdir(ans):
            if filex.endswith(".wav"):
                filex = ans + "/" + filex
                read_start = time.time()
                music_database.add(filex)
                read_end = time.time()
                print(filex)
                print("%g secs" % round((read_end - read_start), 1))
            gc.collect()
        end_time = time.time()
        music_database.save()
        print("****\n")
        print("Directory imported in %g seconds\n"
            % round((end_time - start_time), 1))
    else:
        print("Invalid directory name, try again? [y/n]")
        print("\n\n****")
        ans = raw_input()
        if ans == 'y':
            import_dir()
        else:
            print("****\n\n")
    music_database.export()
    menu()

def id_sample(sample, mode = "sample"):
    '''Finds any possible matches in the database for the given sample.

       @param string file location
       @return string'''
    quora = QueryClient(music_database.get_hash())
    match = quora.query(sample, mode)
    return match

def match_file():
     '''Tries to match audio file with song in database.
        User is prompted for file location.'''
     print("****\n\n")
     print("Please enter sample file path to match:")
     print("(Enter 'm' to return to menu)\n")
     print("\n****")
     ans = raw_input()
     if ans == "m":
        menu()
     elif os.path.exists(ans):
        if ans.endswith(".wav"):
            start_time = time.time()
            match = id_sample(ans)
            end_time = time.time()
            print("****")
            print("\n\n===================================")
            if match[0] == "No match was found":
                print (match[0])
            else:
                print("Your song is:")
                print (match[0])
            print("-------")
            print("Search completed in %g seconds" % (end_time - start_time))
            print("===================================\n")
            print("Press 'r' for related songs, or 'Enter' to return to menu")
            ans1 = raw_input()
            if ans1 == 'r':
                print("Related Songs\n=============\n")
                for name in match[1]:
                    print(name.split("/")[1].strip())
                print("\nPress any key to return to menu")
                ans2 = raw_input()
                menu()
            else:
                menu()
        else:
            print("\nQuery failed. "+"/"+ans+" is not a WAV file.")
            match_file()
     else:
        print("\n/"+ans+" is not a valid sample filepath. Please re-enter.")
        match_file()

def record(fname):
    '''Helper function for option5 that records sound and uses fname
       as the file name. 
       -> PyAudio provides Python bindings for PortAudio, the cross-platform audio I/O library.

       @param string saves recorded audio with this name'''
    import pyaudio
    import time
    import wave

    # from http://people.csail.mit.edu/hubert/pyaudio/#examples
    CHUNK = 1024
    FORMAT = pyaudio.paInt16
    CHANNELS = 2
    RATE = 44100
    RECORD_SECONDS = 20
    WAVE_OUTPUT_FILENAME = fname

    p = pyaudio.PyAudio()

    stream = p.open(format=FORMAT,
                    channels=CHANNELS,
                    rate=RATE,
                    input=True,
                    frames_per_buffer=CHUNK)

    print("* recording")

    frames = []

    for i in range(0, int(RATE / CHUNK * RECORD_SECONDS)):
        data = stream.read(CHUNK)
        frames.append(data)

    print("* done recording")
    stream.stop_stream()
    stream.close()
    p.terminate()

    wf = wave.open(WAVE_OUTPUT_FILENAME, 'wb')
    wf.setnchannels(CHANNELS)
    wf.setsampwidth(p.get_sample_size(FORMAT))
    wf.setframerate(RATE)
    wf.writeframes(b''.join(frames))
    wf.close()

    start_time = time.time()
    match = id_sample(fname, mode="record")
    end_time = time.time()

    print("\n\n===================================")
    if match[0] == "No match was found":
        print (match[0])
    else:
        print("Your song is:")
        print(match[0])
        print("-------")
        print("Search completed in %g seconds" % (end_time - start_time))
        print("===================================\n")
        print("Press 'r' for related songs, or 'Enter' to return to menu")
        ans1 = raw_input()
        if ans1 == 'r':
            print("Related Songs\n=============\n")
            for name in match[1]:
                print(name.split("/")[1].strip())
            print("\nPress any key to return to menu")
            ans2 = raw_input()
            menu()
        else:
            menu()

def match_live():
    '''Allows user to record live audio.'''
    print("****\n\n")
    print("Press enter to record")
    print("(Enter 'm' to return to menu)")
    print("\n****")
    ans = raw_input()
    if ans == "m":
        menu()
    elif ans == '':
        record("sample.wav")
        menu()
    else:
        print("Sorry, didn't get that!")
        match_live()

def test_helper(f, num):
    '''Helper function for test which performs the actual search.'''
    quora = QueryClient(music_database.get_hash())
    if f.endswith(".wav"):
        print("\nSample: "+f)
        for n in range(num):
            start_time = time.time()
            match = quora.query(f)
            end_time = time.time()
            if match[0] == "No match was found":
                match[0] = "None"
            print("\nMatch %d: " % (n+1)+match[0])
            print("%g secs" % round((end_time-start_time), 1))
        print("\n------------------------")

def test():
    '''Prints repeated match results for a file or directory.'''
    print("****\n\n")
    print("Enter directory or file path to test:")
    ans = raw_input()
    if ans == "m":
        menu()
    print("\nEnter number of tests per sample:")
    ans2 = raw_input()
    if ans2 == "m":
        menu()
    elif ans2 == "":
        num = 1
    else:
        try:
            int(ans2)
            num = int(ans2)
        except ValueError:
            menu()
    if ans == '':
        ans = os.getcwd()
    if ans.endswith("/"):
        ans = ans[:-1]
    if os.path.exists(ans):
        print("\nTEST RESULTS\nDirectory: "+ans+"\n\n")
        if os.path.isdir(ans):
            directory = os.listdir(ans)
            if directory == []:
                print("Directory '"+ans+"' is empty.")
            else:
                print("\n\n===================================")
                for filex in os.listdir(ans):
                    test_helper(ans+"/"+filex, num)
        elif os.path.isfile(ans):
            print("\n\n===================================")
            test_helper(ans, num)
    else:
        print("/"+ans+" is not a valid file or directory. Please re-enter.")
        test()
    admin()

def admin():
    '''Brings up admin menu, which has useful debugging tools'''
    print("****\n\n")
    print("ADMIN PANEL")
    print("\nPlease choose an option:")
    print("[1] Cache current library")
    print("[2] Import directory of songs into library")
    print("[3] Remove song (dir/name without extension) from library")
    print("[4] Test match on file or directory")
    print("[5] Force save library & hash to CSV (should not be necessary)")
    print("    --------------------")
    print("[m] Return to main menu")
    print("[q] Quit")
    print("\n\n****")
    ans = raw_input()
    if ans == '1':
        cache_library()
    elif ans == '2':
        import_dir()
    elif ans == '3':
        remove_song()
    elif ans == '4':
        test()
    elif ans == '5':
        start_time = time.time()
        music_database.save()
        end_time = time.time()
        print("Save time: %g" % (end_time - start_time))
    elif ans == 'm':
        menu()
    elif ans == 'q':
        sys.exit()
    else:
        print("Invalid input.")
        print("")
        admin()

#Used when we want to run the block only if the program was used by itself 
#and not when it was imported from another module
if __name__ == "__main__":
    import sys
    initialize()
