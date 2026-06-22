import os
from os import path

from const import destination_path
from spotify import Spotify
from youtube import YouTube


def main() -> None:
    youtube = YouTube()
    spotify = Spotify(youtube)

    while True:
        try:
            url = input("\nEnter YouTube link, 'liked' for Spotify likes, or 'q' to exit: ").strip()

            if not path.exists(destination_path):
                os.mkdir(destination_path)

            if url == "q":
                print("See you soon")
                break
            elif url == "liked":
                spotify.download_liked_tracks()
            elif url.startswith("https://www.youtube.com/watch?"):
                youtube.download_track(url)
            elif url.startswith("https://www.youtube.com/playlist?"):
                youtube.download_playlist(url)
            else:
                print("Unknown input.")

        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"Error: {e}")


if __name__ == "__main__":
    main()