"""
Google Home Time Announcer
Announces the time every hour from 6 AM to midnight on a designated Chromecast/
Google Home speaker using pychromecast's text-to-speech capability.

Setup:
    pip install -r requirements.txt
    cp .env.example .env   # fill in SPEAKER_NAME
    python time_announcer.py

The script runs as a persistent daemon; keep it running (e.g. via systemd or
screen) for continuous operation.
"""

import os
import time
import datetime
import socket
import logging
import schedule
import pychromecast
from pychromecast.controllers.media import MediaController
from dotenv import load_dotenv

load_dotenv()

# ── Configuration ─────────────────────────────────────────────────────────────
SPEAKER_NAME     = os.getenv("GOOGLE_SPEAKER_NAME", "Living Room speaker")
ANNOUNCE_HOURS   = set(range(6, 24)) | {0}   # 6 AM – 11 PM + midnight
TTS_LANGUAGE     = os.getenv("TTS_LANGUAGE", "en-us")
TTS_VOLUME       = float(os.getenv("TTS_VOLUME", "0.8"))  # 0.0 – 1.0
SCAN_TIMEOUT     = 10   # seconds to scan for Chromecast devices

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger(__name__)

# ── Helpers ───────────────────────────────────────────────────────────────────
def build_announcement(hour: int) -> str:
    """Return a natural-language time string for the given hour (0-23)."""
    if hour == 0:
        return "Good night! It is now midnight."
    if hour == 6:
        return "Good morning! It is now 6 AM."
    if hour == 12:
        return "Good afternoon! It is now 12 noon."

    period = "AM" if hour < 12 else "PM"
    display = hour if hour <= 12 else hour - 12
    if hour < 12:
        greeting = "Good morning"
    elif hour < 18:
        greeting = "Good afternoon"
    else:
        greeting = "Good evening"

    return f"{greeting}! It is now {display} {period}."


def get_tts_url(text: str, lang: str = "en-us") -> str:
    """
    Build a Google Translate TTS URL for the announcement.
    This is a free, no-auth approach for personal/local use.
    Replace with a proper TTS service (Google Cloud TTS, etc.) for production.
    """
    from urllib.parse import quote
    encoded = quote(text)
    return (
        f"https://translate.google.com/translate_tts"
        f"?ie=UTF-8&client=tw-ob&tl={lang}&q={encoded}"
    )


def find_speaker(name: str) -> pychromecast.Chromecast | None:
    """Scan the local network and return the named Chromecast device."""
    log.info(f"Scanning for Google Home device: '{name}' …")
    chromecasts, browser = pychromecast.get_listed_chromecasts(
        friendly_names=[name], timeout=SCAN_TIMEOUT
    )
    pychromecast.discovery.stop_discovery(browser)

    if not chromecasts:
        log.warning(f"Device '{name}' not found on the local network.")
        return None

    cast = chromecasts[0]
    cast.wait()
    log.info(f"Connected to: {cast.device.friendly_name} "
             f"({cast.host}:{cast.port})")
    return cast


def announce(cast: pychromecast.Chromecast, text: str) -> None:
    """Play a TTS announcement on the Chromecast device."""
    log.info(f"Announcing: {text!r}")
    cast.set_volume(TTS_VOLUME)

    mc: MediaController = cast.media_controller
    tts_url = get_tts_url(text, TTS_LANGUAGE)
    mc.play_media(tts_url, "audio/mpeg")
    mc.block_until_active(timeout=10)


# ── Scheduled job ─────────────────────────────────────────────────────────────
def hourly_job() -> None:
    now = datetime.datetime.now()
    hour = now.hour

    if hour not in ANNOUNCE_HOURS:
        return   # outside the 6 AM – midnight window; do nothing

    text = build_announcement(hour)

    # Re-discover the device each time (handles reboots / IP changes)
    cast = find_speaker(SPEAKER_NAME)
    if cast is None:
        log.error("Skipping announcement — device unavailable.")
        return

    try:
        announce(cast, text)
    except Exception as exc:
        log.error(f"Announcement failed: {exc}")
    finally:
        cast.disconnect()


# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    log.info(f"Google Home Time Announcer starting.")
    log.info(f"Target speaker : {SPEAKER_NAME}")
    log.info(f"Active hours   : 6 AM – midnight")

    # Verify device is reachable on startup
    cast = find_speaker(SPEAKER_NAME)
    if cast is None:
        log.warning("Device not found at startup — will retry each hour.")
    else:
        log.info("Device reachable. Disconnecting until first scheduled run.")
        cast.disconnect()

    # Schedule at the top of every hour (:00)
    schedule.every().hour.at(":00").do(hourly_job)
    log.info("Scheduler running. Press Ctrl+C to stop.")

    while True:
        schedule.run_pending()
        time.sleep(30)
