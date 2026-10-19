# -*- coding: utf-8 -*-
"""Live ticker for the progress box.

Shows the progress box moving (elapsed time ticking + "fetching info" line) from the very first
second, until yt-dlp's real progress hook takes over. Stops by itself on stop.set(), when the
message is gone, or after max_seconds.
"""
import threading
import time

from HELPERS.fancy_progress import build_progress_text
from HELPERS.safe_messeger import safe_edit_message_text


def start_prep_ticker(user_id, msg_id, downloading=True, interval=3.0, max_seconds=120):
    stop = threading.Event()
    t0 = time.time()

    def _run():
        while not stop.wait(interval):
            elapsed = time.time() - t0
            if elapsed > max_seconds:
                break
            try:
                text = build_progress_text(
                    downloading, None, 0, 0, 0, elapsed=elapsed,
                    prefix="🔎 <i>Fetching video info, download starting...</i>",
                )
                if stop.is_set():
                    break
                if safe_edit_message_text(user_id, msg_id, text) is None:
                    break
            except Exception:
                break

    threading.Thread(target=_run, name="prep-progress-ticker", daemon=True).start()
    return stop
