from flask import Flask, render_template, send_from_directory, jsonify, request, send_file
from flask_socketio import SocketIO, emit
import logging
import time
from music_downloader import maindownload
import os
import json
import random
import asyncio
import urllib.parse

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, cors_allowed_origins="*", logger=True, engineio_logger=True)

global current_timestamp, is_playing, queue, current_song_index, last_update_time
current_timestamp = 0
is_playing = False
queue = []
current_song_index = 0
last_update_time = time.time()

logging.basicConfig(level=logging.DEBUG)

LIBRARY_FOLDER = 'library'
LIBDATA_FILE = 'libdata.json'

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/music/<path:name>')
def music(name):
    name = urllib.parse.unquote(name)  # Decode URL-encoded characters
    name = name.replace('/', os.sep)  # Convert URL path to OS path
    logging.debug(f"Sending music file: {name}")
    return send_from_directory(LIBRARY_FOLDER, name, as_attachment=True)


@app.route('/library')
def get_library():
    with open(LIBDATA_FILE, 'r', encoding='utf-8') as file:
        data = json.load(file)
    logging.debug(f"Library data: {data}")
    return jsonify(data)

@app.route('/add_song', methods=['POST'])
def add_song():
    url = request.json['songurl']
    logging.debug(f"Adding song from URL: {url}")
    asyncio.run(maindownload(url))
    time.sleep(5)
    return jsonify({'status': 'success'})

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
        emit('sync', {'timestamp': current_timestamp, 'is_playing': is_playing})

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
    emit('sync', {'timestamp': current_timestamp, 'is_playing': is_playing}, broadcast=True)

@socketio.on('timestamp')
def handle_timestamp(data):
    global current_timestamp, last_update_time
    logging.debug(f"Timestamp received from client: {data}")
    if 'timestamp' in data:
        current_timestamp = data['timestamp']
        last_update_time = time.time()
        logging.debug(f"Updated server timestamp to: {current_timestamp}")
        emit('sync', {'timestamp': current_timestamp, 'is_playing': is_playing}, broadcast=True)  # Ensure broadcast of the latest state

@socketio.on('seek')
def handle_seek(data):
    global current_timestamp, last_update_time
    logging.debug(f"Seek event received with timestamp: {data['timestamp']}")
    if 'timestamp' in data:
        current_timestamp = data['timestamp']
        last_update_time = time.time()
        logging.debug(f"Updated current_timestamp to: {current_timestamp}")
    else:
        logging.warning("Timestamp not found in seek data")
    emit('sync', {'timestamp': current_timestamp, 'is_playing': is_playing}, broadcast=True)

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
        emit('song_selected', {
            'filename': selected_song['path'],
            'title': selected_song['name'],
            'artist': selected_song['artist'],
            'cover_art': selected_song['cover_url']
        }, broadcast=True)
    else:
        logging.error("Selected song index out of range.")

def load_library():
    global queue
    with open(LIBDATA_FILE, 'r', encoding='utf-8') as file:
        queue = json.load(file)

@app.route('/shuffle')
def shuffle():
    global queue
    queue = random.shuffle(queue)
    return jsonify({'status': 'success'})

if __name__ == '__main__':
    load_library()
    socketio.run(app, host='0.0.0.0', port=5000)
