import subprocess
import os
import re
import json
import asyncio
import aiohttp
from pathlib import Path

def fetch_metadata(url, save_file="incoming.spotdl"):
    print("Fetching metadata for the playlist. This may take a while depending on the size of the playlist.")
    result = subprocess.run(['spotdl', 'save', url, '--save-file', save_file], capture_output=True, text=True)
    if result.returncode != 0:
        print(f"An error occurred while fetching metadata: {result}")
        return None
    print("Metadata fetched successfully")
    return save_file

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

async def download_song(session, song, library_path="./library"):
    print(f"Downloading {song['name']} by {song['artists']}")
    url = song['url']
    cmd = ['spotdl', 'download', url, '--output', library_path]
    process = await asyncio.create_subprocess_exec(*cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = await process.communicate()
    if process.returncode == 0:
        print(f"Downloaded {song['name']} by {song['artists']}")
        song_name = decode_unicode_escape(song['name'])
        song_artist = decode_unicode_escape(song['artist'])
        song_artists = ", ".join([decode_unicode_escape(artist) for artist in song['artists']])
        estimated_path_all_artists = os.path.join(library_path, f"{song_artists} - {song_name}.mp3")
        estimated_path_first_artist = os.path.join(library_path, f"{song_artist} - {song_name}.mp3")
        if os.path.exists(estimated_path_all_artists):
            song['path'] = estimated_path_all_artists
        elif os.path.exists(estimated_path_first_artist):
            song['path'] = estimated_path_first_artist
        else:
            print(f"Failed to find the path for {song['name']} by {song['artists']}")
    else:
        print(f"Failed to download {song['name']} by {song['artists']}: {stderr.decode()}")
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
        async with aiohttp.ClientSession() as session:
            for i in range(0, len(new_songs), batch_size):
                batch = new_songs[i:i + batch_size]
                tasks = [download_song(session, song, "./library") for song in batch]
                downloaded_songs = await asyncio.gather(*tasks)
                libdata.extend(downloaded_songs)
        save_libdata(libdata, "libdata.json")
        if os.path.exists(incoming_file):
            os.remove(incoming_file)
    else:
        print("No new songs found.")

if __name__ == "__main__":
    playlist_url = "https://open.spotify.com/track/5Y0hBfi0F1uGvuKpIXvr2C?si=78f9c4ec73c24d6b"
    asyncio.run(maindownload(playlist_url))
