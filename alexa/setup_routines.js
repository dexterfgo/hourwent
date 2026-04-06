/**
 * Alexa Time Announcement Routines
 * Creates one routine per hour for the configured time range.
 *
 * Setup:
 *   1. cp .env.example .env  and fill in your credentials
 *   2. npm install
 *   3. npm run setup
 *
 * On first run Alexa may require a 2FA / CAPTCHA; follow the printed URL.
 */

require('dotenv').config();
const AlexaRemote = require('alexa-remote2');

// ── Configuration ────────────────────────────────────────────────────────────
const SPEAKER_NAME   = process.env.ALEXA_SPEAKER_NAME || 'Living Room Echo';
const ALEXA_EMAIL    = process.env.ALEXA_EMAIL;
const ALEXA_PASS     = process.env.ALEXA_PASSWORD;
const ALEXA_COOKIE   = process.env.ALEXA_COOKIE || '';   // optional saved cookie
const ROUTINE_PREFIX = 'TimeAnnounce_';

// Time range: START_HOUR and END_HOUR use 24-hour values (0–23).
// END_HOUR is inclusive. Default: 6 AM to midnight (0).
// Examples:
//   START_HOUR=6  END_HOUR=23  → 6 AM – 11 PM
//   START_HOUR=8  END_HOUR=0   → 8 AM – midnight
//   START_HOUR=0  END_HOUR=23  → all 24 hours
const START_HOUR = parseInt(process.env.START_HOUR ?? '6',  10);
const END_HOUR   = parseInt(process.env.END_HOUR   ?? '0', 10);  // 0 = midnight

/**
 * Build the ordered list of hours to announce.
 * Handles wrap-around (e.g. 22 → 23 → 0).
 */
function buildHourRange(start, end) {
  const hours = [];
  let h = start;
  while (true) {
    hours.push(h);
    if (h === end) break;
    h = (h + 1) % 24;
    // Safety: never produce more than 24 entries
    if (hours.length >= 24) break;
  }
  return hours;
}

const ANNOUNCE_HOURS = buildHourRange(START_HOUR, END_HOUR);

// ── Helpers ──────────────────────────────────────────────────────────────────
function formatHour(h) {
  if (h === 0)  return { label: 'Midnight', text: "Good night! It's midnight." };
  if (h === 6)  return { label: '6_AM',     text: "Good morning! It's 6 AM." };
  if (h === 12) return { label: '12_PM',    text: "Good afternoon! It's 12 noon." };
  const period = h < 12 ? 'AM' : 'PM';
  const display = h <= 12 ? h : h - 12;
  const greeting = h < 12 ? 'Good morning' : h < 18 ? 'Good afternoon' : 'Good evening';
  return {
    label: `${display}_${period}`,
    text:  `${greeting}! It's ${display} ${period}.`
  };
}

/** Build the Alexa routine payload for a single hour */
function buildRoutinePayload(hour, deviceSerialNumber, deviceType) {
  const { label, text } = formatHour(hour);

  return {
    status: 'ENABLED',
    utcOffset: '+00:00',
    name: `${ROUTINE_PREFIX}${label}`,
    guard: null,
    trigger: {
      type: 'SCHEDULED_REGULAR',
      id: '',
      scheduledTriggerType: 'DAILY',
      recurringPattern: 'P1D',
      triggerTime: `T${String(hour).padStart(2, '0')}:00:00.000`,
    },
    sequence: {
      '@type': 'com.amazon.alexa.behaviors.model.Sequence',
      startNode: {
        '@type': 'com.amazon.alexa.behaviors.model.OpaquePayloadOperationNode',
        type: 'Alexa.speak',
        operationPayload: {
          deviceType,
          deviceSerialNumber,
          locale: 'en-US',
          customerId: '',
          textToSpeak: text,
        },
      },
    },
  };
}

// ── Main ─────────────────────────────────────────────────────────────────────
const alexa = new AlexaRemote();

alexa.init(
  {
    cookie:           ALEXA_COOKIE || undefined,
    email:            ALEXA_EMAIL,
    password:         ALEXA_PASS,
    alexaServiceHost: 'alexa.amazon.com',
    userAgent:        'Mozilla/5.0',
    acceptLanguage:   'en-US',
    amazonPage:       'amazon.com',
    logger:           console.log,
    bluetooth:        false,
    useWsMqtt:        false,
  },
  async (err) => {
    if (err) {
      console.error('[FATAL] Alexa login failed:', err.message);
      if (err.message.includes('login')) {
        console.log('→ Complete the login manually, copy the cookie from your browser,');
        console.log('  and set ALEXA_COOKIE in your .env file.');
      }
      process.exit(1);
    }

    console.log('[OK] Logged in to Alexa.');
    console.log(`[INFO] Scheduling hours: ${ANNOUNCE_HOURS.join(', ')} (${ANNOUNCE_HOURS.length} routines)`);

    const devices = await alexa.getDevices();
    const target = devices?.devices?.find(
      (d) => d.accountName.toLowerCase() === SPEAKER_NAME.toLowerCase()
    );

    if (!target) {
      console.error(`[ERROR] Speaker "${SPEAKER_NAME}" not found.`);
      console.log('Available devices:');
      devices?.devices?.forEach((d) => console.log('  •', d.accountName));
      process.exit(1);
    }

    console.log(`[OK] Found device: ${target.accountName} (${target.serialNumber})`);

    const existing = await alexa.getAutomationRoutines();
    const existingNames = new Set((existing || []).map((r) => r.name));

    let created = 0;
    let skipped = 0;

    for (const hour of ANNOUNCE_HOURS) {
      const { label } = formatHour(hour);
      const routineName = `${ROUTINE_PREFIX}${label}`;

      if (existingNames.has(routineName)) {
        console.log(`[SKIP] Routine already exists: ${routineName}`);
        skipped++;
        continue;
      }

      const payload = buildRoutinePayload(hour, target.serialNumber, target.deviceType);
      await alexa.createAutomationRoutine(payload);
      console.log(`[CREATED] ${routineName}`);
      created++;

      await new Promise((r) => setTimeout(r, 300));
    }

    console.log(`\nDone. Created: ${created}  Skipped (already exist): ${skipped}`);
    process.exit(0);
  }
);
