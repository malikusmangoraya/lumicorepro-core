import { describe, it, expect, vi, afterEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import Modal from '../../components/ui/Modal';

afterEach(() => {
  document.body.style.overflow = '';
  vi.restoreAllMocks();
});

describe('Modal', () => {
  it('renders nothing while closed', () => {
    render(
      <Modal open={false} title="Hidden">
        Body
      </Modal>
    );
    expect(screen.queryByRole('dialog')).toBeNull();
  });

  it('exposes a labelled, modal dialog with size classes and footer content', () => {
    const { container } = render(
      <Modal
        open
        onClose={() => {}}
        title="Confirm delete"
        description="This cannot be undone."
        size="sm"
        footer={<button type="button">Confirm</button>}
      >
        <p>Project 42 will be removed.</p>
      </Modal>
    );

    const dialog = screen.getByRole('dialog', { name: 'Confirm delete' });
    expect(dialog).toHaveAttribute('aria-modal', 'true');
    expect(dialog).toHaveAccessibleDescription('This cannot be undone.');
    expect(screen.getByText('Project 42 will be removed.')).toBeTruthy();
    expect(screen.getByRole('button', { name: 'Confirm' })).toBeTruthy();

    const panel = container.querySelector('.max-w-sm');
    expect(panel).not.toBeNull();
  });

  it('closes on Escape and restores body scrolling once the parent closes it', async () => {
    const onClose = vi.fn();
    const onOpenChange = vi.fn();
    const { rerender } = render(
      <Modal open onClose={onClose} onOpenChange={onOpenChange} title="Escapable">
        Body
      </Modal>
    );

    expect(document.body.style.overflow).toBe('hidden');
    fireEvent.keyDown(document, { key: 'Escape' });

    expect(onClose).toHaveBeenCalledTimes(1);
    expect(onOpenChange).toHaveBeenCalledWith(false);

    rerender(
      <Modal open={false} onClose={onClose} onOpenChange={onOpenChange} title="Escapable">
        Body
      </Modal>
    );
    await waitFor(() => {
      expect(screen.queryByRole('dialog')).toBeNull();
      expect(document.body.style.overflow).toBe('');
    });
  });

  it('honours closeOnEscape={false}', () => {
    const onClose = vi.fn();
    render(
      <Modal open onClose={onClose} closeOnEscape={false} title="Sticky">
        Body
      </Modal>
    );

    fireEvent.keyDown(document, { key: 'Escape' });
    expect(onClose).not.toHaveBeenCalled();
    expect(screen.getByRole('dialog')).toBeTruthy();
  });

  it('closes on backdrop click but not on content click', () => {
    const onClose = vi.fn();
    render(
      <Modal open onClose={onClose} title="Backdrop">
        <p>Inner content</p>
      </Modal>
    );

    const dialog = screen.getByRole('dialog');
    fireEvent.click(screen.getByText('Inner content'));
    expect(onClose).not.toHaveBeenCalled();

    fireEvent.click(dialog);
    expect(onClose).toHaveBeenCalledTimes(1);
  });

  it('closes from the labelled close button and can hide it', () => {
    const onClose = vi.fn();
    const { unmount } = render(
      <Modal open onClose={onClose} title="Closable">
        Body
      </Modal>
    );

    fireEvent.click(screen.getByRole('button', { name: 'Close modal' }));
    expect(onClose).toHaveBeenCalledTimes(1);
    unmount();

    render(
      <Modal open onClose={onClose} title="No close" showCloseButton={false}>
        Body
      </Modal>
    );
    expect(screen.queryByRole('button', { name: 'Close modal' })).toBeNull();
  });
});
