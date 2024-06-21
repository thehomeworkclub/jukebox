import subprocess
import os
import re
import json
import asyncio
import aiohttp

def fetch_metadata(url, save_file="incoming.spotdl"):
    result = subprocess.run(['python', '-m', 'spotdl', 'save', url, '--save-file', save_file], capture_output=True, text=True)
    if result.returncode != 0:
        print(f"An error occurred while fetching metadata: {result.stderr}")
        return None
    return save_file



def filter_new_songs(incoming_file, libdata_file="libdata.json"):
    with open(incoming_file, 'r') as file:
        incoming_data = json.load(file)

    if os.path.exists(libdata_file):
        with open(libdata_file, 'r') as file:
            libdata = json.load(file)
    else:
        libdata = []

    existing_urls = {song['url'] for song in libdata}
    print(existing_urls)
    new_songs = [song for song in incoming_data if song['url'] not in existing_urls]

    return new_songs

async def download_song(session, song):
    url = song['url']
    lib = "./library"
    cmd = ['python', '-m', 'spotdl', 'download', url, '--output', lib]
    process = await asyncio.create_subprocess_exec(*cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = await process.communicate()


    if process.returncode == 0:
        print(f"Downloaded {song['name']} by {song['artists']}")
    else:
        print(f"Failed to download {song['name']} by {song['artists']}: {stderr.decode()}")

async def maindownload(playlist_url):
    def is_valid_spotify_url(url):
        pattern = r'^https:\/\/open\.spotify\.com\/playlist\/[a-zA-Z0-9]+(\?si=[a-zA-Z0-9]+)?$'
        return re.match(pattern, url) is not None

    if not is_valid_spotify_url(playlist_url):
        print("Invalid Spotify URL")
        return

    incoming_file = fetch_metadata(playlist_url)
    os.remove(incoming_file)
    if not incoming_file:
        return

    new_songs = filter_new_songs(incoming_file)

    if new_songs:
        print("New songs to be added:")
        new_song_urls = [song['url'] for song in new_songs]
        print(new_song_urls)
        for song in new_songs:
            print(f"{song['name']} by {song['artists']}")

        libdata_file = "libdata.json"
        if os.path.exists(libdata_file):
            with open(libdata_file, 'r') as file:
                libdata = json.load(file)
        else:
            libdata = []

        libdata.extend(new_songs)

        with open(libdata_file, 'w') as file:
            json.dump(libdata, file, indent=4)

        os.remove(incoming_file)

        async with aiohttp.ClientSession() as session:
            tasks = [download_song(session, song) for song in new_songs]
            await asyncio.gather(*tasks)
    else:
        print("No new songs found.")

if __name__ == "__main__":
    playlist_url = "https://open.spotify.com/playlist/7IXTedx5tRGadIjaCThQUK?si=ada181a04b15462c"
    asyncio.run(maindownload(playlist_url))
