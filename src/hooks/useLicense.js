import React, { useCallback, useEffect, useState } from 'react';
import { licenseAPI } from '../services/api';

/**
 * useLicense — client-side license state (free, self-hosted).
 *
 * Reads the license key from localStorage and validates it through the
 * backend once per session. Unknown/offline states are treated as
 * "trial-like" so the platform never hard-blocks new users.
 *
 * Holds the LICENSE_ACTIVATED key so manual entry is remembered.
 */
export default function useLicense() {
  const [state, setState] = useState({
    loaded: false,
    valid: false,
    status: 'no_key',
    trial: true,
    daysLeft: 0,
  });

  const validate = useCallback(async (key) => {
    try {
      const { data } = await licenseAPI.validate(key);
      if (data?.success && data.data?.valid) {
        localStorage.setItem('lmc_license_key', key);
        setTimeout(() => localStorage.setItem('LICENSE_ACTIVATED', '1'), 0);
        setState({
          loaded: true,
          valid: true,
          status: 'active',
          trial: false,
          daysLeft: 0,
        });
        return { valid: true };
      }
      localStorage.removeItem('LICENSE_ACTIVATED');
      setState({
        loaded: true,
        valid: false,
        status: data?.data?.status || 'invalid',
        trial: true,
        daysLeft: data?.data?.daysLeft || 0,
      });
      return { valid: false };
    } catch (e) {
      // Offline / unconfigured — do not block the user.
      setState({ loaded: true, valid: false, status: 'offline', trial: true, daysLeft: 0 });
      return { valid: false };
    }
  }, []);

  useEffect(() => {
    const key = localStorage.getItem('lmc_license_key');
    if (key) {
      validate(key);
    } else {
      setState((s) => ({ ...s, loaded: true }));
    }
  }, [validate]);

  const activate = useCallback(
    (key) => validate(key),
    [validate]
  );

  return { ...state, activate };
}