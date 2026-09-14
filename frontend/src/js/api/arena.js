import { ApiError, browserFetch } from './game.js';

const configuredApiBaseUrl = typeof __AIG_API_BASE_URL__ === 'undefined' ? '' : __AIG_API_BASE_URL__;

export function createArenaApi(fetcher = browserFetch, baseUrl = configuredApiBaseUrl) {
  async function request(path, payload, method = 'POST') {
    let response;
    try {
      response = await fetcher(`${baseUrl.replace(/\/$/, '')}/api/arena${path}`, {
        method, cache: 'no-store',
        ...(payload === undefined ? {} : { headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) }),
      });
    } catch {
      throw new ApiError('connection_error', 'Cannot reach Arena. Check the backend, then retry.', 0);
    }
    let body;
    try { body = await response.json(); } catch {
      throw new ApiError('invalid_response', 'Arena returned an unreadable response.', response.status);
    }
    if (!response.ok) {
      if (response.status === 404 && path.startsWith('/observer/')) {
        throw new ApiError('observer_unavailable', `Observer mode is not loaded at ${baseUrl || 'this site'}. Restart that backend (Docker: docker compose restart api; local dev: restart npm run dev), then refresh Arena.`, response.status);
      }
      throw new ApiError(body.error, body.message || (typeof body.detail === 'string' ? body.detail : null) || 'Arena request failed.', response.status);
    }
    return body;
  }
  return {
    createObserverDemo: () => request('/observer/demo'),
    observerTurn: () => request('/observer/turn'),
    getGame: () => request('', undefined, 'GET'),
    createDemo: () => request('/demo'),
    createAiDemo: (provider) => request(provider ? `/demo-ai/${encodeURIComponent(provider)}` : '/demo-ai'),
    command: (type, actor_id, details = {}) => request('/commands', {
      ...details, schema_version: 'arena-command-v2', type: `arena_${type}`, actor_id,
    }),
  };
}
