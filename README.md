# Smart Speaker – Hourly Time Announcements

Announces the current time every hour from **6:00 AM to 12:00 midnight** on a designated speaker. All three major platforms are covered.

---

## Platform Quick-Start

### 1. Amazon Alexa

**Folder:** `alexa/`

**Requirements:** Node.js 18+, an Amazon account, an Echo speaker.

```bash
cd alexa
cp .env.example .env      # edit with your Amazon credentials & speaker name
npm install
npm run setup
```

- Creates **19 daily routines** in your Alexa account (one per hour, 6 AM – midnight).
- On first run you may be prompted to complete a browser-based CAPTCHA/2FA login.  Copy the resulting session cookie into `ALEXA_COOKIE` in `.env` for future runs.
- The target speaker is set via `ALEXA_SPEAKER_NAME` (exact name from the Alexa app).

---

### 2. Google Home

**Folder:** `google_home/`

Two approaches are provided — use whichever fits your setup:

#### Option A – Standalone Python daemon (no Home Assistant required)

```bash
cd google_home
pip install -r requirements.txt
cp .env.example .env      # set GOOGLE_SPEAKER_NAME to match your Google Home app
python time_announcer.py
```

Keep the script running (e.g. via `screen`, `tmux`, or a systemd service). It wakes up at the top of every hour and plays a TTS announcement on your speaker.

#### Option B – Home Assistant automation (recommended for HA users)

1. Copy `home_assistant_automations.yaml` contents into your HA `automations.yaml` (or add via the UI).
2. Replace `media_player.living_room_speaker` with your actual entity ID.
3. Reload automations (`Developer Tools → YAML → Automations`).

---

### 3. Apple Home (HomePod / AirPlay speaker)

**Folder:** `apple_home/`

Apple Shortcuts doesn't support bulk import of automations; you set them up once in the app.

#### Step 1 – Create the "Announce the Time" Shortcut

1. Open **Shortcuts** → tap **+** (new shortcut) → name it `Announce the Time`.
2. Add these actions in order:
   | # | Action | Setting |
   |---|--------|---------|
   | 1 | **Get Current Date** | — |
   | 2 | **Format Date** | Format: `h a` → save as `HourLabel` |
   | 3 | **Format Date** | Format: `H` (24-hour) → save as `HourNumber` |
   | 4 | **If** (HourNumber = 0) | Text: `"Good night! It is now midnight."` → `Greeting` |
   |   | **Otherwise If** (6–11) | Text: `"Good morning! It is now [HourLabel]."` → `Greeting` |
   |   | **Otherwise If** (= 12) | Text: `"Good afternoon! It is now 12 noon."` → `Greeting` |
   |   | **Otherwise If** (13–17) | Text: `"Good afternoon! It is now [HourLabel]."` → `Greeting` |
   |   | **Otherwise If** (18–23) | Text: `"Good evening! It is now [HourLabel]."` → `Greeting` |
   | 5 | **Speak Text** | Input: `Greeting` |

   See `TimeAnnouncer.shortcut.json` for the full action spec.

#### Step 2 – Create 19 Personal Automations

For each time listed in `automation_schedule.json`:

1. **Shortcuts** → **Automations** → **+** → **Time of Day**
2. Set the time, select **Daily**, tap **Next**
3. Add action: **Run Shortcut** → `Announce the Time`
4. Disable "Ask Before Running" so it fires silently
5. Tap **Done**

> **Speaker routing:** When the automation fires, Siri speaks through your default HomePod or AirPlay speaker. To route to a specific HomePod, add a **Set Playback Destination** action before **Speak Text**.

---

## Hour Coverage (all platforms)

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

- **Alexa:** Routines fire in the device's local timezone automatically.
- **Google Home (Python):** The daemon uses the system clock of the machine running it — ensure that machine's timezone is set correctly.
- **Apple Home:** Automations use iPhone/iPad local time.
- To silence announcements temporarily: disable the routines/automations in their respective apps without deleting them.
