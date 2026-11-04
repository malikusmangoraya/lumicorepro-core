import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import expandedCatalog from '../../registry/technology-stack-catalog.json';

const apiMocks = vi.hoisted(() => ({
  generate: vi.fn(),
  getTechnologyCatalog: vi.fn(),
  analyzeVision: vi.fn(),
  createPreview: vi.fn(),
  deployRun: vi.fn(),
  connectDomain: vi.fn(),
}));

vi.mock('@/context/AppContext', () => ({
  useAppContext: () => ({ language: 'en', user: null }),
}));

vi.mock('@/services/api', () => ({
  aiAgentAPI: apiMocks,
  previewAPI: { create: apiMocks.createPreview },
  resolvePreviewUrl: vi.fn((url) => url),
}));

vi.mock('@/components/common/PageSEO', () => ({ default: () => null }));

import GeneratePage from '../pages/Generate';

const catalog = {
  version: '1.0',
  languages: {
    nodejs: {
      label: 'Node.js',
      scaffold_supported: true,
      frameworks: [{ id: 'express', label: 'Express', databases: ['postgresql'], orms: ['prisma'] }],
    },
    python: {
      label: 'Python',
      scaffold_supported: false,
      frameworks: [
        {
          id: 'fastapi',
          label: 'FastAPI',
          databases: ['postgresql', 'sqlite', 'mongodb'],
          orms: ['sqlalchemy', 'pymongo'],
        },
      ],
    },
  },
  databases: [
    { id: 'postgresql', label: 'PostgreSQL', type: 'relational' },
    { id: 'sqlite', label: 'SQLite', type: 'relational' },
    { id: 'mongodb', label: 'MongoDB', type: 'document' },
  ],
  orm_database_types: { sqlalchemy: ['relational'], pymongo: ['document'] },
  api_styles: [{ id: 'rest', label: 'REST' }, { id: 'graphql', label: 'GraphQL' }],
  architectures: [{ id: 'modular-monolith', label: 'Modular Monolith' }],
  authentication: [{ id: 'jwt', label: 'JWT' }],
  cache_options: [{ id: 'none', label: 'None' }],
  queue_options: [{ id: 'none', label: 'None' }],
  testing_options: [{ id: 'unit-integration', label: 'Unit + Integration' }],
  observability_options: [{ id: 'structured-logging', label: 'Structured Logging' }],
  deployment_options: [{ id: 'docker', label: 'Docker' }],
  ...expandedCatalog,
};

describe('Generate page backend stack selection', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    apiMocks.getTechnologyCatalog.mockResolvedValue({
      data: { success: true, data: { catalog } },
    });
    apiMocks.generate.mockImplementation(() => new Promise(() => {}));
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it('submits Auto mode by default', async () => {
    render(<GeneratePage />);

    await screen.findByRole('radio', { name: 'Auto' });
    expect(screen.getByRole('radio', { name: 'Auto' })).toBeChecked();
    fireEvent.change(screen.getByLabelText('Website description prompt'), {
      target: { value: 'Build a bakery website' },
    });
    fireEvent.click(screen.getByRole('button', { name: 'Generate website' }));

    await waitFor(() => expect(apiMocks.generate).toHaveBeenCalledOnce());
    expect(apiMocks.generate.mock.calls[0][0].backend_stack).toEqual({ mode: 'auto' });
  }, 15000);

  it('submits only explicitly selected manual and advanced options', async () => {
    render(<GeneratePage />);

    const manualMode = await screen.findByRole('radio', { name: 'Manual' });
    await waitFor(() => expect(manualMode).toBeEnabled());
    fireEvent.click(manualMode);
    await screen.findByLabelText('Backend language');
    fireEvent.change(screen.getByLabelText('Backend language'), {
      target: { value: 'python' },
    });
    fireEvent.change(screen.getByLabelText('Backend framework'), {
      target: { value: 'fastapi' },
    });
    fireEvent.change(screen.getByLabelText('Backend database'), {
      target: { value: 'sqlite' },
    });
    fireEvent.click(screen.getByRole('button', { name: 'Advanced backend options' }));
    fireEvent.change(screen.getByLabelText('API style'), {
      target: { value: 'graphql' },
    });
    fireEvent.change(screen.getByLabelText('Website description prompt'), {
      target: { value: 'Build a bakery website' },
    });
    fireEvent.click(screen.getByRole('button', { name: 'Generate website' }));

    await waitFor(() => expect(apiMocks.generate).toHaveBeenCalledOnce());
    expect(apiMocks.generate.mock.calls[0][0].backend_stack).toEqual({
      mode: 'manual',
      language: 'python',
      framework: 'fastapi',
      database: 'sqlite',
      api_style: 'graphql',
    });
  }, 15000);

  it('filters ORM choices by database and clears incompatible selections', async () => {
    render(<GeneratePage />);

    const manualMode = await screen.findByRole('radio', { name: 'Manual' });
    await waitFor(() => expect(manualMode).toBeEnabled());
    fireEvent.click(manualMode);
    fireEvent.change(await screen.findByLabelText('Backend language'), {
      target: { value: 'python' },
    });
    fireEvent.change(screen.getByLabelText('Backend framework'), {
      target: { value: 'fastapi' },
    });
    fireEvent.change(screen.getByLabelText('Backend database'), {
      target: { value: 'postgresql' },
    });

    const ormSelect = screen.getByLabelText('ORM');
    expect(within(ormSelect).queryByRole('option', { name: 'pymongo' })).not.toBeInTheDocument();

    fireEvent.change(screen.getByLabelText('Backend database'), {
      target: { value: 'mongodb' },
    });
    expect(within(ormSelect).getByRole('option', { name: 'pymongo' })).toBeInTheDocument();
    fireEvent.change(ormSelect, { target: { value: 'pymongo' } });
    fireEvent.change(screen.getByLabelText('Backend database'), {
      target: { value: 'sqlite' },
    });

    expect(screen.getByLabelText('ORM')).toHaveValue('');
  }, 15000);

  it('keeps Auto available and reports catalog loading errors', async () => {
    apiMocks.getTechnologyCatalog.mockRejectedValueOnce(new Error('catalog unavailable'));

    render(<GeneratePage />);

    expect(await screen.findByRole('alert')).toHaveTextContent(/could not load backend options/i);
    expect(screen.getByRole('radio', { name: 'Auto' })).toBeChecked();
    expect(screen.getByRole('radio', { name: 'Manual' })).toBeDisabled();
  }, 15000);

  it('keeps manual choices disabled while the catalog is loading', async () => {
    apiMocks.getTechnologyCatalog.mockImplementation(() => new Promise(() => {}));

    render(<GeneratePage />);

    expect(await screen.findByText('Loading backend options...')).toBeInTheDocument();
    expect(screen.getByRole('radio', { name: 'Auto' })).toBeEnabled();
    expect(screen.getByRole('radio', { name: 'Manual' })).toBeDisabled();
  }, 15000);

  it('disables backend controls while generation is running', async () => {
    render(<GeneratePage />);

    const manualMode = await screen.findByRole('radio', { name: 'Manual' });
    await waitFor(() => expect(manualMode).toBeEnabled());
    fireEvent.click(manualMode);
    await screen.findByLabelText('Backend language');
    fireEvent.change(screen.getByLabelText('Website description prompt'), {
      target: { value: 'Build a bakery website' },
    });
    fireEvent.click(screen.getByRole('button', { name: 'Generate website' }));

    await waitFor(() => expect(apiMocks.generate).toHaveBeenCalledOnce());
    expect(screen.getByLabelText('Backend language')).toBeDisabled();
    expect(screen.getByRole('radio', { name: 'Manual' })).toBeDisabled();
  }, 15000);

  it('reports the resolved stack without claiming an unsupported scaffold was generated', async () => {
    let socket;
    class MockWebSocket {
      constructor() {
        socket = this;
      }

      close() {}
    }
    vi.stubGlobal('WebSocket', MockWebSocket);
    apiMocks.generate.mockResolvedValue({
      data: { mode: 'live_agent', ws_url: 'ws://localhost/generation' },
    });

    render(<GeneratePage />);
    fireEvent.change(screen.getByLabelText('Website description prompt'), {
      target: { value: 'Build a bakery website' },
    });
    fireEvent.click(screen.getByRole('button', { name: 'Generate website' }));
    await waitFor(() => expect(socket).toBeDefined());
    socket.onmessage({
      data: JSON.stringify({
        type: 'complete',
        result: {
          selected_resources: {
            backend_stack: {
              mode: 'manual',
              language: 'python',
              framework: 'fastapi',
              database: 'postgresql',
              scaffold_status: 'catalog_only_not_generated',
            },
          },
        },
      }),
    });

    expect(
      await screen.findByText('Catalog selection only: backend code for this stack was not generated.')
    ).toBeInTheDocument();
    expect(screen.getByText('Python')).toBeInTheDocument();
    expect(screen.getByText('FastAPI')).toBeInTheDocument();
  }, 15000);

  it('shows technology options in grouped panels in Manual mode', async () => {
    render(<GeneratePage />);
    fireEvent.click(await screen.findByRole('radio', { name: 'Manual' }));

    expect((await screen.findAllByText('Additional technologies')).length).toBeGreaterThan(0);
    expect(screen.getByLabelText('Frontend framework')).toBeInTheDocument();
    expect(screen.getByLabelText('Admin and CMS platform')).toBeInTheDocument();
    expect(screen.getByLabelText('Frontend hosting')).toBeInTheDocument();
    expect(screen.getByLabelText('Backend hosting')).toBeInTheDocument();
    expect(screen.getByLabelText('Database hosting')).toBeInTheDocument();
    expect(screen.getByText('Authentication libraries')).toBeInTheDocument();
    expect(screen.getByText('Engineering topics')).toBeInTheDocument();
  });

  it('renders every catalog option in its capability group', async () => {
    render(<GeneratePage />);
    fireEvent.click(await screen.findByRole('radio', { name: 'Manual' }));

    const displayedGroups = [
      ['frontend_frameworks', 'Frontend framework'],
      ['admin_platforms', 'Admin and CMS platform'],
      ['ci_providers', 'Continuous integration'],
      ['source_control_providers', 'Source control'],
      ['authentication_profiles', 'Authentication profile'],
    ];
    for (const [group, label] of displayedGroups) {
      const select = screen.getByLabelText(label);
      for (const option of catalog[group]) {
        expect(within(select).getByRole('option', { name: option.label })).toBeInTheDocument();
      }
    }
    for (const provider of catalog.hosting_providers) {
      const fieldLabel = {
        frontend_host: 'Frontend hosting',
        backend_host: 'Backend hosting',
        database_host: 'Database hosting',
        backend_and_database_host: 'Backend hosting',
      }[provider.category];
      expect(
        within(screen.getByLabelText(fieldLabel)).getByRole('option', { name: provider.label })
      ).toBeInTheDocument();
      if (provider.category === 'backend_and_database_host') {
        expect(
          within(screen.getByLabelText('Database hosting')).getByRole('option', {
            name: provider.label,
          })
        ).toBeInTheDocument();
      }
    }
    for (const [group, label] of [
      ['testing_tools', 'Testing tools'],
      ['quality_tools', 'Quality and security tools'],
    ]) {
      expect(screen.getByText(label)).toBeInTheDocument();
      for (const option of catalog[group]) {
        expect(screen.getByLabelText(new RegExp(option.label, 'i'))).toBeInTheDocument();
      }
    }
    for (const group of ['authentication_libraries', 'engineering_topics']) {
      for (const option of catalog[group]) {
        expect(await screen.findAllByText(option.label)).not.toHaveLength(0);
      }
    }
  });

  it('filters explicitly incompatible hosts and warns about unknown compatibility', async () => {
    const incompatibleCatalog = structuredClone(catalog);
    incompatibleCatalog.frontend_frameworks
      .find((option) => option.id === 'nextjs')
      .compatibility.push({
        group: 'hosting_providers',
        id: 'netlify',
        status: 'incompatible',
      });
    apiMocks.getTechnologyCatalog.mockResolvedValueOnce({
      data: { success: true, data: { catalog: incompatibleCatalog } },
    });

    render(<GeneratePage />);
    fireEvent.click(await screen.findByRole('radio', { name: 'Manual' }));
    fireEvent.change(await screen.findByLabelText('Frontend framework'), {
      target: { value: 'nextjs' },
    });

    const frontendHost = screen.getByLabelText('Frontend hosting');
    expect(within(frontendHost).queryByRole('option', { name: 'Netlify' }))
      .not.toBeInTheDocument();
    fireEvent.change(frontendHost, { target: { value: 'github-pages' } });
    expect(await screen.findByText(/compatibility is unverified/i)).toBeInTheDocument();
  });

  it('submits selected technology choices and testing tool lists', async () => {
    render(<GeneratePage />);
    fireEvent.click(await screen.findByRole('radio', { name: 'Manual' }));
    fireEvent.change(await screen.findByLabelText('Frontend framework'), {
      target: { value: 'nextjs' },
    });
    fireEvent.click(await screen.findByLabelText(/Playwright/));
    fireEvent.change(screen.getByLabelText('Website description prompt'), {
      target: { value: 'Build a bakery website' },
    });
    fireEvent.click(screen.getByRole('button', { name: 'Generate website' }));

    await waitFor(() => expect(apiMocks.generate).toHaveBeenCalledOnce());
    expect(apiMocks.generate.mock.calls[0][0].technology_choices).toEqual({
      frontend_framework: 'nextjs',
      testing_tools: ['playwright'],
    });
  });

  it('clears manual technology choices when returning to Auto', async () => {
    render(<GeneratePage />);
    fireEvent.click(await screen.findByRole('radio', { name: 'Manual' }));
    const frameworkSelect = await screen.findByLabelText('Frontend framework');
    fireEvent.change(frameworkSelect, { target: { value: 'nextjs' } });
    fireEvent.click(screen.getByRole('radio', { name: 'Auto' }));
    fireEvent.click(screen.getByRole('radio', { name: 'Manual' }));

    expect(await screen.findByLabelText('Frontend framework')).toHaveValue('');
  });

  it('keeps technology catalog loading, error, and disabled states explicit', async () => {
    apiMocks.getTechnologyCatalog.mockRejectedValueOnce(new Error('catalog unavailable'));
    render(<GeneratePage />);

    expect(await screen.findByRole('alert')).toHaveTextContent(/could not load backend options/i);
    expect(screen.getByRole('radio', { name: 'Manual' })).toBeDisabled();
  });

  it('reports catalog-only technology selections without claiming they were generated', async () => {
    let socket;
    class MockWebSocket {
      constructor() {
        socket = this;
      }

      close() {}
    }
    vi.stubGlobal('WebSocket', MockWebSocket);
    apiMocks.generate.mockResolvedValue({
      data: { mode: 'live_agent', ws_url: 'ws://localhost/generation' },
    });

    render(<GeneratePage />);
    fireEvent.change(await screen.findByLabelText('Website description prompt'), {
      target: { value: 'Build a bakery website' },
    });
    fireEvent.click(screen.getByRole('button', { name: 'Generate website' }));
    await waitFor(() => expect(socket).toBeDefined());
    socket.onmessage({
      data: JSON.stringify({
        type: 'complete',
        result: {
          selected_resources: {
            technology_choices: {
              choices: { frontend_framework: 'nextjs' },
              resolved_options: [
                {
                  field: 'frontend_framework',
                  id: 'nextjs',
                  label: 'Next.js',
                  capability_status: 'catalog_only_not_generated',
                  compatibility_status: 'not_applicable',
                },
              ],
              warnings: [],
            },
          },
        },
      }),
    });

    expect(
      await screen.findByText('Catalog selection only: Next.js was not generated.')
    ).toBeInTheDocument();
  });
});
