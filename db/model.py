from peewee import *

db = SqliteDatabase('db/db.db')

class BaseModel(Model):
    class Meta:
        database = db

class Queue(BaseModel):
    id = AutoField()
    name = CharField()
    artist = CharField()
    file_location = CharField()
    spotify_url = CharField()
    is_playing = BooleanField()