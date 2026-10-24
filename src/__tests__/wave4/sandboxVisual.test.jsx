import { describe, expect, it, vi, beforeEach } from 'vitest';
import { act, fireEvent, render, screen, waitFor } from '@testing-library/react';

const { loadProjectToSandbox, stopSandbox } = vi.hoisted(() => ({
  loadProjectToSandbox: vi.fn(),
  stopSandbox: vi.fn().mockResolvedValue(undefined),
}));

vi.mock('../../services/sandbox', () => ({ loadProjectToSandbox, stopSandbox }));

import SandboxPreview from '../../components/SandboxPreview';
import VisualCanvas from '../../components/VisualCanvas';

const selectedPayload = {
  component: 'GlassButton',
  domPath: 'main > section > button',
  sourceFile: '/src/components/ui/GlassButton.jsx',
  sourceLine: 42,
  tag: 'button',
  className: 'glass',
};

const dispatchSelection = () => {
  act(() => {
    window.dispatchEvent(
      new MessageEvent('message', {
        data: { type: 'LUMI_ELEMENT_SELECTED', payload: selectedPayload },
      })
    );
  });
};

beforeEach(() => {
  vi.clearAllMocks();
  stopSandbox.mockResolvedValue(undefined);
  loadProjectToSandbox.mockImplementation((runId, handlers) => {
    handlers.onTerminal?.('Installing dependencies...');
    handlers.onTerminal?.('VITE ready');
    handlers.onReady?.({ container: { url: 'https://sandbox.example.dev' } });
  });
});

describe('SandboxPreview', () => {
  it('renders the idle shell with no preview and a close action', () => {
    const onClose = vi.fn();
    const { container } = render(<SandboxPreview onClose={onClose} />);

    expect(screen.getByText('Live Sandbox')).toBeInTheDocument();
    expect(screen.getByText('idle')).toBeInTheDocument();
    expect(screen.getByText('No files loaded')).toBeInTheDocument();
    expect(screen.queryByTitle('Sandbox preview')).toBeNull();

    fireEvent.click(container.querySelector('.lucide-square').closest('button'));
    expect(onClose).toHaveBeenCalledTimes(1);
  });

  it('streams terminal output and shows the running iframe', async () => {
    render(<SandboxPreview runId="run-42" onClose={vi.fn()} />);

    expect(await screen.findByTitle('Sandbox preview')).toHaveAttribute(
      'src',
      'https://sandbox.example.dev'
    );
    expect(screen.getByText('running')).toBeInTheDocument();
    expect(screen.getByText('Installing dependencies...')).toBeInTheDocument();
    expect(screen.getByText('VITE ready')).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Open in new tab' })).toHaveAttribute(
      'href',
      'https://sandbox.example.dev'
    );
    expect(loadProjectToSandbox).toHaveBeenCalledWith('run-42', expect.any(Object));
  });

  it('reports sandbox failures in the terminal and badge', async () => {
    loadProjectToSandbox.mockImplementation((runId, handlers) => {
      handlers.onError?.('WebContainer unavailable');
    });

    render(<SandboxPreview runId="run-7" onClose={vi.fn()} />);

    expect(await screen.findByText(/WebContainer unavailable/)).toBeInTheDocument();
    expect(screen.getByText('error')).toBeInTheDocument();
  });

  it('tears the sandbox down on unmount', () => {
    const { unmount } = render(<SandboxPreview runId="run-1" onClose={vi.fn()} />);

    unmount();

    expect(stopSandbox).toHaveBeenCalledTimes(1);
  });
});

describe('VisualCanvas', () => {
  it('renders the empty canvas and toggles inspector mode', () => {
    render(<VisualCanvas />);

    expect(screen.getByText('Visual Canvas')).toBeInTheDocument();
    expect(
      screen.getByText('Generate a project to see the live canvas')
    ).toBeInTheDocument();
    expect(screen.getByTitle('Toggle element inspector')).toBeInTheDocument();

    fireEvent.click(screen.getByTitle('Toggle element inspector'));
    expect(screen.getByText('Inspecting')).toBeInTheDocument();

    fireEvent.click(screen.getByTitle('Toggle element inspector'));
    expect(screen.queryByText('Inspecting')).toBeNull();
  });

  it('shows selected element metadata and submits an edit prompt', () => {
    const onPromptSubmit = vi.fn();
    render(
      <VisualCanvas
        previewUrl="https://preview.example.dev"
        onPromptSubmit={onPromptSubmit}
      />
    );

    expect(screen.getByTitle('Visual Canvas Preview')).toHaveAttribute(
      'src',
      'https://preview.example.dev'
    );

    dispatchSelection();

    expect(screen.getByText('GlassButton')).toBeInTheDocument();
    expect(screen.getByText('GlassButton.jsx:42')).toBeInTheDocument();
    expect(screen.getByText(/Edit selected: GlassButton/)).toBeInTheDocument();

    const send = screen.getByRole('button', { name: 'Send' });
    expect(send).toBeDisabled();

    fireEvent.change(screen.getByPlaceholderText(/change the background/), {
      target: { value: 'make it bigger' },
    });
    fireEvent.click(send);

    expect(onPromptSubmit).toHaveBeenCalledWith({
      prompt: 'make it bigger',
      element: selectedPayload,
    });
    expect(screen.getByPlaceholderText(/change the background/)).toHaveValue('');
  });

  it('submits with Ctrl+Enter and clears everything with Escape', () => {
    const onPromptSubmit = vi.fn();
    render(<VisualCanvas previewUrl="/preview" onPromptSubmit={onPromptSubmit} />);

    dispatchSelection();
    const input = screen.getByPlaceholderText(/change the background/);

    fireEvent.change(input, { target: { value: 'add an animation' } });
    fireEvent.keyDown(input, { key: 'Enter', ctrlKey: true });

    expect(onPromptSubmit).toHaveBeenCalledWith({
      prompt: 'add an animation',
      element: selectedPayload,
    });

    dispatchSelection();
    fireEvent.keyDown(screen.getByPlaceholderText(/change the background/), {
      key: 'Escape',
    });

    expect(screen.queryByText('GlassButton')).toBeNull();
    expect(screen.queryByText(/Edit selected/)).toBeNull();
  });

  it('ignores empty prompts and respects the send disabled state', async () => {
    const onPromptSubmit = vi.fn();
    render(<VisualCanvas previewUrl="/preview" onPromptSubmit={onPromptSubmit} />);

    dispatchSelection();
    const send = screen.getByRole('button', { name: 'Send' });

    fireEvent.change(screen.getByPlaceholderText(/change the background/), {
      target: { value: '   ' },
    });
    await waitFor(() => expect(send).toBeDisabled());
    fireEvent.click(send);

    expect(onPromptSubmit).not.toHaveBeenCalled();
  });
});
