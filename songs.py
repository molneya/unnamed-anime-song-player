
import filetype, json, logging, os, requests, subprocess, time
from dataclasses import dataclass
from hosts import hosts
from mutagen.easyid3 import EasyID3
from mutagen.id3 import ID3, APIC
from mutagen.mp3 import MP3
from typing import Dict

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
    id: int
    season: str
    linked_ids: Dict[str, int]

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
            data['songLength'],
            data['annSongId'],
            data['animeVintage'],
            data['linked_ids'],
        )

    @property
    def file_path(self):
        return os.path.join("data", self.audio)

    @property
    def image_file_path(self):
        if 'anilist' not in self.linked_ids:
            return
        if not self.linked_ids['anilist']:
            return
        return os.path.join("data", str(self.linked_ids['anilist']))

    def full_name(self, prefer_english: bool=False):
        return f"{self.artist} - {self.title} [{self.anime_name(prefer_english)}]"

    def anime_name(self, prefer_english: bool=False):
        return self.anime.name if prefer_english else self.anime.name_jp

    def anime_link(self, preferred_site: str="anilist"):
        base_urls = {
            'myanimelist': "https://myanimelist.net/anime/",
            'anidb': "https://anidb.net/anime/",
            'anilist': "https://anilist.co/anime/",
            'kitsu': "https://kitsu.app/anime/",
        }

        if preferred_site not in self.linked_ids:
            return None
        if not self.linked_ids[preferred_site]:
            return

        return base_urls[preferred_site] + str(self.linked_ids[preferred_site])

    def download(self, copyright_as_album=False, include_cover_art=False):
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
            logging.warning(f"Failed to get audio for {self.audio}")
            return

        # Save file
        with open(self.file_path, 'wb') as f:
            logging.debug(f"Saving file: {self.file_path}")
            f.write(r.content)

        # Set the metadata
        self.set_metadata(copyright_as_album, include_cover_art)

    def set_metadata(self, copyright_as_album=False, include_cover_art=False):
        '''
        Sets the metadata of the song to something more reasonable.
        '''
        # We can't update tags if the song isn't downloaded
        if not os.path.isfile(self.file_path):
            return

        song = MP3(self.file_path, ID3=EasyID3)

        if not song.tags:
            song.tags = EasyID3()

        # Get encoding information (or title, which sometimes also has encoding information)
        encoding = ""
        if 'encodedby' in song.tags:
            encoding = song.tags['encodedby'][0]
        elif 'title' in song.tags:
            encoding = song.tags['title'][0]

        # Delete existing tags
        song.delete()

        # Add tag information
        song.tags['artist'] = self.artist
        song.tags['title'] = self.title
        song.tags['website'] = self.audio
        song.tags['media'] = f"{self.anime.type} Anime"
        song.tags['version'] = self.type
        song.tags['compilation'] = "1"
        song.tags['tracknumber'] = str(self.id)
        song.tags['date'] = self.season[-4:]

        if encoding:
            song.tags['encodedby'] = encoding

        if copyright_as_album:
            song.tags['album'] = self.anime.name_jp
        else:
            song.tags['copyright'] = self.anime.name_jp

        song.save()

        if include_cover_art:
            self.set_image()

        logging.debug(f"Updated tags: {self.file_path}")
        logging.debug(f"Previous encoding: {encoding}")

    def download_image(self):
        '''
        Downloads anime cover art.
        '''
        if not self.image_file_path:
            logging.warning(f"Anilist ID not linked: {self.audio}")
            return

        query = """
            query ($id: Int) {
                Media(id: $id, type: ANIME) {
                    coverImage {
                        extraLarge
                    }
                }
            }
        """
        id = self.linked_ids['anilist']

        r = requests.post(
            "https://graphql.anilist.co",
            json={'query': query, 'variables': {"id": id}},
        )

        # Anilist rate limit is 30 requests per minute
        time.sleep(2)

        if not r.ok:
            logging.warning(f"Bad request for Anilist query")
            return

        json = r.json()
        image_url = json['data']['Media']['coverImage']['extraLarge']

        r = requests.get(image_url)

        if not r.ok:
            logging.warning(f"Bad request Anilist image query")
            return

        with open(self.image_file_path, 'wb') as f:
            logging.debug(f"Saving file: {self.image_file_path}")
            f.write(r.content)

    def set_image(self):
        '''
        Sets mp3 cover art.
        '''
        if not self.image_file_path:
            return
        if not os.path.exists(self.image_file_path):
            self.download_image()

        song = MP3(self.file_path)

        song.tags.add(
            APIC(
                encoding=0,
                type=3,
                mime=filetype.guess(self.image_file_path).mime,
                desc=u"Cover",
                data=open(self.image_file_path, 'rb').read(),
            )
        )

        song.save()
        logging.debug(f"Updated image: {self.file_path}")

    def play(self, player):
        '''
        Plays the song through the preferred player.
        '''
        subprocess.run(f"{player} {self.file_path}", shell=True, stdout=subprocess.PIPE)
