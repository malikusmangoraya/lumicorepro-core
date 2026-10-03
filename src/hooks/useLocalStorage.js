import { useCallback, useEffect, useRef, useState } from 'react';
import { getStorage } from '../utils/helpers';

function getInitialValue(value) {
  return typeof value === 'function' ? value() : value;
}

function readValue(key, initialValue) {
  return getStorage(key, getInitialValue(initialValue));
}

/**
 * Persist a state value in localStorage and synchronize it across browser tabs.
 * @template T
 * @param {string} key Storage key.
 * @param {T | (() => T)} initialValue Value or lazy initializer used when no value is stored.
 * @returns {[T, (value: T | ((currentValue: T) => T)) => void, () => void]}
 *   Current value, setter, and remove function.
 */
export default function useLocalStorage(key, initialValue) {
  const [fallbackValue] = useState(() => getInitialValue(initialValue));
  const [storedValue, setStoredValue] = useState(() => readValue(key, fallbackValue));
  const storedValueRef = useRef(storedValue);

  useEffect(() => {
    const value = readValue(key, fallbackValue);
    storedValueRef.current = value;
    setStoredValue(value);
  }, [fallbackValue, key]);

  useEffect(() => {
    const handleStorage = (event) => {
      if (event.storageArea && event.storageArea !== window.localStorage) return;
      if (event.key !== key && event.key !== null) return;

      const value = event.key === null ? fallbackValue : readValue(key, fallbackValue);
      storedValueRef.current = value;
      setStoredValue(value);
    };

    window.addEventListener('storage', handleStorage);
    return () => window.removeEventListener('storage', handleStorage);
  }, [fallbackValue, key]);

  const setValue = useCallback(
    (value) => {
      const nextValue = typeof value === 'function' ? value(storedValueRef.current) : value;

      try {
        const serialized = JSON.stringify(nextValue);
        if (serialized === undefined) {
          throw new TypeError('Value cannot be serialized to JSON');
        }
        window.localStorage.setItem(key, serialized);
      } catch (error) {
        throw new Error(`Unable to save localStorage key "${key}"`, { cause: error });
      }

      storedValueRef.current = nextValue;
      setStoredValue(nextValue);
    },
    [key]
  );

  const removeValue = useCallback(() => {
    try {
      window.localStorage.removeItem(key);
    } catch (error) {
      throw new Error(`Unable to remove localStorage key "${key}"`, { cause: error });
    }

    storedValueRef.current = fallbackValue;
    setStoredValue(fallbackValue);
  }, [fallbackValue, key]);

  return [storedValue, setValue, removeValue];
}
