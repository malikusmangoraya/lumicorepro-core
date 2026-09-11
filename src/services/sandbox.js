/**
 * Sandbox Service — StackBlitz WebContainers integration.
 *
 * Mounts generated project files into an in-browser Node.js runtime,
 * installs dependencies, runs dev server, and pipes output to the UI.
 */
import { api } from './api';
import { getApiKey } from './apiConfig';

let webcontainerInstance = null;
let currentTerminalLines = [];

export const getWebContainer = async () => {
  if (webcontainerInstance) return webcontainerInstance;

  try {
    const { WebContainer } = await import('@webcontainer/api');
    webcontainerInstance = await WebContainer.boot();
    return webcontainerInstance;
  } catch {
    return null;
  }
};

export const loadProjectToSandbox = async (runId, { onTerminal, onReady, onError }) => {
  const container = await getWebContainer();
  if (!container) {
    onError?.('WebContainer not available in this browser. Use Chrome/Edge with SharedArrayBuffer support.');
    return null;
  }

  try {
    const apiKey = getApiKey('agent') || '';
    const res = await api.get(`/ai/sandbox/${runId}`, {
      headers: apiKey ? { 'X-API-Key': apiKey } : {},
    });
    const data = res?.data?.data;
    if (!data?.mount_tree) {
      onError?.('Sandbox payload empty — project may not be generated yet.');
      return null;
    }

    currentTerminalLines = [];
    const term = container.serial;
    term.onData((line) => {
      currentTerminalLines.push(line);
      if (currentTerminalLines.length > 500) currentTerminalLines.shift();
      onTerminal?.(line);
    });

    await container.mount(data.mount_tree);

    const installProc = await container.spawn('npm', ['install']);
    await installProc.exit;

    const startCmd = (data.start_command || 'npm run dev').split(' ');
    const devProc = await container.spawn(startCmd[0], startCmd.slice(1));
    devProc.exit.then((code) => {
      if (code !== 0) {
        onError?.(`Dev server exited with code ${code}`);
      }
    });

    onReady?.({
      container,
      url: container.url,
      port: data.port || 5173,
      startCommand: data.start_command,
    });

    return container;
  } catch (err) {
    onError?.(`Sandbox error: ${err.message}`);
    return null;
  }
};

export const stopSandbox = async () => {
  if (webcontainerInstance) {
    try {
      await webcontainerInstance.teardown();
    } catch {
      // Teardown may fail if container is already stopped
    }
    webcontainerInstance = null;
  }
  currentTerminalLines = [];
};

export const getTerminalHistory = () => [...currentTerminalLines];
