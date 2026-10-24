import { act, renderHook, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

const licenseAPI = vi.hoisted(() => ({ validate: vi.fn() }));

vi.mock('../../services/api', () => ({ licenseAPI }));

import useLicense from '../../hooks/useLicense';

beforeEach(() => {
  localStorage.clear();
  licenseAPI.validate.mockReset();
});

afterEach(() => {
  vi.restoreAllMocks();
});

describe('useLicense', () => {
  it('loads immediately with trial state when no key is stored', async () => {
    const { result } = renderHook(() => useLicense());

    await waitFor(() => expect(result.current.loaded).toBe(true));
    expect(result.current).toMatchObject({
      valid: false,
      status: 'no_key',
      trial: true,
      daysLeft: 0,
    });
    expect(licenseAPI.validate).not.toHaveBeenCalled();
  });

  it('validates a stored key and records activation', async () => {
    localStorage.setItem('lmc_license_key', 'LMC-STORED');
    licenseAPI.validate.mockResolvedValue({ data: { success: true, data: { valid: true } } });

    const { result } = renderHook(() => useLicense());

    await waitFor(() => expect(result.current.valid).toBe(true));
    expect(licenseAPI.validate).toHaveBeenCalledWith('LMC-STORED');
    expect(result.current).toMatchObject({ status: 'active', trial: false, loaded: true });
    expect(localStorage.getItem('lmc_license_key')).toBe('LMC-STORED');
    // Written on a macrotask so the UI can paint the activated state first.
    await waitFor(() => expect(localStorage.getItem('LICENSE_ACTIVATED')).toBe('1'));
  });

  it('reports an invalid key with the server status and clears activation', async () => {
    localStorage.setItem('lmc_license_key', 'LMC-OLD');
    localStorage.setItem('LICENSE_ACTIVATED', '1');
    licenseAPI.validate.mockResolvedValue({
      data: { success: true, data: { valid: false, status: 'expired', daysLeft: 3 } },
    });

    const { result } = renderHook(() => useLicense());

    await waitFor(() => expect(result.current.loaded).toBe(true));
    expect(result.current).toMatchObject({
      valid: false,
      status: 'expired',
      trial: true,
      daysLeft: 3,
    });
    expect(localStorage.getItem('LICENSE_ACTIVATED')).toBeNull();
  });

  it('falls back to offline trial state when the API is unreachable', async () => {
    localStorage.setItem('lmc_license_key', 'LMC-STORED');
    licenseAPI.validate.mockRejectedValue(new Error('network down'));

    const { result } = renderHook(() => useLicense());

    await waitFor(() => expect(result.current.loaded).toBe(true));
    expect(result.current).toMatchObject({
      valid: false,
      status: 'offline',
      trial: true,
      daysLeft: 0,
    });
  });

  it('activates a key entered in the UI', async () => {
    licenseAPI.validate.mockResolvedValue({ data: { success: true, data: { valid: true } } });

    const { result } = renderHook(() => useLicense());
    await waitFor(() => expect(result.current.loaded).toBe(true));

    let outcome;
    await act(async () => {
      outcome = await result.current.activate('LMC-NEW');
    });

    expect(outcome).toEqual({ valid: true });
    expect(licenseAPI.validate).toHaveBeenCalledWith('LMC-NEW');
    expect(localStorage.getItem('lmc_license_key')).toBe('LMC-NEW');
    expect(result.current.status).toBe('active');
  });
});
