import os
import shutil
from typing import Any

import eyed3  # type: ignore[import-untyped]
import requests
import yt_dlp  # type: ignore[import-untyped]

from const import destination_path, ydl_opts

class YouTube:
    SPLIT_LETTER: str = "["

    def __init__(self) -> None:
        pass

    def _load_metadata_to_mp3(self, file_mp3: str, metadata: Any, url: str) -> str:
        audio_file = eyed3.load(file_mp3)
        if audio_file is None or audio_file.tag is None:
            audio_file.initTag()  # type: ignore[union-attr]

        video_id = url[url.index("=") + 1:]
        title = file_mp3.split(self.SPLIT_LETTER)[0].strip()

        with open("img.jpg", "wb") as f:
            f.write(requests.get(f"https://i.ytimg.com/vi/{video_id}/hqdefault.jpg").content)

        audio_file.tag.title = title.strip()  # type: ignore[union-attr]
        audio_file.tag.images.set(3, open("img.jpg", "rb").read(), "image/jpeg")  # type: ignore[union-attr]
        audio_file.tag.save()  # type: ignore[union-attr]

        new_name = title + ".mp3"
        os.rename(file_mp3, new_name)
        return new_name

    def search_url(self, artist: str, title: str) -> str | None:
        query = f"ytsearch1:{artist} - {title} official audio"
        opts: Any = {**ydl_opts, "quiet": True, "skip_download": True}

        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(query, download=False)
            entries = info.get("entries", [])
            if entries and entries[0]:
                return f"https://www.youtube.com/watch?v={entries[0]['id']}"

        return None

    def download_track(self, url: str) -> None:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:  # type: ignore[arg-type]
            metadata: Any = ydl.extract_info(url, download=False)
            ydl.download([url])

        download_file: str | None = None
        while download_file is None:
            for file in os.listdir():
                if file.endswith(".mp3"):
                    download_file = file

        audio = self._load_metadata_to_mp3(download_file, metadata, url)
        shutil.move(audio, os.path.join(destination_path, audio))

        if os.path.exists("img.jpg"):
            os.remove("img.jpg")

    def download_playlist(self, url: str) -> None:
        opts: Any = {**ydl_opts, "quiet": True, "skip_download": True, "extract_flat": True}

        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=False)

        entries = info.get("entries", []) if info else []
        video_urls = [f"https://www.youtube.com/watch?v={e['id']}" for e in entries if e]
        total = len(video_urls)

        for i, video_url in enumerate(video_urls, 1):
            print(f"[{i}/{total}]")
            self.download_track(video_url)