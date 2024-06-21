from db.model import * 
from peewee import *


def add_to_queue(spotifyurl, name, artist, file_location):
    Queue.create(spotify_url=spotifyurl, name=name, artist=artist, file_location=file_location, is_playing=False)

def get_queue():
    return Queue.select()

def get_current_song():
    return Queue.select().where(Queue.is_playing == True)

def get_next_song():
    return Queue.select().where(Queue.is_playing == False).order_by(Queue.timestamp.desc()).limit(1)

def set_playing(id):
    query = Queue.update(is_playing = True).where(Queue.id == id)
    query.execute()

def set_not_playing(id):
    query = Queue.update(is_playing = False).where(Queue.id == id)
    query.execute()

def delete_from_queue(id):
    query = Queue.delete().where(Queue.id == id)
    query.execute()

