#! /usr/bin/python
import library
from query import *
import os
import time
import gc
from flask import Flask, request
import json
from flask import render_template
from flask.ext.api import status

app = Flask(__name__)
app.config["DEBUG"] = True
app.config['ALLOWED_EXTENSIONS'] = {'wav'}
music_database = library.Library()


def auto():
    """Tasks to be run automatically each time the program starts up."""
    music_database.load()
    if music_database.empty():
        info = "There is no songs in the library. Please import songs!"
        songs = None
    else:
        num = music_database.size()
        info = "Library loaded! Contains " + str(num) + " songs"
        songs = music_database.get_songs()
    music_database.export()
    return info, songs


def cache_library(clear_ans):
    """Caches and optionally clears currently stored library.
    :param clear_ans: Clear working directory or not.
    """
    if music_database.empty():
        info = "Library empty"
    else:
        info = "Library will be cached."
        if clear_ans:
            music_database.cache(True)
        else:
            music_database.cache(False)
    music_database.export()
    return info


def remove_song(song_id):
    """Removes a song from the database.
    :param song_id: fingerprint ID (dir/name) to remove from library:
    """
    init_size = music_database.size()
    music_database.remove(song_id)
    new_size = music_database.size()
    if init_size == new_size:
        info = "'" + song_id + "' not found."
    else:
        info = "'" + str(song_id) + "' successfully removed. Library now contains " + str(new_size) + " songs"
    music_database.export()
    music_database.save()
    return info


def remove_all_songs():
    """Removes all songs from library"""
    songs = music_database.get_songs()
    for song in songs:
        music_database.remove(song.get_id())
    music_database.export()
    music_database.save()
    return "Removed All Songs from Library!"


def import_dir(directory):
    """Prompts user to enter location of directory to be imported.
       Every file in that directory is then loaded into the library.
       :param directory: Enter directory to import to library:"""
    if os.path.exists(directory):
        start_time = time.time()
        info = ""
        for filex in os.listdir(directory):
            if filex.endswith(".wav"):
                filex = directory + "/" + filex
                read_start = time.time()
                music_database.add(filex)
                read_end = time.time()
                info += str(filex)
                info += " - " + str(round((read_end - read_start), 1)) + " secs"
            gc.collect()
        end_time = time.time()
        music_database.save()
        info += "\nDirectory imported in " + str(round((end_time - start_time), 1)) + " seconds"
    else:
        info = "Invalid directory name!"
    music_database.export()
    return info


def import_file(audio_file):
    """Prompts user to enter location of directory to be imported.
       Every file in that directory is then loaded into the library.
       :param audio_file: file to be imported"""
    start_time = time.time()
    info = ""
    read_start = time.time()
    music_database.add(audio_file)
    read_end = time.time()
    info += str(audio_file)
    info += " - " + str(round((read_end - read_start), 1)) + " secs"
    gc.collect()
    end_time = time.time()
    music_database.save()
    info += "\nFile imported in " + str(round((end_time - start_time), 1)) + " seconds"
    music_database.export()
    return info


def search_sample(fname):
    start_time = time.time()
    match = id_sample(fname, mode="record")
    end_time = time.time()
    return start_time, match, end_time


def id_sample(sample, mode="sample"):
    """Finds any possible matches in the database for the given sample.

       :param mode:
       :param sample: string file location
       :return string"""
    quora = QueryClient(music_database.get_hash())
    match = quora.query(sample, mode)
    return match


def match_file(sample_file_path):
    """Tries to match audio file with song in database.
        User is prompted for file location.
        :param sample_file_path: enter sample file path to match:"""
    if os.path.exists(sample_file_path):
        if sample_file_path.endswith(".wav"):
            start_time = time.time()
            match = id_sample(sample_file_path)
            end_time = time.time()
            if match[0] == "No match was found":
                info = str(match[0])
            else:
                info = "Your song is:" + match[0]
            info += "Search completed in " + str(end_time - start_time) + " seconds"
        else:
            info = "Query failed. " + "/" + str(sample_file_path) + " is not a WAV file."
    else:
        info = "/" + str(sample_file_path) + " is not a valid sample filepath. Please re-enter."
    return info


def related_songs(match):
    """Return related songs
    :param match: song for which to get related songs
    """
    info = ""
    for name in match[1]:
        info += str(name.split("/")[1].strip()) + ", "
    return info


def test_helper(f, num):
    """Helper function for test which performs the actual search.
    :param num:
    :param f: sample file
    """
    quora = QueryClient(music_database.get_hash())
    if f.endswith(".wav"):
        info = "Sample: " + str(f)
        for n in range(num):
            start_time = time.time()
            match = quora.query(f)
            end_time = time.time()
            if match[0] == "No match was found":
                match[0] = "None"
            info += "Match " + str((n+1)+match[0]) + " : " + str(round((end_time-start_time), 1)) + " secs"
    else:
        info = "File is not .wav"
    return info


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in app.config['ALLOWED_EXTENSIONS']


@app.route('/')
def index():
    return render_template('index.html', title="Hummers - Recognize songs by humming!")


@app.route('/about')
def about():
    return render_template('about.html', title="About Us | Hummers")


@app.route('/library')
def library():
    info, songs = auto()
    return render_template('library.html', title="Library | Hummers", info=info, songs=songs)


@app.route('/remove', methods=['POST'])
def remove():
    if request.method == 'POST':
        """remove song with ID <song_id>"""
        song_id = str(request.form['song_id'])
        remove_song(song_id)
        return 'Success', status.HTTP_204_NO_CONTENT
    else:
        return 'No Song Exist of this ID', status.HTTP_204_NO_CONTENT


@app.route('/search', methods=['POST'])
def search():
    if request.method == 'POST':
        """search sample"""
        sample = request.files.get('file')
        if sample and allowed_file(sample.filename):
            filepath = os.path.join(os.path.dirname(__file__), "sample.wav")
            sample.save(filepath)

            start_time, match, end_time = search_sample(filepath)
            if match[0] == "No match was found":
                return json.dumps({'song_name': match[0], 'successful': False})
            else:
                return json.dumps({
                    'song_name': match[0],
                    'search_time': "%g secs" % round((end_time - start_time), 1),
                    'successful': True,
                    'related': [{'song_name': name} for name in match[1]]
                })
        return 'Success', status.HTTP_200_OK
    else:
        return 'No Results Found', status.HTTP_204_NO_CONTENT


@app.route("/upload", methods=["POST"])
def upload():
    uploaded_files = request.files.getlist("file[]")
    for filex in uploaded_files:
        if file and allowed_file(filex.filename):
            import_file(filex)
    return 'Success', status.HTTP_204_NO_CONTENT


@app.route('/import')
def import_dir():
    return render_template('import.html', title="Import Songs | Hummers")


@app.route('/admin', methods=["GET", "POST"])
def admin():
    if request.method == 'POST':
        action = str(request.form['action'])
        if action == 'cache_lib':
            info = cache_library(True)
            return 'Success', status.HTTP_204_NO_CONTENT
        elif action == 'remove_all':
            info = remove_all_songs()
            return 'Success', status.HTTP_204_NO_CONTENT
        elif action == 'force_save':
            start_time = time.time()
            music_database.save()
            end_time = time.time()
            info = "Save time: " + str(end_time - start_time)
            return 'Success', status.HTTP_204_NO_CONTENT
        else:
            return 'Error', status.HTTP_404_NOT_FOUND
    else:
        return render_template('admin.html', title="Administrator Options | Hummers")


if __name__ == '__main__':
    app.run()
