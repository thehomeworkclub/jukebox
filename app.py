from flask import Flask, render_template, send_from_directory, jsonify, request
from flask_socketio import SocketIO, emit
import logging
import time
from music_downloader import maindownload
import os
import json

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, cors_allowed_origins="*", logger=True, engineio_logger=True)

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

@app.route('/music/<name>')
def music(name):
    logging.debug(f"Sending music file: {name}")
    return send_from_directory(LIBRARY_FOLDER, name)

@app.route('/library')
def get_library():
    with open(LIBDATA_FILE, 'r') as file:
        data = json.load(file)
    logging.debug(f"Library data: {data}")
    return jsonify(data)

@app.route('/add_song', methods=['POST'])
def add_song():
    url = request.form['songurl']
    logging.debug(f"Adding song from URL: {url}")
    maindownload(url)
    time.sleep(5)
    return open("incoming.spotdl").read()

@socketio.on('connect')
def handle_connect():
    global current_timestamp, is_playing, last_update_time
    logging.debug("Client connected")
    emit('sync', {'timestamp': current_timestamp, 'is_playing': is_playing})

@socketio.on('play')
def handle_play(data):
    global is_playing, current_timestamp, last_update_time
    logging.debug("Play event received")
    current_timestamp = data['timestamp']
    is_playing = True
    last_update_time = time.time()
    emit('play', {'timestamp': current_timestamp}, broadcast=True)


@socketio.on('pause')
def handle_pause(data):
    global is_playing, current_timestamp, last_update_time
    logging.debug("Pause event received")
    current_timestamp = data['timestamp']
    is_playing = False
    last_update_time = time.time()
    emit('pause', {'timestamp': current_timestamp}, broadcast=True)


@socketio.on('sync')
def handle_sync(data):
    global current_timestamp, is_playing, last_update_time
    logging.debug(f"Sync event received with data: {data}")
    if 'timestamp' in data:
        current_timestamp = data['timestamp']
    is_playing = data['is_playing']
    last_update_time = time.time()
    emit('sync', {'timestamp': current_timestamp, 'is_playing': is_playing}, broadcast=True)

@socketio.on('request_sync')
def handle_request_sync():
    global current_timestamp, is_playing, last_update_time
    logging.debug("Sync request received")
    emit('sync', {'timestamp': current_timestamp, 'is_playing': is_playing})

@socketio.on('timestamp')
def handle_timestamp(data):
    global current_timestamp, last_update_time
    logging.debug(f"Timestamp received: {data}")
    current_timestamp = data.get('timestamp', current_timestamp)
    last_update_time = time.time()

@socketio.on('seek')
def handle_seek(data):
    global current_timestamp, last_update_time
    logging.debug(f"Seek event received with timestamp: {data['timestamp']}")
    current_timestamp = data['timestamp']
    last_update_time = time.time()
    emit('sync', {'timestamp': current_timestamp, 'is_playing': is_playing}, broadcast=True)

@socketio.on('next_song')
def handle_next_song():
    global current_song_index, queue, current_timestamp, is_playing, last_update_time
    logging.debug("Next song requested")
    current_timestamp = 0
    current_song_index += 1
    if current_song_index >= len(queue):
        current_song_index = 0
    if queue:
        next_song = queue[current_song_index]
        current_timestamp = 0
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

@socketio.on('select_song')
def handle_select_song(data):
    global current_song_index, queue, current_timestamp, last_update_time, is_playing
    logging.debug(f"Song selected: {data}")
    current_song_index = data['index']
    if current_song_index < len(queue):
        selected_song = queue[current_song_index]
        current_timestamp = 0  # Change timestamp to 0 on song switch
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
    with open(LIBDATA_FILE, 'r') as file:
        queue = json.load(file)

if __name__ == '__main__':
    load_library()
    socketio.run(app, host='0.0.0.0', port=5000)
