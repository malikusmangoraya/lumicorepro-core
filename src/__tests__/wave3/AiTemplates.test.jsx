import { act, fireEvent, render, screen } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { MemoryRouter } from 'react-router-dom';
import ChatInterface from '../../templates/ai/ChatInterface/ChatInterface';
import AIGenerator from '../../templates/ai/AIGenerator/AIGenerator';
import UsageDashboard from '../../templates/ai/UsageDashboard/UsageDashboard';
import ModelSelection from '../../templates/ai/ModelSelection/ModelSelection';
import GenerationHistory from '../../templates/ai/GenerationHistory/GenerationHistory';

/** AI template pages render local mock data and need only a router. */
function renderTemplate(ui) {
  return render(<MemoryRouter>{ui}</MemoryRouter>);
}

afterEach(() => {
  vi.useRealTimers();
});

describe('ChatInterface template', () => {
  it('renders the header, seeded conversation, and model status', () => {
    renderTemplate(<ChatInterface />);

    expect(screen.getByRole('heading', { level: 1, name: 'AI Chat Interface' })).toBeInTheDocument();
    expect(screen.getByText('Lumicore AI')).toBeInTheDocument();
    expect(screen.getByText('Powered by gpt-4')).toBeInTheDocument();
    expect(
      screen.getByText('Hi — I am Lumicore AI. How can I help you today?')
    ).toBeInTheDocument();
    expect(screen.getByPlaceholderText(/Message Lumicore AI/)).toBeInTheDocument();
  });

  it('sends a message and receives the simulated reply', async () => {
    vi.useFakeTimers();
    renderTemplate(<ChatInterface />);

    const send = screen.getByRole('button', { name: 'Send message' });
    expect(send).toBeDisabled();

    fireEvent.change(screen.getByPlaceholderText(/Message Lumicore AI/), {
      target: { value: 'Summarise our roadmap' },
    });
    expect(send).toBeEnabled();
    fireEvent.click(send);

    expect(screen.getByText('Summarise our roadmap')).toBeInTheDocument();
    expect(screen.getByText(/Lumicore is thinking/)).toBeInTheDocument();

    await act(async () => {
      await vi.advanceTimersByTimeAsync(950);
    });

    expect(screen.getByText(/Got it\. Here is a clear, concise answer/)).toBeInTheDocument();
    expect(screen.queryByText(/Lumicore is thinking/)).toBeNull();
  });

  it('switches the active model from the model selector', () => {
    renderTemplate(<ChatInterface />);

    fireEvent.click(screen.getByRole('button', { name: 'gpt-4' }));
    fireEvent.click(screen.getByRole('button', { name: /GPT-4o/ }));

    expect(screen.getByText('Powered by gpt-4o')).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: /GPT-4o/ })).toBeNull();
  });

  it('clears the conversation back to the seed messages with New Chat', async () => {
    vi.useFakeTimers();
    renderTemplate(<ChatInterface />);

    fireEvent.change(screen.getByPlaceholderText(/Message Lumicore AI/), {
      target: { value: 'Temporary prompt' },
    });
    fireEvent.click(screen.getByRole('button', { name: 'Send message' }));
    expect(screen.getByText('Temporary prompt')).toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: 'New Chat' }));

    expect(screen.queryByText('Temporary prompt')).toBeNull();
    expect(
      screen.getByText('Hi — I am Lumicore AI. How can I help you today?')
    ).toBeInTheDocument();
  });
});

describe('AIGenerator template', () => {
  it('renders the prompt form, model choices, and empty output state', () => {
    renderTemplate(<AIGenerator />);

    expect(screen.getByRole('heading', { level: 1, name: 'AI Generator' })).toBeInTheDocument();
    expect(screen.getByText('Your generation will appear here.')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Copy' })).toBeDisabled();
    for (const model of ['Lumi Fast', 'Lumi Pro', 'Lumi Reason']) {
      expect(screen.getByRole('button', { name: model })).toBeInTheDocument();
    }
  });

  it('generates output for the prompt with the selected model', async () => {
    vi.useFakeTimers();
    renderTemplate(<AIGenerator />);

    fireEvent.click(screen.getByRole('button', { name: 'Lumi Pro' }));
    fireEvent.change(screen.getByLabelText(/Prompt/), {
      target: { value: 'Draft a launch email' },
    });

    fireEvent.click(screen.getByRole('button', { name: 'Generate' }));
    expect(screen.getByRole('button', { name: 'Generate' })).toHaveAttribute('aria-busy', 'true');

    await act(async () => {
      await vi.advanceTimersByTimeAsync(850);
    });

    const output = screen.getByText(/## Result \(Lumi Pro\)/);
    expect(output).toBeInTheDocument();
    expect(output.textContent).toContain('Draft a launch email');
    expect(screen.getByRole('button', { name: 'Copy' })).toBeEnabled();
  });

  it('keeps the empty state and does nothing for a blank prompt', async () => {
    vi.useFakeTimers();
    renderTemplate(<AIGenerator />);

    fireEvent.click(screen.getByRole('button', { name: 'Generate' }));
    await act(async () => {
      await vi.advanceTimersByTimeAsync(900);
    });

    expect(screen.getByText('Your generation will appear here.')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Copy' })).toBeDisabled();
  });
});

describe('UsageDashboard template', () => {
  it('renders all usage metrics and the upgrade action', () => {
    renderTemplate(<UsageDashboard />);

    expect(screen.getByRole('heading', { level: 1, name: 'Usage Dashboard' })).toBeInTheDocument();
    for (const label of ['Requests', 'Tokens', 'Cost']) {
      expect(screen.getByText(label)).toBeInTheDocument();
    }
    expect(screen.getByText('18.4k')).toBeInTheDocument();
    expect(screen.getByText('2.1M')).toBeInTheDocument();
    expect(screen.getByText('$84')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Upgrade' })).toBeInTheDocument();
  });

  it('shows the monthly allowance progress with an accessible value', () => {
    renderTemplate(<UsageDashboard />);

    expect(screen.getByRole('heading', { name: 'Monthly allowance' })).toBeInTheDocument();
    const progress = screen.getByRole('progressbar', {
      name: '2,100,000 / 3,000,000 tokens',
    });
    expect(progress).toHaveAttribute('aria-valuenow', '70');
    expect(progress).toHaveAttribute('aria-valuemax', '100');
    expect(screen.getByText('70%')).toBeInTheDocument();
  });
});

describe('ModelSelection template', () => {
  it('renders every model card with the default selection applied', () => {
    renderTemplate(<ModelSelection />);

    expect(screen.getByRole('heading', { level: 1, name: 'Model Selection' })).toBeInTheDocument();
    for (const name of ['Lumi Fast', 'Lumi Pro', 'Lumi Reason']) {
      expect(screen.getByRole('heading', { name })).toBeInTheDocument();
    }
    expect(screen.getByText('Popular')).toBeInTheDocument();
    expect(screen.getAllByRole('button', { name: 'Select' })).toHaveLength(2);
    expect(screen.getAllByRole('button', { name: 'Selected' })).toHaveLength(1);
  });

  it('moves the selection to a card when its Select button is clicked', () => {
    renderTemplate(<ModelSelection />);

    fireEvent.click(screen.getAllByRole('button', { name: 'Select' })[0]);

    expect(screen.getAllByRole('button', { name: 'Selected' })).toHaveLength(1);
    const fastCard = screen.getByRole('heading', { name: 'Lumi Fast' }).closest('[role="button"]');
    expect(fastCard).toHaveClass('border-primary');
  });
});

describe('GenerationHistory template', () => {
  it('renders the full history with statuses and reuse actions', () => {
    renderTemplate(<GenerationHistory />);

    expect(
      screen.getByRole('heading', { level: 1, name: 'Generation History' })
    ).toBeInTheDocument();
    for (const prompt of [
      'Landing page headline options',
      'Onboarding email sequence',
      'Pricing FAQ draft',
    ]) {
      expect(screen.getByText(prompt)).toBeInTheDocument();
    }
    expect(screen.getAllByRole('button', { name: 'Reuse' })).toHaveLength(3);
    expect(screen.getAllByText('saved')).toHaveLength(2);
  });

  it('filters history after the search debounce elapses', async () => {
    vi.useFakeTimers();
    renderTemplate(<GenerationHistory />);

    fireEvent.change(screen.getByPlaceholderText(/Search prompts/), {
      target: { value: 'pricing' },
    });

    expect(screen.getByText('Landing page headline options')).toBeInTheDocument();

    await act(async () => {
      await vi.advanceTimersByTimeAsync(350);
    });

    expect(screen.getByText('Pricing FAQ draft')).toBeInTheDocument();
    expect(screen.queryByText('Landing page headline options')).toBeNull();
    expect(screen.queryByText('Onboarding email sequence')).toBeNull();
  });

  it('shows the empty state when no prompt matches', async () => {
    vi.useFakeTimers();
    renderTemplate(<GenerationHistory />);

    fireEvent.change(screen.getByPlaceholderText(/Search prompts/), {
      target: { value: 'no such prompt' },
    });
    await act(async () => {
      await vi.advanceTimersByTimeAsync(350);
    });

    expect(screen.getByRole('heading', { name: 'No results' })).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: 'Reuse' })).toBeNull();
  });
});
