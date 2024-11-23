
import argparse, logging, os, pathlib, traceback
from database import Database
from options import Options
from playlist import Playlist

def main():
    print("unnamed music player version: 20241124")

    # Parse player options from file and command line
    options = Options()
    options.from_file("options.conf")
    options.from_options()

    # Create logger
    logger = logging.getLogger(__name__)
    log_level = getattr(logging, options.log_level, 30)
    logging.basicConfig(level=log_level, format="[%(levelname)s] %(message)s")

    # Ensure we have correct directories
    os.makedirs(options.songs_path, exist_ok=True)
    os.makedirs(options.covers_path, exist_ok=True)

    # Set up database
    db = Database("player.db")
    db.initalise()

    # Start playlist
    playlist = Playlist(options, db)
    playlist.create()

    if options.update_metadata:
        print("Updating metadata of previously downloaded songs...")
        playlist.update_metadata()

    playlist.play()

if __name__ == "__main__":
    try:
        main()
    except:
        with open("trackback.log", 'w') as log_file:
            traceback.print_exc(file=log_file)
            raise
