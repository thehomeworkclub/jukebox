# Jukebox

A collaborative jukebox web application where users can add songs to a shared playlist and listen together in sync.

## Features

- Add your favorite songs to the queue
- Sync playback across all connected users
- Control playback (play, pause, seek) in real-time
- Shuffle the queue
- Adjust volume
- Clear the queue

## Getting Started

Follow these instructions to set up and run the project on your local machine.

### Prerequisites

- Python
- pip
- ffmpeg
- [SpotDL](https://github.com/spotDL/spotify-downloader)

### Installation

1. Clone the repository:

```bash
git clone https://github.com/thehomeworkclub/jukebox.git
cd jukebox
```

2. Open jukebox directorty and install the dependencies:

```bash
pip install -r requirements.txt
```

3. Start the server:

```bash
python app.py
```

4. Open your browser and navigate to:

```
http://localhost:5135
```

## Usage

1. Open the application in your browser.
2. Paste the spotify link to your favorite song in the input field and press Enter.
3. Control playback using the play/pause, next, and previous buttons.
4. Adjust the volume (client side) using the volume slider.
5. Clear the queue or shuffle the songs as needed.


## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch:

```bash
git checkout -b feature/YourFeature
```

3. Commit your changes:

```bash
git commit -m 'Add some feature'
```

4. Push to the branch:

```bash
git push origin feature/YourFeature
```

5. Open a Pull Request
6. 

## Acknowledgements

- Made with ❤️ by The Homework Club
- Special thanks to all the contributors!
