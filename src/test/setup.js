import React from 'react';
import { vi } from 'vitest';
import i18n from '../i18n';

i18n.changeLanguage('en');

globalThis.IntersectionObserver = class IntersectionObserver {
  constructor(callback) {
    this.callback = callback;
  }

  observe() {
    this.callback([{ isIntersecting: true }], this);
  }

  unobserve() {}
  disconnect() {}
  takeRecords() {
    return [];
  }
  root = null;
  rootMargin = '';
  thresholds = [];
};

vi.mock('@react-three/fiber', () => ({
  Canvas: ({ children }) => React.createElement('div', { 'data-testid': 'scene-canvas' }, children),
  useFrame: () => {},
}));
