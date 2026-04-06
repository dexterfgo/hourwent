"""
Home Assistant Automation Generator
Regenerates home_assistant_automations.yaml for any START_HOUR / END_HOUR range.

Usage:
    python generate_ha_automations.py
    # or override the range inline:
    START_HOUR=8 END_HOUR=22 python generate_ha_automations.py
"""

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

START_HOUR    = int(os.getenv("START_HOUR", "6"))
END_HOUR      = int(os.getenv("END_HOUR",   "0"))
ENTITY_ID     = os.getenv("HA_ENTITY_ID", "media_player.living_room_speaker")
OUTPUT_FILE   = Path(__file__).parent / "home_assistant_automations.yaml"

GREETINGS = {
    **{h: "Good morning"   for h in range(6, 12)},
    **{h: "Good afternoon" for h in range(12, 18)},
    **{h: "Good evening"   for h in range(18, 24)},
    0: "Good night",
}

def build_hour_range(start: int, end: int) -> list[int]:
    hours = []
    h = start
    while True:
        hours.append(h)
        if h == end:
            break
        h = (h + 1) % 24
        if len(hours) >= 24:
            break
    return hours

def hour_label(h: int) -> str:
    if h == 0:  return "Midnight"
    if h == 12: return "12 Noon"
    period  = "AM" if h < 12 else "PM"
    display = h if h <= 12 else h - 12
    return f"{display} {period}"

def announcement(h: int) -> str:
    if h == 0:  return "Good night! It is now midnight."
    if h == 12: return "Good afternoon! It is now 12 noon."
    period  = "AM" if h < 12 else "PM"
    display = h if h <= 12 else h - 12
    greeting = GREETINGS.get(h, "Hello")
    return f"{greeting}! It is now {display} {period}."

def render_yaml(hours: list[int]) -> str:
    header = (
        "# ──────────────────────────────────────────────────────────────────────────\n"
        "# Home Assistant – Hourly Time Announcements (auto-generated)\n"
        f"# Range: {hour_label(hours[0])} → {hour_label(hours[-1])}  ({len(hours)} automations)\n"
        "# Re-generate: python generate_ha_automations.py\n"
        "# ──────────────────────────────────────────────────────────────────────────\n\n"
    )
    blocks = []
    for h in hours:
        time_str = f"{h:02d}:00:00"
        blocks.append(
            f"- id: time_announce_{h:04d}\n"
            f'  alias: "Time Announcement – {hour_label(h)}"\n'
            f"  trigger:\n"
            f"    - platform: time\n"
            f'      at: "{time_str}"\n'
            f"  action:\n"
            f"    - service: tts.google_translate_say\n"
            f"      target:\n"
            f"        entity_id: {ENTITY_ID}\n"
            f"      data:\n"
            f'        message: "{announcement(h)}"\n'
            f"        language: en\n"
        )
    return header + "\n".join(blocks) + "\n"

if __name__ == "__main__":
    hours = build_hour_range(START_HOUR, END_HOUR)
    yaml  = render_yaml(hours)
    OUTPUT_FILE.write_text(yaml)
    print(f"Written {len(hours)} automations to {OUTPUT_FILE}")
    print(f"Hours: {hours}")
