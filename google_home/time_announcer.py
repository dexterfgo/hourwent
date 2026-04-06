"""
Google Home Time Announcer
Announces the time every hour within a configurable range on a designated
Chromecast / Google Home speaker using pychromecast.

Setup:
    pip install -r requirements.txt
    cp .env.example .env   # set SPEAKER_NAME, START_HOUR, END_HOUR
    python time_announcer.py

The script runs as a persistent daemon; keep it running (e.g. via systemd or
screen) for continuous operation.
"""

import os
import time
import datetime
import logging
import schedule
import pychromecast
from dotenv import load_dotenv

load_dotenv()

# Warn if .env is readable by group or others (should be chmod 600)
_env_path = os.path.join(os.path.dirname(__file__), ".env")
if os.path.exists(_env_path) and (os.stat(_env_path).st_mode & 0o077):
    import warnings
    warnings.warn(".env permissions are too open. Run: chmod 600 .env", stacklevel=1)

# ── Configuration ─────────────────────────────────────────────────────────────
SPEAKER_NAME  = os.getenv("GOOGLE_SPEAKER_NAME", "Living Room speaker")
TTS_LANGUAGE  = os.getenv("TTS_LANGUAGE", "en-us")
TTS_VOLUME    = float(os.getenv("TTS_VOLUME", "0.8"))
SCAN_TIMEOUT  = 10

# START_HOUR and END_HOUR are 24-hour integers (0–23), both inclusive.
# Default: 6 AM → midnight (0).  Supports wrap-around (e.g. 22 → 0).
START_HOUR = int(os.getenv("START_HOUR", "6"))
END_HOUR   = int(os.getenv("END_HOUR",   "0"))   # 0 = midnight

def _build_hour_range(start: int, end: int) -> set[int]:
    """Return the set of hours to announce, handling midnight wrap-around."""
    hours = set()
    h = start
    while True:
        hours.add(h)
        if h == end:
            break
        h = (h + 1) % 24
        if len(hours) >= 24:   # full day guard
            break
    return hours

ANNOUNCE_HOURS = _build_hour_range(START_HOUR, END_HOUR)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger(__name__)

# ── Helpers ───────────────────────────────────────────────────────────────────
def build_announcement(hour: int) -> str:
    if hour == 0:
        return "Good night! It is now midnight."
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
    from urllib.parse import quote
    return (
        f"https://translate.google.com/translate_tts"
        f"?ie=UTF-8&client=tw-ob&tl={lang}&q={quote(text)}"
    )


def find_speaker(name: str):
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
    log.info(f"Connected to: {cast.device.friendly_name} ({cast.host}:{cast.port})")
    return cast


def announce(cast, text: str) -> None:
    log.info(f"Announcing: {text!r}")
    cast.set_volume(TTS_VOLUME)
    mc = cast.media_controller
    mc.play_media(get_tts_url(text, TTS_LANGUAGE), "audio/mpeg")
    mc.block_until_active(timeout=10)


# ── Scheduled job ─────────────────────────────────────────────────────────────
def hourly_job() -> None:
    hour = datetime.datetime.now().hour

    if hour not in ANNOUNCE_HOURS:
        return

    text = build_announcement(hour)
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
    log.info("Google Home Time Announcer starting.")
    log.info(f"Target speaker : {SPEAKER_NAME}")
    log.info(f"Active hours   : {sorted(ANNOUNCE_HOURS)} ({len(ANNOUNCE_HOURS)} slots)")

    cast = find_speaker(SPEAKER_NAME)
    if cast is None:
        log.warning("Device not found at startup — will retry each hour.")
    else:
        cast.disconnect()

    schedule.every().hour.at(":00").do(hourly_job)
    log.info("Scheduler running. Press Ctrl+C to stop.")

    while True:
        schedule.run_pending()
        time.sleep(30)
