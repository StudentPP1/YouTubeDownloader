import json
import os
import re
import time
import webbrowser

import keyboard
import pyautogui
import pyperclip
import win32api
import win32con
from dotenv import load_dotenv

from youtube import YouTube

load_dotenv()

JS_TRACKS: str = """
let rows = document.querySelectorAll('[data-testid="tracklist-row"]');
let tracks = [...rows].map(r => ({
    title: r.querySelector('[data-testid="internal-track-link"] div')?.innerText,
    artist: r.querySelector('a[href*="/artist/"]')?.innerText
})).filter(t => t.title && t.artist);
copy(JSON.stringify(tracks));
"""

JS_TOTAL: str = """
copy(document.querySelector('[data-encore-id="text"].encore-internal-color-text-subdued')?.innerText || '0');
"""

CLICK_X: int = 500
CLICK_Y: int = 550
PROGRESS_FILE: str = "spotify_progress.txt"


class Spotify:
    SCROLL_SPD: int = 120
    SCROLL_DELAY: float = 0.15

    def __init__(self, youtube: YouTube) -> None:
        self.youtube = youtube

    def _load_progress(self) -> int:
        if not os.path.exists(PROGRESS_FILE):
            return 0
        try:
            return int(open(PROGRESS_FILE).read().strip())
        except ValueError:
            return 0

    def _save_progress(self, count: int) -> None:
        with open(PROGRESS_FILE, "w") as f:
            f.write(str(count))

    def _open_and_wait(self) -> None:
        webbrowser.open("https://open.spotify.com/collection/tracks")
        time.sleep(5)

    def _focus_page(self) -> None:
        win32api.SetCursorPos((CLICK_X, CLICK_Y))
        win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
        win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
        time.sleep(0.3)

    def _run_js(self, js: str) -> str:
        pyautogui.hotkey("f12")
        time.sleep(1.5)
        pyautogui.click(1500, 1000)
        time.sleep(0.3)
        keyboard.write(js.strip(), delay=0.01)
        time.sleep(0.3)
        keyboard.press_and_release("enter")
        time.sleep(1)
        pyautogui.hotkey("f12")
        time.sleep(0.3)
        self._focus_page()
        return pyperclip.paste()

    def _get_total(self) -> int:
        raw = self._run_js(JS_TOTAL)
        m = re.search(r"(\d+)\s+songs", raw)
        return int(m.group(1)) if m else 0

    def _parse_dom(self) -> list[dict]:
        raw = self._run_js(JS_TRACKS)
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return []

    def _scroll(self, steps: int = 10) -> None:
        for _ in range(steps):
            win32api.mouse_event(win32con.MOUSEEVENTF_WHEEL, 0, 0, -self.SCROLL_SPD, 0)
            time.sleep(self.SCROLL_DELAY)

    def _scrape_liked_tracks(self) -> list[dict]:
        self._open_and_wait()
        self._focus_page()

        seen: set[str] = set()
        tracks: list[dict] = []

        def add_batch(batch: list[dict]) -> None:
            for t in batch:
                key = t["title"].lower()
                if key not in seen:
                    seen.add(key)
                    tracks.append(t)
                    print(f"  [{len(tracks):>3}] {t['title']} - {t['artist']}")

        add_batch(self._parse_dom())

        while True:
            self._scroll(steps=10)
            before = len(tracks)
            add_batch(self._parse_dom())
            if len(tracks) == before:
                break

        return tracks

    def download_liked_tracks(self) -> None:
        tracks = self._scrape_liked_tracks()

        if not tracks:
            print("No tracks found.")
            return

        prev = self._load_progress()
        total = len(tracks)

        print(f"Available: {total} | Previously downloaded: {prev}")

        raw = input(
            f"How many to download? (Enter = new only [{total - prev}], number = custom): "
        ).strip()

        if raw == "":
            to_download = tracks[: total - prev]
        else:
            try:
                to_download = tracks[: int(raw)]
            except ValueError:
                print("Invalid input.")
                return

        if not to_download:
            print("Nothing new to download.")
            return

        skipped = 0
        count = len(to_download)

        for i, track in enumerate(to_download, 1):
            artist, title = track["artist"], track["title"]
            print(f"[{i}/{count}] {title} - {artist}")

            yt_url = self.youtube.search_url(artist, title)
            if not yt_url:
                print("  Not found, skipping.")
                skipped += 1
                continue

            print(f"  -> {yt_url}")
            try:
                self.youtube.download_track(yt_url)
            except Exception as e:
                print(f"  Error: {e}")
                skipped += 1

        downloaded = count - skipped
        self._save_progress(prev + downloaded)
        print(f"Done: {downloaded}/{count} downloaded.")