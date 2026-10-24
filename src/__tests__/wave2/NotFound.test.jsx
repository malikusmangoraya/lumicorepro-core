import { describe, expect, it } from 'vitest';
import { fireEvent, render, screen } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import NotFoundPage from '../../pages/NotFound';

const renderNotFound = () =>
  render(
    <MemoryRouter initialEntries={['/missing-page']}>
      <Routes>
        <Route path="/" element={<div>home-page</div>} />
        <Route path="/templates" element={<div>templates-page</div>} />
        <Route path="/generate" element={<div>generate-page</div>} />
        <Route path="*" element={<NotFoundPage />} />
      </Routes>
    </MemoryRouter>
  );

describe('NotFound page', () => {
  it('renders the 404 message and recovery copy', () => {
    renderNotFound();

    expect(screen.getByText('404')).toBeTruthy();
    expect(screen.getByRole('heading', { level: 1, name: 'Page not found' })).toBeTruthy();
    expect(screen.getByText(/doesn't exist or has been moved/)).toBeTruthy();
  });

  it('sets a noindex SEO title for unknown routes', () => {
    renderNotFound();

    expect(document.title).toBe('Page Not Found — LumicorePro');
    expect(document.querySelector('meta[name="description"]').getAttribute('content')).toBe(
      'The page you are looking for does not exist.'
    );
    expect(document.querySelector('meta[name="robots"]').getAttribute('content')).toBe(
      'noindex,nofollow'
    );
  });

  it('shows the popular-page quick links', () => {
    renderNotFound();

    expect(screen.getByText('Popular Pages')).toBeTruthy();
    expect(screen.getByRole('button', { name: /60 Templates/ })).toBeTruthy();
    expect(screen.getByRole('button', { name: /AI Generator/ })).toBeTruthy();
    expect(screen.getByRole('button', { name: /Restaurant/ })).toBeTruthy();
  });

  it('navigates back to the home page', () => {
    renderNotFound();

    fireEvent.click(screen.getByRole('button', { name: /back to home/i }));

    expect(screen.getByText('home-page')).toBeTruthy();
  });

  it('navigates to the template gallery and a quick link', () => {
    renderNotFound();

    fireEvent.click(screen.getByRole('button', { name: /browse templates/i }));

    expect(screen.getByText('templates-page')).toBeTruthy();
  });

  it('navigates through popular page quick links', () => {
    renderNotFound();

    fireEvent.click(screen.getByRole('button', { name: /AI Generator/ }));

    expect(screen.getByText('generate-page')).toBeTruthy();
  });
});
