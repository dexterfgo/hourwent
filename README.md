# Smart Speaker – Hourly Time Announcements

Announces the current time every hour on a designated speaker. The active time range is fully configurable. All three major platforms are supported.

**Default range:** 6:00 AM – 12:00 midnight (19 hourly slots)

---

## Configuring the Time Range

All platforms share the same two settings:

| Variable | Meaning | Example |
|----------|---------|---------|
| `START_HOUR` | First hour to announce (24-h, 0–23) | `6` = 6 AM |
| `END_HOUR` | Last hour to announce (24-h, 0–23) | `0` = midnight, `22` = 10 PM |

Both hours are **inclusive**. Midnight wrap-around is supported — e.g. `START_HOUR=22 END_HOUR=1` covers 10 PM → 11 PM → midnight → 1 AM.

---

## Platform Quick-Start

### 1. Amazon Alexa

**Folder:** `alexa/`  **Requirements:** Node.js 18+

```bash
cd alexa
cp .env.example .env      # set credentials, speaker name, and hour range
npm install
npm run setup
```

- Logs into your Amazon account and creates one daily Alexa Routine per hour.
- Re-run any time you change `START_HOUR` / `END_HOUR`; existing routines are skipped.
- On first run you may be prompted to complete a browser-based CAPTCHA. Copy the resulting session cookie into `ALEXA_COOKIE` in `.env` for future runs.

---

### 2. Google Home

**Folder:** `google_home/`

Two options — use whichever fits your setup:

#### Option A – Standalone Python daemon (no Home Assistant required)

```bash
cd google_home
pip install -r requirements.txt
cp .env.example .env      # set GOOGLE_SPEAKER_NAME and hour range
python time_announcer.py
```

Runs as a persistent daemon; wakes at `:00` every hour and plays TTS directly to the speaker over your local network.

#### Option B – Home Assistant automations

```bash
cd google_home
# Optional: set HA_ENTITY_ID, START_HOUR, END_HOUR in .env first
python generate_ha_automations.py
```

Regenerates `home_assistant_automations.yaml`. Copy its contents into your HA `automations.yaml` (or import via the UI), then replace `media_player.living_room_speaker` with your entity ID and reload automations.

---

### 3. Apple Home (HomePod / AirPlay speaker)

**Folder:** `apple_home/`

#### Step 1 – Create the "Announce the Time" Shortcut

1. Open **Shortcuts** → tap **+** → name it `Announce the Time`.
2. Add these actions in order:

   | # | Action | Setting |
   |---|--------|---------|
   | 1 | **Get Current Date** | — |
   | 2 | **Format Date** | Format `h a` → save as `HourLabel` |
   | 3 | **Format Date** | Format `H` (24-h) → save as `HourNumber` |
   | 4 | **If** `HourNumber = 0` | Text → `"Good night! It is now midnight."` → `Greeting` |
   |   | **Otherwise If** `6–11` | Text → `"Good morning! It is now [HourLabel]."` → `Greeting` |
   |   | **Otherwise If** `= 12` | Text → `"Good afternoon! It is now 12 noon."` → `Greeting` |
   |   | **Otherwise If** `13–17` | Text → `"Good afternoon! It is now [HourLabel]."` → `Greeting` |
   |   | **Otherwise If** `18–23` | Text → `"Good evening! It is now [HourLabel]."` → `Greeting` |
   | 5 | **Speak Text** | Input: `Greeting` |

   Full action spec: `apple_home/TimeAnnouncer.shortcut.json`

#### Step 2 – Generate your schedule

```bash
cd apple_home
START_HOUR=6 END_HOUR=0 node generate_schedule.js
```

This rewrites `automation_schedule.json` for your chosen range.

#### Step 3 – Create Personal Automations

For each entry in `automation_schedule.json`:

1. **Shortcuts → Automations → + → Time of Day**
2. Set the time, select **Daily** → **Next**
3. Add action: **Run Shortcut → `Announce the Time`**
4. Disable "Ask Before Running"
5. **Done**

> **Specific HomePod:** Add a **Set Playback Destination** action before **Speak Text** to pin audio to a particular HomePod.

---

## Hour Coverage (default range)

| Time | Announcement |
|------|-------------|
| 6 AM | Good morning! It is now 6 AM. |
| 7–11 AM | Good morning! It is now [X] AM. |
| 12 PM | Good afternoon! It is now 12 noon. |
| 1–5 PM | Good afternoon! It is now [X] PM. |
| 6–11 PM | Good evening! It is now [X] PM. |
| 12 AM | Good night! It is now midnight. |

---

## Notes

- **Alexa:** Routines fire in the Echo's local timezone automatically.
- **Google Home (Python):** Uses the system clock of the host machine — ensure the correct timezone is set (`timedatectl set-timezone Region/City`).
- **Apple Home:** Automations use the iPhone/iPad local time.
- To pause announcements temporarily, disable routines/automations in their apps without deleting them.
