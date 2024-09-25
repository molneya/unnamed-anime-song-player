
# unnamed anime song player

A simple player to play anime songs.

## Setup

This guide assumes you're using Windows. If you use something else, good luck.

### Player

By default, this music player uses [mpv](https://mpv.io/) to play music. To install (including to PATH), I'd recommend first installing [Chocolatey](https://chocolatey.org/install#individual), then installing [mpv](https://community.chocolatey.org/packages/mpv) using Chocolatey.

For a list of mpv shortcuts to use during song playback, check the mpv [manual](https://mpv.io/manual/stable/#interactive-control). TL;DR use `0` or `9` to adjust volume, `Space` to pause and `q` to end playback of the current song.

### Rainmeter

To help with anime song memorisation, this music player can output the current song to a file, where it can be read by [Rainmeter](https://www.rainmeter.net/) to display it on the screen.

To use the provided overlay of the current playing song using Rainmeter, you can make a symlink using the command below to add the skin to Rainmeter (requires admin on Windows 10).
```
cd path/to/this/music/player/folder
mklink /d "%USERPROFILE%\Documents\Rainmeter\Skins\CurrentlyPlaying" "%CD%\skins\CurrentlyPlaying"
```

You may also need to refresh the skin to make it show up properly because Rainmeter can be funny sometimes.

### Lists

Before playing songs, you need to download a list. Use [AnisongDB](https://anisongdb.com/) to search and download `.json` files. You can place these files into a folder (let's call it `lists`), or into subdirectories for better organisation.

## Usage

### Starting the player

#### Lists

To play lists (aka those `.json` files) inside the `lists` directory, use the following command:
```
player --list lists
```

Note the above command does not search folders recursively. If you've put files into subdirectories, you need to specify them:
```
player --list lists\firstlist lists\someotherlist
```

The player also understands individual files:
```
player --list lists\overlord_ii.json lists\overlord_iv.json
```

#### Options

There are many options to adjust how you want the player to behave. You can either make changes to the `options.conf` file, or specify command line arguments. View those command line arguments by using
```
player --help
```

The above lists example can instead be done through the `options.conf` file, for example.

### Playback

To go back a song, close the current player (`q` by default) and quickly press `q`. Simply, just double tap the `q` button.

To end the playlist, close the current player and quickly press `Escape`.
