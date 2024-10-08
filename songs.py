
import json, logging, os, requests, subprocess
from dataclasses import dataclass
from hosts import hosts
from mutagen.easyid3 import EasyID3
from mutagen.mp3 import MP3

@dataclass
class Anime:
    name: str
    name_jp: str
    season: str
    type: str

@dataclass
class Song:
    anime: Anime
    title: str
    artist: str
    type: str
    difficulty: float
    audio: str | None
    duration: float | None

    def __hash__(self):
        if self.audio:
            base = self.audio[-10:-4].encode()
            return int.from_bytes(base)
        return 0

    @classmethod
    def decode(cls, data):
        return cls(
            Anime(
                data['animeENName'],
                data['animeJPName'],
                data['animeVintage'],
                data['animeType'],
            ),
            data['songName'],
            data['songArtist'],
            data['songType'],
            data['songDifficulty'],
            data['audio'][-10:] if data['audio'] else None, # Only get file name
            data['songLength']
        )

    @property
    def file_path(self):
        return os.path.join("data", self.audio)

    def name(self, prefer_english: bool=False):
        return f"{self.artist} - {self.title} [{self.anime.name if prefer_english else self.anime.name_jp}]"

    def download(self):
        '''
        Downloads the song into our collection.
        '''
        # Don't download the file if we already have it
        if os.path.isfile(self.file_path):
            return

        success = False

        # Sometimes, hosts can be out of date. Therefore, try different ones until we get a hit.
        for host in hosts:
            url = host + self.audio

            try:
                r = requests.get(url)
            except Exception as e:
                logging.warning(f"Download failed: {e}")
                continue

            if not r.ok:
                continue

            success = True
            break

        if not success:
            logging.warning(f"Failed to get audio for {self.name}")
            return

        # Save file
        with open(self.file_path, 'wb') as f:
            logging.debug(f"Saving file: {self.file_path}")
            f.write(r.content)

        # Set the metadata
        self.set_metadata()

    def set_metadata(self):
        '''
        Sets the metadata of the song to something more reasonable.
        '''
        song = MP3(self.file_path, ID3=EasyID3)

        if song.tags is None:
            logging.warning(f"Failed to load and set tags: {self.file_path}")
            return

        # Get old title information, which is usually encoding information
        encoding = ""
        if song.tags and 'title' in song.tags:
            encoding = song.tags['title'][0]

        song.delete()

        if encoding:
            song.tags['encodedby'] = encoding

        # Add the rest of the information
        song.tags['artist'] = self.artist
        song.tags['title'] = self.title
        song.tags['website'] = self.audio
        song.tags['copyright'] = self.anime.name_jp
        song.tags['media'] = f"{self.anime.type} Anime"
        song.save()

        logging.debug(f"Updated tags: {self.file_path}")
        logging.debug(f"Previous tags title: {encoding}")

    def play(self, player):
        '''
        Plays the song through the preferred player.
        '''
        subprocess.run(f"{player} {self.file_path}", shell=True, stdout=subprocess.PIPE)
