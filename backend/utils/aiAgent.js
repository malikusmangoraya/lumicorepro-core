/**
 * AI-agent upstream helpers.
 *
 * The Express backend proxies generation, chat, preview, download, and
 * extension calls to the Python FastAPI agent. These helpers centralize three
 * previously scattered failure modes:
 *
 * - upstream fetches without timeouts;
 * - preview/WebSocket URLs that forced `http:`/`ws:` even for HTTPS agents;
 * - unsafe string handling for optional user input used in slugs.
 */

export const AI_AGENT_TIMEOUTS = {
  generate: 240000,
  chat: 30000,
  vision: 60000,
  status: 15000,
  download: 300000,
  preview: 30000,
  deploy: 120000,
  extension: 120000,
};

const BACKEND_STACK_FIELDS = new Set([
  'language',
  'framework',
  'database',
  'orm',
  'api_style',
  'architecture',
  'authentication',
  'cache',
  'queue',
  'testing',
  'observability',
  'deployment',
]);

const TECHNOLOGY_CHOICE_FIELDS = new Set([
  'frontend_framework',
  'admin_platform',
  'frontend_host',
  'backend_host',
  'database_host',
  'source_control_provider',
  'testing_tools',
  'quality_tools',
  'ci_provider',
  'authentication_profile',
]);
const TECHNOLOGY_CHOICE_LIST_FIELDS = new Set(['testing_tools', 'quality_tools']);

export function validateTechnologyChoicesPayload(value) {
  if (value === undefined) return undefined;
  if (!value || typeof value !== 'object' || Array.isArray(value)) {
    throw new TypeError('technology_choices must be an object.');
  }

  for (const [key, choice] of Object.entries(value)) {
    if (!TECHNOLOGY_CHOICE_FIELDS.has(key)) {
      throw new TypeError(`Unknown technology_choices field: ${key}.`);
    }
    if (TECHNOLOGY_CHOICE_LIST_FIELDS.has(key)) {
      if (
        !Array.isArray(choice) ||
        choice.some((item) => typeof item !== 'string' || !item.trim())
      ) {
        throw new TypeError(`technology_choices.${key} must be a list of non-empty IDs.`);
      }
    } else if (typeof choice !== 'string' || !choice.trim()) {
      throw new TypeError(`technology_choices.${key} must be a non-empty catalog ID.`);
    }
  }

  return { ...value };
}

export function validateBackendStackPayload(value) {
  if (value === undefined) return undefined;
  if (!value || typeof value !== 'object' || Array.isArray(value)) {
    throw new TypeError('backend_stack must be an object.');
  }

  for (const key of Object.keys(value)) {
    if (key !== 'mode' && !BACKEND_STACK_FIELDS.has(key)) {
      throw new TypeError(`Unknown backend_stack field: ${key}.`);
    }
  }

  if (value.mode !== undefined && !['auto', 'manual'].includes(value.mode)) {
    throw new TypeError("backend_stack.mode must be 'auto' or 'manual'.");
  }
  for (const key of BACKEND_STACK_FIELDS) {
    if (value[key] !== undefined && (typeof value[key] !== 'string' || !value[key].trim())) {
      throw new TypeError(`backend_stack.${key} must be a non-empty catalog ID.`);
    }
  }

  return { ...value };
}

export function agentBaseUrl(value = process.env.AI_AGENT_URL || 'http://localhost:8000') {
  let url;
  try {
    url = new URL(value);
  } catch {
    throw new Error(`Invalid AI_AGENT_URL: ${value}`);
  }
  if (!['http:', 'https:'].includes(url.protocol)) {
    throw new Error(`Invalid AI_AGENT_URL protocol: ${url.protocol}`);
  }
  return url;
}

export function agentEndpointUrl(endpoint, value) {
  return new URL(endpoint, agentBaseUrl(value)).toString();
}

export function agentPreviewUrl(slug, rest = '', value) {
  const base = agentBaseUrl(value);
  const path = rest
    ? `/preview/${encodeURIComponent(slug)}/${encodeURIComponent(rest)}`
    : `/preview/${encodeURIComponent(slug)}`;
  return new URL(path, base).toString();
}

export function agentWebSocketUrl(runId, value) {
  const base = agentBaseUrl(value);
  base.protocol = base.protocol === 'https:' ? 'wss:' : 'ws:';
  base.pathname = `/ws/generate/${encodeURIComponent(runId)}`;
  base.search = '';
  base.hash = '';
  return base.toString();
}

export function slugifyProjectName(value, fallback = 'generated-website') {
  const slug = String(value || '')
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '')
    .slice(0, 30);
  return slug || fallback;
}

export async function fetchWithTimeout(url, options = {}, timeoutMs = 30000) {
  const { timeout, ...fetchOptions } = options;
  const effectiveTimeout = timeout ?? timeoutMs;
  const controller = new AbortController();
  let timedOut = false;
  const timeoutError = new Error(`Request timed out after ${effectiveTimeout}ms`);
  timeoutError.code = 'FETCH_TIMEOUT';
  let timer;
  const timeoutPromise = new Promise((_, reject) => {
    timer = setTimeout(() => {
      timedOut = true;
      controller.abort();
      reject(timeoutError);
    }, effectiveTimeout);
  });
  try {
    // Race the timeout as well as passing AbortSignal: a hung upstream that
    // ignores abort signals must still release the caller.
    return await Promise.race([
      fetch(url, {
        ...fetchOptions,
        signal: fetchOptions.signal ?? controller.signal,
      }),
      timeoutPromise,
    ]);
  } catch (err) {
    if (err === timeoutError || (err?.name === 'AbortError' && timedOut)) {
      throw timeoutError;
    }
    throw err;
  } finally {
    clearTimeout(timer);
  }
}

export async function fetchAgentJson(endpoint, options = {}) {
  const { timeoutMs = AI_AGENT_TIMEOUTS.status, agentUrl, ...fetchOptions } = options;
  const url = agentEndpointUrl(endpoint, agentUrl);
  const response = await fetchWithTimeout(
    url,
    {
      headers: { 'Content-Type': 'application/json', ...(fetchOptions.headers || {}) },
      ...fetchOptions,
    },
    timeoutMs
  );
  if (!response.ok) {
    const errorText = await response.text();
    const error = new Error(`Agent request failed (${response.status}): ${errorText}`);
    error.status = response.status;
    throw error;
  }
  return response.json();
}
