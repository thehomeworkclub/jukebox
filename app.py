from flask import Flask, render_template, send_from_directory, request
from flask_socketio import SocketIO, emit
from peewee import *
from queries import *
from db.model import *
from music_downloader import *
import logging
import time

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, cors_allowed_origins="*", logger=True, engineio_logger=True)

current_timestamp = 0
is_playing = False
last_update_time = time.time()

logging.basicConfig(level=logging.ERROR)

@app.route('/')
def index():
    return render_template('index.html')
@app.route('/music/<name>')
def music(name):
    return send_from_directory('static', name)
@app.route('/add_song', methods=['POST'])
def add_song():
    url = request.form['songurl']
    maindownload(url)
    time.sleep(5)
    return open("incoming.spotdl").read()

@socketio.on('connect')
def handle_connect():
    global current_timestamp, is_playing, last_update_time
    logging.debug("Client connected")
    if is_playing:
        current_timestamp += time() - last_update_time
        last_update_time = time()
    emit('sync', {'timestamp': current_timestamp, 'is_playing': is_playing})

@socketio.on('play')
def handle_play(data):
    global is_playing, last_update_time
    is_playing = True
    last_update_time = time()
    logging.debug("Play event received")
    emit('play', {'timestamp': current_timestamp}, broadcast=True)

@socketio.on('pause')
def handle_pause(data):
    global is_playing, current_timestamp, last_update_time
    is_playing = False
    current_timestamp += time() - last_update_time
    last_update_time = time()
    logging.debug("Pause event received")
    emit('pause', {'timestamp': current_timestamp}, broadcast=True)

@socketio.on('sync')
def handle_sync(data):
    global current_timestamp, is_playing, last_update_time
    logging.debug(f"Sync event received with data: {data}")
    if 'timestamp' in data:
        current_timestamp = data['timestamp']
    is_playing = data['is_playing']
    last_update_time = time()
    emit('sync', {'timestamp': current_timestamp, 'is_playing': is_playing}, broadcast=True)

@socketio.on('request_sync')
def handle_request_sync():
    global current_timestamp, is_playing, last_update_time
    if is_playing:
        current_timestamp += time() - last_update_time
        last_update_time = time()
    emit('sync', {'timestamp': current_timestamp, 'is_playing': is_playing})

@socketio.on('timestamp')
def handle_timestamp(data):
    global current_timestamp, last_update_time
    current_timestamp = data.get('timestamp', current_timestamp)
    last_update_time = time()
    logging.debug(f"Timestamp updated to {current_timestamp}")

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000)
