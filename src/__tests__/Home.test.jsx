import React from 'react';
import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import Home from '../pages/Home';

describe('Home page', () => {
  it('renders the core hero content', () => {
    render(
      <MemoryRouter>
        <Home />
      </MemoryRouter>
    );

    expect(screen.getByText(/Build Any Website/i)).toBeTruthy();
    expect(screen.getByText(/Generate Website Free/i)).toBeTruthy();
  });
});
