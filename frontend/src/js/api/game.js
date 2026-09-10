/** The only browser network boundary. Commands return authoritative state. */
export class ApiError extends Error {
  constructor(code, message, status) {
    super(message);
    this.code = code;
    this.status = status;
  }
}

// esbuild supplies the public origin; direct Node tests retain same-origin URLs.
const configuredApiBaseUrl = typeof __AIG_API_BASE_URL__ === 'undefined' ? '' : __AIG_API_BASE_URL__;

export function createGameApi(fetcher = (...args) => fetch(...args), baseUrl = configuredApiBaseUrl) {
  const origin = baseUrl.replace(/\/$/, '');
  async function request(path = '', payload, method = 'POST') {
    let response;
    try {
      response = await fetcher(`${origin}/api/game${path}`, {
        method, cache: 'no-store',
        ...(payload === undefined ? {} : {
          headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload),
        }),
      });
    } catch {
      throw new ApiError('connection_error', 'Cannot reach the game. Check the backend and dev server, then retry.', 0);
    }
    let body;
    try { body = await response.json(); } catch {
      throw new ApiError('invalid_response', 'The game server returned an unreadable response. Check the backend log.', response.status);
    }
    if (!response.ok) throw new ApiError(body.error, body.message || 'The request failed.', response.status);
    return body;
  }
  const command = (payload) => request('/commands', payload);
  return {
    getGame: () => request('', undefined, 'GET'),
    createDemoGame: () => request('/demo'),
    createAiDemoGame: () => request('/demo/ai'),
    createLlmDemoGame: () => request('/demo/llm'),
    startGame: () => request('/start'),
    moveUnit: (unitId, x, y) => command({ type: 'move_unit', unitId, x, y }),
    attackUnit: (attackerUnitId, targetUnitId) => command({ type: 'attack_unit', attackerUnitId, targetUnitId }),
    foundCity: (settlerUnitId, name) => command({ type: 'found_city', settlerUnitId, name }),
    setProduction: (cityId, unitType) => command({ type: 'set_city_production', cityId, unitType }),
    setResearch: (technology) => command({ type: 'set_research', technology }),
    endActivation: () => command({ type: 'end_activation' }),
  };
}
