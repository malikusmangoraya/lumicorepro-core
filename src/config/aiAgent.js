const configuredUrl = import.meta.env.VITE_AI_URL || 'http://localhost:8000';

export const AI_AGENT_URL = configuredUrl.replace(/\/+$/, '');
export const AI_AGENT_WS_URL = AI_AGENT_URL.replace(/^https:/i, 'wss:').replace(/^http:/i, 'ws:');
