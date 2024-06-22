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
# TODO: Add song name, artist, id, variables and syncing
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
    is_playing = True
    print("IKLFHGAWSEIKLURGVHBIKLWE" + str(last_update_time))
    last_update_time = time.time()
    emit('play', {'timestamp': current_timestamp}, broadcast=True)

@socketio.on('pause')
def handle_pause(data):
    global is_playing, current_timestamp, last_update_time
    logging.debug("Pause event received")
    is_playing = False
    current_timestamp += time.time() - last_update_time
    last_update_time = time.time()
    emit('pause', {'timestamp': current_timestamp}, broadcast=True)

@socketio.on('sync')
def handle_sync(data):
    global current_timestamp, is_playing, last_update_time
    if not is_playing:     
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

# TODO: Add a route to move song ahead in the queue

# TODO: Add a route to move song back in the queue

# TODO: Add a route to return the queue / playhead



if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000)
