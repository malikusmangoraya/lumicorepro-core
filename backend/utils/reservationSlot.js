/**
 * Reservation slot math — one place where a wall-clock date/time becomes an
 * unambiguous instant.
 *
 * A restaurant table is booked with a calendar date and a local clock time. The
 * only value that can be compared, sorted or checked for overlap is the UTC
 * instant those two mean in the restaurant's own timezone; a bare
 * `new Date('YYYY-MM-DDTHH:mm')` instead resolves to whatever zone the Node
 * process happens to run in, so the same request means different instants on
 * different deployments.
 */

const MINUTE_MS = 60_000;

/** 24-hour `HH:MM` only — `'25:70'` and `'9pm'` are not slots. */
export const TIME_PATTERN = /^([01]\d|2[0-3]):[0-5]\d$/;

/**
 * Calendar date `YYYY-MM-DD` that actually exists. A round trip through
 * `Date.UTC` is the only honest check: JS date parsing rolls `2027-02-30` over to
 * 2 March instead of rejecting it, which would book a table on a day nobody named.
 */
export function isValidDate(value) {
  const match = /^(\d{4})-(\d{2})-(\d{2})$/.exec(String(value || ''));
  if (!match) return false;
  const [year, month, day] = match.slice(1).map(Number);
  if (year < 1000 || month < 1 || month > 12 || day < 1) return false;
  const probe = new Date(Date.UTC(year, month - 1, day));
  return probe.getUTCFullYear() === year && probe.getUTCMonth() === month - 1 && probe.getUTCDate() === day;
}

export function isValidTime(value) {
  return TIME_PATTERN.test(String(value || ''));
}

/** Offset (minutes east of UTC) of `timeZone` at the given UTC instant. */
function zoneOffsetMinutes(utcDate, timeZone) {
  const parts = new Intl.DateTimeFormat('en-US', {
    timeZone,
    hour12: false,
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  }).formatToParts(utcDate);
  const at = (type) => Number(parts.find((p) => p.type === type)?.value || 0);
  const asUtc = Date.UTC(at('year'), at('month') - 1, at('day'), at('hour') % 24, at('minute'), at('second'));
  return Math.round((asUtc - utcDate.getTime()) / MINUTE_MS);
}

/**
 * Wall-clock `YYYY-MM-DD` + `HH:MM` in `timeZone` → UTC Date.
 * Iterates the offset twice so a slot that straddles a DST change still lands on
 * a real instant; ambiguous fall-back hours resolve to the earlier of the two.
 */
export function slotInstant({ date, time, timeZone }) {
  if (!isValidDate(date) || !isValidTime(time)) return null;
  const wallMs = Date.parse(`${date}T${time}:00.000Z`);
  if (Number.isNaN(wallMs)) return null;
  let guess = wallMs - zoneOffsetMinutes(new Date(wallMs), timeZone) * MINUTE_MS;
  for (let i = 0; i < 2; i += 1) {
    const next = wallMs - zoneOffsetMinutes(new Date(guess), timeZone) * MINUTE_MS;
    if (next === guess) break;
    guess = next;
  }
  return new Date(guess);
}

export function slotEnd(startAt, durationMinutes) {
  return new Date(startAt.getTime() + Math.max(1, Number(durationMinutes) || 0) * MINUTE_MS);
}

/** Half-open overlap: two slots that only touch at an endpoint do not collide. */
export function overlaps(startA, endA, startB, endB) {
  return startA.getTime() < endB.getTime() && startB.getTime() < endA.getTime();
}

export const isPastSlot = (startAt, now = new Date()) => startAt.getTime() < now.getTime();
