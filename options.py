
import argparse, pathlib, logging, shlex

class Options:
    def __init__(self):
        self.lists = []
        self.player = "mpv --no-video"
        self.output = r"skins\CurrentlyPlaying\CurrentlyPlaying.txt"
        self.prefer_english = False
        self.offline_mode = False
        self.log_level = "WARNING"
        self.min_difficulty = None
        self.max_difficulty = None
        self.search_artists = []
        self.search_anime = []
        self.exact_search = False
        self.copyright_as_album = False
        self.update_metadata = False
        self.start_with_unplayed = False

    def from_file(self, file_path):
        '''
        Sets options from file. This will overwrite the default options.
        '''
        with open(file_path, 'r') as f:
            for line in f.readlines():
                line = line.strip()

                # Skip lines without content or comments
                if not line or line.startswith('#'):
                    continue

                # Unpack key/value pairs, skipping if we get something invalid
                try:
                    key, value = line.split('=', 1)
                except ValueError:
                    continue

                try:
                    match key.lower():
                        # String values
                        case 'player' | 'output' | 'log_level':
                            setattr(self, key, value)
                        # Switches
                        case 'prefer_english' | 'offline_mode' | 'exact_search' | 'copyright_as_album' | 'update_metadata' | 'start_with_unplayed':
                            setattr(self, key, bool(int(value)))
                        # Floats
                        case 'min_difficulty' | 'max_difficulty':
                            setattr(self, key, float(value))
                        # Lists
                        case 'lists' | 'search_artists' | 'search_anime':
                            setattr(self, key, shlex.split(value))
                        # Ignore anything else
                        case _:
                            print(f"Ignoring unknown option: '{key}'")

                except (ValueError, AttributeError):
                    print(f"Ignoring invalid value for option {key}: '{value}'")

    def from_options(self):
        '''
        Sets options from command line arguments. This will overwrite options loaded from file.
        '''
        parser = argparse.ArgumentParser()
        parser.add_argument("-l", "--lists", default=self.lists, type=pathlib.Path, nargs='+', help="lists to play, can be either directories or files")
        parser.add_argument("-p", "--player", default=self.player, type=str, help="the audio player to use")
        parser.add_argument("-o", "--output", default=self.output, type=pathlib.Path, help="output file of the currently playing song")
        parser.add_argument("--prefer-english", default=self.prefer_english, action="store_true", help="show titles in english")
        parser.add_argument("--offline-mode", default=self.offline_mode, action="store_true", help="use the program without features requiring an internet connection")
        parser.add_argument("--log-level", default=self.log_level, type=str, help="level of logs to show")
        parser.add_argument("--min-difficulty", default=self.min_difficulty, type=float, metavar="MIN", help="minimum song difficulty to play")
        parser.add_argument("--max-difficulty", default=self.max_difficulty, type=float, metavar="MAX", help="maximum song difficulty to play")
        parser.add_argument("--search-artists", default=self.search_artists, type=str, nargs='*', metavar="ARTIST", help="search for artists to play from")
        parser.add_argument("--search-anime", default=self.search_anime, type=str, nargs='*', metavar="ANIME", help="search for anime to play from")
        parser.add_argument("--exact-search", default=self.exact_search, action="store_true", help="show results for exact searches only")
        parser.add_argument("--copyright-as-album", default=self.copyright_as_album, action="store_true", help="sets mp3 copyright info as album info instead")
        parser.add_argument("--update-metadata", default=self.copyright_as_album, action="store_true", help="updates mp3 metadata for all previously downloaded songs")
        parser.add_argument("--start-with-unplayed", default=self.start_with_unplayed, action="store_true", help="starts playlist with unplayed songs first")
        args = parser.parse_args()

        # Set values
        for key, value in vars(args).items():
            setattr(self, key, value)
