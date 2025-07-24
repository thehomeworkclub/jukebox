import logging
import subprocess
import os
import re
import json
import asyncio
import aiohttp
import sys
from spotdl import Spotdl
from spotdl.types.song import Song
from pathlib import Path
from dataclasses import asdict

import dotenv
dotenv.load_dotenv()
downloader_settings = {"output": "./library"}
spotdl_instance = Spotdl(os.getenv("SPOTIFY_CLIENT_ID"), os.getenv("SPOTIFY_CLIENT_SECRET"), downloader_settings=downloader_settings)




def fetch_metadata(url: str, save_file: str="incoming.spotdl") -> str | None:
    try:

        # Search for song(s) – returns list of Song objects
        songs = spotdl_instance.search([url])

        if not songs:
            print("No songs found.")
            return None

        # Convert each Song dataclass to a dictionary using asdict
        serialized = [asdict(song) for song in songs]

        # Write to .spotdl file (which is just a JSON list)
        with open(save_file, 'w', encoding='utf-8') as f:
            json.dump(serialized, f, ensure_ascii=False, indent=2)

        print("Metadata fetched successfully")
        return save_file

    except Exception as e:
        print(f"An error occurred while fetching metadata: {e}")
        return None

def filter_new_songs(incoming_file, libdata_file="libdata.json"):
    with open(incoming_file, 'r', encoding='utf-8') as file:
        incoming_data = json.load(file)
    if os.path.exists(libdata_file):
        with open(libdata_file, 'r', encoding='utf-8') as file:
            libdata = json.load(file)
    else:
        libdata = []
    existing_urls = {song['url'] for song in libdata}
    new_songs = [song for song in incoming_data if song['url'] not in existing_urls]
    print(f"Found {len(new_songs)} new songs")
    return new_songs

def decode_unicode_escape(s):
    return bytes(s, 'utf-8').decode('unicode_escape').encode('latin1').decode('utf-8')

def download_song_sync(song: dict, library_path="./library") -> dict:
    print(f"Downloading {song['name']} by {song['artists']}")
    url = song['url']

    try:
        # Search song metadata
        songs = spotdl_instance.search([url])
        if not songs:
            print(f"No song found for {url}")
            return song
        results = spotdl_instance.download_songs(songs)
        if results:
            song['path'] = str(results[0].file_path)
            print(f"Downloaded to {song['path']}")
        else:
            print(f"Failed to download {song['name']}")

    except Exception as e:
        print(f"Error downloading {song['name']}: {e}")
    return song

def load_libdata(libdata_file):
    if os.path.exists(libdata_file):
        with open(libdata_file, 'r', encoding='utf-8') as file:
            return json.load(file)
    else:
        return []

def save_libdata(libdata, libdata_file):
    with open(libdata_file, 'w', encoding='utf-8') as file:
        json.dump(libdata, file, indent=4, ensure_ascii=False)
        
def is_valid_spotify_url(url):
    pattern = r'^https:\/\/open\.spotify\.com'
    return re.match(pattern, url) is not None

async def maindownload(playlist_url, batch_size=5):
    if not is_valid_spotify_url(playlist_url):
        print("Invalid Spotify URL")
        return
    incoming_file = fetch_metadata(playlist_url)
    if not incoming_file:
        return
    new_songs = filter_new_songs(incoming_file)
    if new_songs:
        print("New songs to be added:")
        for song in new_songs:
            song['name'] = decode_unicode_escape(song['name'])
            song['artist'] = decode_unicode_escape(song['artist'])
            print(f"{song['name']} by {song['artists']}")
        libdata = load_libdata("libdata.json")
        downloaded_songs = []
        for song in new_songs:
            downloaded_song = download_song_sync(song, "./library")
            downloaded_songs.append(downloaded_song)
            logging.info(f"Downloaded song: {downloaded_song}")
        libdata.extend(downloaded_songs)
        save_libdata(libdata, "libdata.json")
        if os.path.exists(incoming_file):
            os.remove(incoming_file)
    else:
        print("No new songs found.")
if __name__ == "__main__":
    playlist_url = "https://open.spotify.com/track/5Y0hBfi0F1uGvuKpIXvr2C?si=78f9c4ec73c24d6b"
    asyncio.run(maindownload(playlist_url))
