/**
 * Unit tests — utils/reservationSlot.js
 *
 * The restaurant vertical books a table with a calendar date plus a local clock
 * time. Everything that decides whether two requests collide (and whether a
 * request is already in the past) depends on turning those two strings into one
 * comparable instant, so that math is tested on its own — including across a DST
 * boundary, where the naive `new Date(`${date}T${time}`)` silently shifts by an
 * hour depending on the machine's zone.
 */
import { describe, it, expect } from '@jest/globals';
import {
  TIME_PATTERN,
  isValidDate,
  isValidTime,
  isPastSlot,
  overlaps,
  slotEnd,
  slotInstant,
} from '../../utils/reservationSlot.js';

describe('isValidTime', () => {
  it.each(['00:00', '09:30', '19:00', '23:59'])('accepts the 24-hour slot %s', (time) => {
    expect(isValidTime(time)).toBe(true);
  });

  it.each(['25:70', '9:00', '24:00', '19:60', '9pm', '', '19-00', '1900'])('rejects %s', (time) => {
    expect(isValidTime(time)).toBe(false);
  });

  it.each([null, undefined, 1900])('rejects the non-string %p', (time) => {
    expect(isValidTime(time)).toBe(false);
  });

  it('is the same pattern the route validates with', () => {
    expect(TIME_PATTERN.source).toBe('^([01]\\d|2[0-3]):[0-5]\\d$');
  });
});

describe('isValidDate', () => {
  it('accepts a real calendar date', () => {
    expect(isValidDate('2027-02-28')).toBe(true);
    expect(isValidDate('2028-02-29')).toBe(true); // leap year
  });

  it.each(['2027-02-30', '2027-13-01', '01/06/2027', '2027-6-1', '', null])(
    'rejects %s instead of rolling it over',
    (date) => {
      expect(isValidDate(date)).toBe(false);
    }
  );
});

describe('slotInstant', () => {
  it('reads the wall clock in the venue zone, not the process zone', () => {
    // Asia/Karachi is UTC+5 all year (no DST), so the arithmetic is a constant.
    const slot = slotInstant({ date: '2027-06-01', time: '19:00', timeZone: 'Asia/Karachi' });
    expect(slot.toISOString()).toBe('2027-06-01T14:00:00.000Z');
  });

  it('returns the same instant as UTC when the venue is UTC', () => {
    const slot = slotInstant({ date: '2027-06-01', time: '19:00', timeZone: 'UTC' });
    expect(slot.toISOString()).toBe('2027-06-01T19:00:00.000Z');
  });

  it('applies the daylight-saving offset for the date asked about', () => {
    // New York is UTC-5 in January and UTC-4 in June — a fixed offset would be
    // wrong for one of these two slots.
    expect(slotInstant({ date: '2027-01-15', time: '12:00', timeZone: 'America/New_York' }).toISOString()).toBe(
      '2027-01-15T17:00:00.000Z'
    );
    expect(slotInstant({ date: '2027-06-15', time: '12:00', timeZone: 'America/New_York' }).toISOString()).toBe(
      '2027-06-15T16:00:00.000Z'
    );
  });

  it('answers null for a slot that cannot exist', () => {
    expect(slotInstant({ date: '2027-02-30', time: '19:00', timeZone: 'UTC' })).toBeNull();
    expect(slotInstant({ date: '2027-06-01', time: '25:00', timeZone: 'UTC' })).toBeNull();
  });

  it('is idempotent across a DST transition hour', () => {
    // 02:30 does not exist on the spring-forward day; the slot still resolves to
    // a single instant rather than NaN, so the route can reject or accept it.
    const slot = slotInstant({ date: '2027-03-14', time: '02:30', timeZone: 'America/New_York' });
    expect(slot).toBeInstanceOf(Date);
    expect(Number.isNaN(slot.getTime())).toBe(false);
    expect(slotInstant({ date: '2027-03-14', time: '02:30', timeZone: 'America/New_York' }).getTime()).toBe(slot.getTime());
  });
});

describe('slotEnd', () => {
  it('adds the seating duration in minutes', () => {
    const start = new Date('2027-06-01T19:00:00Z');
    expect(slotEnd(start, 120).toISOString()).toBe('2027-06-01T21:00:00.000Z');
  });

  it('never yields a zero-length slot', () => {
    const start = new Date('2027-06-01T19:00:00Z');
    expect(slotEnd(start, 0).getTime()).toBe(start.getTime() + 60_000);
    expect(slotEnd(start, 'lots').getTime()).toBe(start.getTime() + 60_000);
  });
});

describe('overlaps', () => {
  const at = (time) => new Date(`2027-06-01T${time}:00Z`);

  it('detects a partial overlap in either direction', () => {
    expect(overlaps(at('19:00'), at('21:00'), at('20:00'), at('22:00'))).toBe(true);
    expect(overlaps(at('20:00'), at('22:00'), at('19:00'), at('21:00'))).toBe(true);
  });

  it('treats back-to-back seatings as free', () => {
    expect(overlaps(at('19:00'), at('21:00'), at('21:00'), at('23:00'))).toBe(false);
    expect(overlaps(at('21:00'), at('23:00'), at('19:00'), at('21:00'))).toBe(false);
  });

  it('catches a fully contained slot', () => {
    expect(overlaps(at('19:00'), at('23:00'), at('20:00'), at('21:00'))).toBe(true);
  });
});

describe('isPastSlot', () => {
  it('flags a slot before now', () => {
    expect(isPastSlot(new Date('2020-01-01T19:00:00Z'))).toBe(true);
  });

  it('keeps a future slot bookable, and takes the clock as a seam', () => {
    const now = new Date('2027-06-01T18:00:00Z');
    expect(isPastSlot(new Date('2027-06-01T19:00:00Z'), now)).toBe(false);
    expect(isPastSlot(new Date('2027-06-01T17:59:00Z'), now)).toBe(true);
  });
});
