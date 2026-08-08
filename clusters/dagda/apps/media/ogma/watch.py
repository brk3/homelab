#!/usr/bin/env python3
"""Ogma: watches for finished qBittorrent downloads and links them into Plex's TV/Movies folders.

Watches WATCH_DIR (qBittorrent's completed-downloads folder) for new top-level
entries and hands each one to link_media's linking logic. Also scans whatever's
already there on startup — link_media.link_file() is idempotent (skips
destinations that already exist), so re-processing existing entries is safe
and lets Ogma catch up on anything it missed while it wasn't running.
"""
import logging
import os
import sys
import time
from pathlib import Path

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from link_media import (
    MIN_VIDEO_SIZE_MB,
    MOVIES_ROOT,
    TV_ROOT,
    build_movie_dest,
    build_tv_dest,
    guess_media_type,
    guessit,
    iter_video_files,
    link_file,
    setup_logging,
)

WATCH_DIR = Path(os.environ.get("WATCH_DIR", "/data/downloads/complete"))
SETTLE_SECONDS = int(os.environ.get("SETTLE_SECONDS", "5"))


def process_entry(
    path: Path,
    tv_root: Path = TV_ROOT,
    movies_root: Path = MOVIES_ROOT,
    min_size_mb: int = MIN_VIDEO_SIZE_MB,
):
    if not path.exists():
        return
    # Prefer the containing folder's title/year over the file's: release folder
    # names are almost always properly cased even when the file inside isn't.
    folder_info = guessit(path.name) if path.is_dir() else {}
    for f in iter_video_files(path, min_size_mb=min_size_mb):
        info = guessit(f.name)
        if folder_info.get("title"):
            info["title"] = folder_info["title"]
        if folder_info.get("year"):
            info["year"] = folder_info["year"]
        media_type = guess_media_type(info)
        dest = build_tv_dest(f, info, root=tv_root) if media_type == "episode" else build_movie_dest(f, info, root=movies_root)
        if dest is None:
            logging.warning("Could not determine destination for %s (guessit: %s)", f, info)
            continue
        link_file(f, dest)


class CompletedDownloadHandler(FileSystemEventHandler):
    def on_created(self, event):
        self._handle(event.src_path)

    def on_moved(self, event):
        self._handle(event.dest_path)

    def _handle(self, raw_path: str):
        path = Path(raw_path)
        if path.parent != WATCH_DIR:
            return  # only react to new top-level entries, not incremental writes inside them
        logging.info("New entry detected: %s", path)
        time.sleep(SETTLE_SECONDS)
        process_entry(path)


def main():
    setup_logging()
    if not WATCH_DIR.exists():
        logging.error("Watch directory does not exist: %s", WATCH_DIR)
        sys.exit(1)

    logging.info("Scanning existing entries under %s", WATCH_DIR)
    for entry in WATCH_DIR.iterdir():
        process_entry(entry)

    logging.info("Watching %s for new downloads", WATCH_DIR)
    observer = Observer()
    observer.schedule(CompletedDownloadHandler(), str(WATCH_DIR), recursive=False)
    observer.start()
    try:
        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()


if __name__ == "__main__":
    main()
