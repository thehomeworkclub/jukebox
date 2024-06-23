# Jukebox

A collaborative jukebox web application where users can add songs to a shared playlist and listen together in sync.

## Features

- Add your favorite songs to the queue
- Sync playback across all connected users
- Control playback (play, pause, seek) in real-time
- Shuffle the queue
- Adjust volume
- Clear the queue

## Technologies Used

- HTML
- CSS (DaisyUI, TailwindCSS)
- JavaScript (jQuery)
- Socket.IO

## Getting Started

Follow these instructions to set up and run the project on your local machine.

### Prerequisites

- Node.js
- npm (Node Package Manager)

### Installation

1. Clone the repository:

```bash
git clone https://github.com/your-username/jukebox.git
cd jukebox
```

2. Install the dependencies:

```bash
npm install
```

3. Start the server:

```bash
node server.js
```

4. Open your browser and navigate to:

```
http://localhost:3000
```

## Usage

1. Open the application in your browser.
2. Paste the link to your favorite song in the input field and press Enter.
3. Control playback using the play/pause, next, and previous buttons.
4. Adjust the volume using the volume slider.
5. Clear the queue or shuffle the songs as needed.

## Code Overview

### HTML Structure

The HTML file contains the structure of the application, including the input field for song URLs, playback controls, volume slider, and the song queue.

### CSS

- DaisyUI and TailwindCSS are used for styling the application.
- Custom CSS is loaded from the `/jbtheme` endpoint.

### JavaScript

- Socket.IO is used for real-time communication between the server and clients.
- jQuery is used for DOM manipulation and AJAX requests.
- The application synchronizes playback across all connected users using socket events (`play`, `pause`, `sync`, `next_song`, `song_selected`).

### Key JavaScript Functions

- `playpause()`: Toggles between play and pause states.
- `playsong()`: Starts playing the current song and emits a `play` event to the server.
- `pausesong()`: Pauses the current song and emits a `pause` event to the server.
- `fetchLibrary()`: Fetches and displays the current song queue from the server.
- `playSong(filePath, title, artist, cover_art)`: Updates the audio source and metadata for the current song.

### Socket Events

- `connect`: Requests initial synchronization from the server.
- `play`: Starts playback when a `play` event is received.
- `pause`: Pauses playback and sets the current timestamp when a `pause` event is received.
- `sync`: Synchronizes the playback position and state with the server.
- `next_song`: Plays the next song in the queue.
- `song_selected`: Plays a selected song from the queue.

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

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgements

- Made with ❤️ by The Homework Club
- Special thanks to all the contributors!
