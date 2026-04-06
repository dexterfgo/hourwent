/**
 * Apple Home Schedule Generator
 * Rebuilds automation_schedule.json for any START_HOUR / END_HOUR.
 *
 * Usage:
 *   node generate_schedule.js
 *   START_HOUR=8 END_HOUR=22 node generate_schedule.js
 */

const fs   = require('fs');
const path = require('path');

const START_HOUR = parseInt(process.env.START_HOUR ?? '6',  10);
const END_HOUR   = parseInt(process.env.END_HOUR   ?? '0', 10);   // 0 = midnight

function buildHourRange(start, end) {
  const hours = [];
  let h = start;
  while (true) {
    hours.push(h);
    if (h === end) break;
    h = (h + 1) % 24;
    if (hours.length >= 24) break;
  }
  return hours;
}

const hours = buildHourRange(START_HOUR, END_HOUR);

const automations = hours.map((h) => ({
  time:     `${String(h).padStart(2, '0')}:00`,
  shortcut: 'Announce the Time',
  repeat:   'Daily',
}));

const output = {
  _comment: [
    'Each entry is one Personal Automation in the Shortcuts app.',
    'Shortcuts → Automations → + → Time of Day → set time → Run Shortcut → "Announce the Time".',
    'Re-generate: node generate_schedule.js  (or set START_HOUR / END_HOUR env vars)',
  ],
  config: {
    start_hour: START_HOUR,
    end_hour:   END_HOUR,
    _note: 'Both values are 24-hour (0–23). end_hour 0 = midnight.',
  },
  automations,
};

const outPath = path.join(__dirname, 'automation_schedule.json');
fs.writeFileSync(outPath, JSON.stringify(output, null, 2) + '\n');
console.log(`Written ${automations.length} automation slots to ${outPath}`);
console.log(`Hours: ${hours.join(', ')}`);
