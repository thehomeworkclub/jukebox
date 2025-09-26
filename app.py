import gettext
gettext.translation = lambda *args, **kwargs: gettext.NullTranslations()

from flask import Flask, render_template, send_from_directory, jsonify, request, send_file, abort
from flask_socketio import SocketIO, emit
import logging
import time
from music_downloader import maindownload
import os
import json
import random
import asyncio
import urllib.parse
import base64
from spotdl.utils.ffmpeg import download_ffmpeg


app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, cors_allowed_origins="*",
                    logger=True, engineio_logger=True)

global current_timestamp, is_playing, queue, current_song_index, last_update_time
current_timestamp = 0
is_playing = False
queue = []
current_song_index = 0
last_update_time = time.time()

logging.basicConfig(level=logging.DEBUG, filename='app.log',filemode='a')

LIBRARY_FOLDER = 'library'
LIBDATA_FILE = 'libdata.json'




@app.route('/')
def index():
    return render_template('index.html')


@app.route('/music/<encoded_path>')
def music(encoded_path):
    try:
        decoded_path = base64.urlsafe_b64decode(encoded_path.encode('utf-8')).decode('utf-8')
        logging.debug(f"Directory Path: {os.path.abspath(LIBRARY_FOLDER)}")
        logging.debug(f"Decoded path: {decoded_path}")
        directory = os.path.dirname(decoded_path)
        logging.debug(f"Directory: {directory}")
        file_name = os.path.basename(decoded_path)
        logging.debug(f"File name: {file_name}")
        logging.debug(f"Sending music file: \"{file_name}\" from \"{directory}\"")
        logging.debug(f"Current application root path: {app.root_path}")
        return send_from_directory(os.path.abspath(LIBRARY_FOLDER), file_name, as_attachment=True)
    except Exception as e:
        logging.error(f"Error decoding path: {e}")
        abort(404)


@app.route('/clear_library')
def clear_library():
    global queue
    os.remove(LIBDATA_FILE)
    file_list = os.listdir(LIBRARY_FOLDER)
    for file_name in file_list:
        file_path = os.path.join(LIBRARY_FOLDER, file_name)
        os.remove(file_path)
    queue = []
    return jsonify({'status': 'success'})


@app.route('/library')
def get_library():
    global queue
    return jsonify(queue)


@app.route('/add_song', methods=['POST'])
def add_song():
    url = request.json['songurl']
    logging.debug(f"Adding song from URL: {url}")
    asyncio.run(maindownload(url))
    time.sleep(5)
    return jsonify({'status': 'success'})


@app.route('/update_queue')
def update_queue():
    global queue
    with open(LIBDATA_FILE, 'r', encoding='utf-8') as file:
        libdata = json.load(file)
    existing_urls = {song['url'] for song in queue}
    new_songs = [song for song in libdata if song['url'] not in existing_urls]
    queue.extend(new_songs)
    return jsonify({'status': 'success', 'new_queue': queue})


@app.route('/jbtheme')
def jbtheme():
    return send_file('jukeboxtheme.css')


def get_current_song():
    if queue and 0 <= current_song_index < len(queue):
        return queue[current_song_index]
    return None


@socketio.on('connect')
def handle_connect():
    global current_timestamp, is_playing, last_update_time, queue, current_song_index
    logging.debug("Client connected")
    current_song = get_current_song()
    if current_song:
        emit('sync', {
            'timestamp': current_timestamp,
            'is_playing': is_playing,
            'song': {
                'filename': current_song['path'],
                'title': current_song['name'],
                'artist': current_song['artist'],
                'cover_art': current_song['cover_url']
            }
        })
    else:
        emit('sync', {'timestamp': current_timestamp,
             'is_playing': is_playing})


@socketio.on('play')
def handle_play(data):
    global is_playing, current_timestamp, last_update_time
    logging.debug(f"Play event received with data: {data}")
    if 'timestamp' in data:
        current_timestamp = data['timestamp']
        logging.debug(f"Updated current_timestamp to: {current_timestamp}")
    else:
        logging.warning("Timestamp not found in play data")
    is_playing = True
    last_update_time = time.time()
    emit('play', {'timestamp': current_timestamp}, broadcast=True)


@socketio.on('pause')
def handle_pause(data):
    global is_playing, current_timestamp, last_update_time
    logging.debug(f"Pause event received with data: {data}")
    if 'timestamp' in data:
        current_timestamp = data['timestamp']
        logging.debug(f"Updated current_timestamp to: {current_timestamp}")
    else:
        logging.warning("Timestamp not found in pause data")
    is_playing = False
    last_update_time = time.time()
    emit('pause', {'timestamp': current_timestamp}, broadcast=True)


@socketio.on('request_sync')
def handle_request_sync():
    global current_timestamp, is_playing, last_update_time
    logging.debug("Sync request received")
    emit('sync', {'timestamp': current_timestamp, 'is_playing': is_playing})


@socketio.on('sync')
def handle_sync(data):
    global current_timestamp, is_playing, last_update_time
    logging.debug(f"Sync event received with data: {data}")
    if 'timestamp' in data:
        current_timestamp = data['timestamp']
        logging.debug(f"Updated current_timestamp to: {current_timestamp}")
    else:
        logging.warning("Timestamp not found in sync data")
    if 'is_playing' in data:
        is_playing = data['is_playing']
    else:
        logging.warning("is_playing not found in sync data")
    last_update_time = time.time()
    emit('sync', {'timestamp': current_timestamp,
         'is_playing': is_playing}, broadcast=True)


@socketio.on('timestamp')
def handle_timestamp(data):
    global current_timestamp, last_update_time
    logging.debug(f"Timestamp received from client: {data}")
    if 'timestamp' in data:
        current_timestamp = data['timestamp']
        last_update_time = time.time()
        logging.debug(f"Updated server timestamp to: {current_timestamp}")
        # Ensure broadcast of the latest state
        emit('sync', {'timestamp': current_timestamp,
             'is_playing': is_playing}, broadcast=True)


@socketio.on('seek')
def handle_seek(data):
    global current_timestamp, last_update_time, is_playing
    logging.debug(f"Seek event received with timestamp: {data['timestamp']}")
    if 'timestamp' in data:
        current_timestamp = data['timestamp']
        last_update_time = time.time()
        logging.debug(f"Updated current_timestamp to: {current_timestamp}")
        emit('sync', {'timestamp': current_timestamp, 'is_playing': is_playing, 'action': 'seek'}, broadcast=True)
    else:
        logging.warning("Timestamp not found in seek data")





@socketio.on('next_song')
def handle_next_song():
    global current_song_index, queue, current_timestamp, is_playing, last_update_time
    logging.debug("Next song requested")
    current_song_index += 1
    if current_song_index >= len(queue):
        current_song_index = 0
    if queue:
        next_song = queue[current_song_index]
        is_playing = True
        last_update_time = time.time()
        emit('next_song', {
            'filename': next_song['path'],
            'title': next_song['name'],
            'artist': next_song['artist'],
            'cover_art': next_song['cover_url']
        }, broadcast=True)
    else:
        is_playing = False
        emit('pause', {'timestamp': 0}, broadcast=True)


@socketio.on('prev_song')
def handle_prev_song():
    global current_song_index, queue, current_timestamp, is_playing, last_update_time
    logging.debug("Previous song requested")
    current_song_index -= 1
    if current_song_index < 0:
        current_song_index = len(queue) - 1
    if queue:
        prev_song = queue[current_song_index]
        is_playing = True
        last_update_time = time.time()
        emit('prev_song', {
            'filename': prev_song['path'],
            'title': prev_song['name'],
            'artist': prev_song['artist'],
            'cover_art': prev_song['cover_url']
        }, broadcast=True)
    else:
        is_playing = False
        emit('pause', {'timestamp': 0}, broadcast=True)


@socketio.on('select_song')
def handle_select_song(data):
    global current_song_index, queue, current_timestamp, last_update_time, is_playing
    logging.debug(f"Song selected: {data}")
    current_song_index = data['index']
    if current_song_index < len(queue):
        selected_song = queue[current_song_index]
        is_playing = True
        last_update_time = time.time()
        try:
            emit('song_selected', {
                'filename': selected_song['path'],
                'title': selected_song['name'],
                'artist': selected_song['artist'],
                'cover_art': selected_song['cover_url']
            }, broadcast=True)
        except Exception as e:
            logging.error(f"Error selecting song: {e}")
            get_dir = os.listdir(LIBRARY_FOLDER)
            for file in get_dir:
                if selected_song['name'] in file:
                    emit('song_selected', {
                        'filename': os.path.join(LIBRARY_FOLDER, file),
                        'title': selected_song['name'],
                        'artist': selected_song['artist'],
                        'cover_art': selected_song['cover_url']
                    }, broadcast=True)                    
    else:
        logging.error("Selected song index out of range.")


def load_library():
    global queue
    if not os.path.exists(LIBRARY_FOLDER):
        os.makedirs(LIBRARY_FOLDER)
    if not os.path.exists(LIBDATA_FILE):
        with open(LIBDATA_FILE, 'x', encoding='utf-8') as file:
            file.write('[]')
        queue = []
    else:
        with open(LIBDATA_FILE, 'r', encoding='utf-8') as file:
            queue = json.load(file)


@app.route('/shuffle')
def shuffle():
    global queue
    random.shuffle(queue)
    return jsonify({'status': 'success', 'new_queue': queue})

@app.route('/listeners')
def get_listeners():
    room = '/'  # Default namespace
    participants = socketio.server.manager.rooms.get(room, {})
    count = len(participants)
    if count >= 2: 
        count = count - 1
    return jsonify({'listeners': count})
if __name__ == '__main__':
    logging.debug("Starting the application")
    download_ffmpeg()
    load_library()
    socketio.run(app, host='0.0.0.0', port=5135)

