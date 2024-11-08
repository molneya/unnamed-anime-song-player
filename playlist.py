
import json, logging, random, os, time
from datetime import datetime
from getch import getch_or_timeout
from pypresence import Presence, ActivityType
from songs import Song

class Playlist:
    def __init__(self, options, database):
        self.options = options
        self.database = database
        self.songs = []

        # Songs meta info
        self.total_files = 0
        self.total_songs = 0
        self.count = 0
        self.duration = 0

        # Discord rich presence
        self.rpc = Presence(1299967728874029137)
        self.rpc.connect()

    def load_file(self, file, songs):
        '''
        Loads a anisongdb json file.
        '''
        try:
            with open(file, 'r', encoding="utf-8") as f:
                anisong_json = json.load(f)

        except Exception as e:
            logging.warning(f"Failed to decode {file}: {e}")
            return

        # Decode entry in json
        for entry in anisong_json:
            song = Song.decode(entry)

            # Some songs have no url, ignore them since we can't download them
            if not song.audio:
                logging.info(f"No audio link found: {song.full_name(self.options.prefer_english)}")
                continue

            songs.add(song)
            self.total_songs += 1

        self.total_files += 1

    def load_dir(self, dir, songs):
        '''
        Loads a directory of anisongdb json files.
        '''
        for file in os.listdir(dir):
            path = os.path.join(dir, file)

            # Load only files from directories, this will not recursively load subdirectories.
            if os.path.isfile(path):
                self.load_file(path, songs)

    def create(self):
        '''
        Creates a playlist by loading files and filtering songs.
        '''
        songs = set()

        for path in self.options.lists:
            if os.path.isfile(path):
                self.load_file(path, songs)
            elif os.path.isdir(path):
                self.load_dir(path, songs)
            else:
                logging.warning(f"Not a file or directory: {path}")

        # Filter song list
        if self.options.offline_mode:
            songs = filter(lambda song: os.path.isfile(song.file_path), songs)

        if self.options.min_difficulty:
            songs = filter(lambda song: self.options.min_difficulty <= song.difficulty if song.difficulty else False, songs)

        if self.options.max_difficulty:
            songs = filter(lambda song: song.difficulty <= self.options.max_difficulty if song.difficulty else False, songs)

        if self.options.search_artists:
            if self.options.exact_search:
                songs = filter(lambda song: song.artist.lower() in self.options.search_artists, songs)
            else:
                songs = filter(lambda song: any(artist in song.artist.lower() for artist in self.options.search_artists), songs)

        if self.options.search_anime:
            if self.options.exact_search:
                songs = filter(lambda song: song.anime.name.lower() in self.options.search_anime or song.anime.name_jp.lower() in self.options.search_anime, songs)
            else:
                songs = filter(lambda song: any(anime in song.anime.name.lower() or anime in song.anime.name_jp.lower() for anime in self.options.search_anime), songs)

        self.songs = list(songs)
        self.count = len(self.songs)
        self.duration = sum(song.duration for song in self.songs)
        random.shuffle(self.songs)

        if self.options.start_with_unplayed:
            self.songs.sort(key=lambda song: os.path.exists(song.file_path))

        minutes, seconds = divmod(int(self.duration), 60)
        hours, minutes = divmod(minutes, 60)
        print(f"Loaded {self.count}/{self.total_songs} songs from {self.total_files} files, with a total playlist duration of {hours}:{minutes:0<2}:{seconds:0<2}")

    def update_currently_playing(self, currently_playing):
        '''
        Updates output file to the current song.
        '''
        encoded = ""

        for char in currently_playing:
            value = ord(char)
            encoded += rf"[\{value}]" if value >= 256 else char

        with open(self.options.output, 'w') as f:
            f.write(encoded)

    def update_database(self, song):
        '''
        Updates last played information in the database.
        '''
        play_count, last_played = self.database.select(song)
        self.database.update(song)

        if play_count == 0:
            print("This is your first time playing this song.")
            return

        delta = datetime.now() - last_played
        print(f"You have played this song {play_count} {'time' if play_count == 1 else 'times'}, most recently on {last_played.strftime('%Y/%m/%d')} ({delta.days} {'day' if delta.days == 1 else 'days'} ago)")

    def update_rich_presence(self, song):
        '''
        Updates discord rich presence to the current song.
        '''
        details = song.title
        state = f"{song.artist} ({song.anime_name(self.options.prefer_english)})"

        anilist_link = song.anime_link("anilist")
        mal_link = song.anime_link("myanimelist")
        buttons = []

        # Shorten strings if they are too long
        if len(details) > 128:
            details = details[:125] + "..."
        elif len(details) < 2:
            details += "  "

        if len(state) > 128:
            state = song.artist
        if len(state) > 128:
            state = state[:125] + "..."
        elif len(state) < 2:
            state += "  "

        # Only include buttons if links exist
        if anilist_link:
            buttons.append({'label': "View on Anilist", 'url': anilist_link})
        if mal_link:
            buttons.append({'label': "View on MyAnimeList", 'url': mal_link})

        self.rpc.update(
            activity_type=ActivityType.LISTENING,
            details=details,
            state=state,
            start=time.time(),
            end=time.time() + song.duration,
            buttons=buttons,
        )

    def update_metadata(self):
        '''
        Updates all metadata for playlist.
        '''
        for song in self.songs:
            song.set_metadata(self.options.copyright_as_album, self.options.include_cover_art)

    def play(self):
        '''
        Plays songs from playlist.
        '''
        index = 0

        while index < self.count:
            song = self.songs[index]

            # We are permitted to download the song if we aren't in offline mode
            if not self.options.offline_mode:
                song.download(self.options.copyright_as_album, self.options.include_cover_art)

            # If we can't find the song, skip it. This should only happen if songs were deleted from the data folder.
            if not os.path.isfile(song.file_path):
                logging.warning(f"File not found: {song.file_path}")
                continue

            currently_playing = f"{song.full_name(self.options.prefer_english)} ({index+1}/{self.count}) {{{song.difficulty}%}}"
            print(f"Currently playing: {currently_playing}")

            if self.options.output:
                self.update_currently_playing(currently_playing)

            self.update_database(song)

            if not self.options.disable_discord_rpc:
                self.update_rich_presence(song)

            song.play(self.options.player)

            # Check user input for if we want to do some extra function
            char = getch_or_timeout(0.3)
            logging.debug(f"Got character: {char}")

            if char == b'q':
                index = max(0, index - 1)
            elif char == b'\x1b':
                break
            else:
                index += 1

        logging.info("Playlist has ended")
