
import argparse, logging, os, pathlib
from database import Database
from options import Options
from playlist import Playlist

def main():
    # Parse player options from file and command line
    options = Options()
    options.from_file("options.conf")
    options.from_options()

    # Create logger
    logger = logging.getLogger(__name__)
    log_level = getattr(logging, options.log_level, 30)
    logging.basicConfig(level=log_level, format="[%(levelname)s] %(message)s")

    # Ensure we have correct directories
    os.makedirs("data", exist_ok=True)

    # Set up database
    db = Database("player.db")
    db.initalise()

    # Start playlist
    playlist = Playlist(options, db)
    playlist.create()
    playlist.play()

if __name__ == "__main__":
    main()
