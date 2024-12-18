/**
 * API endpoint constants
 */
export const API_ENDPOINTS = {
  // Game endpoints
  GAMES: {
    BASE: '/api/games',
    COUNT: '/api/games/count',
    RECENT: '/api/games/recent',
    STATS: '/api/games/stats',
    PLAYER_GAMES: (playerName) => `/api/games/player/${encodeURIComponent(playerName)}`,
    PLAYER_SUGGESTIONS: '/api/games/players/suggest',
    GAME_BY_ID: (gameId) => `/api/games/${gameId}`,
  },

  // Player endpoints
  PLAYERS: {
    BASE: '/api/players',
    SEARCH: '/api/players/search',
    PLAYER_BY_ID: (playerId) => `/api/players/${playerId}`,
    PERFORMANCE: (playerId) => `/api/players/${playerId}/performance`,
    DETAILED_STATS: (playerId) => `/api/players/${playerId}/detailed-stats`,
    OPENINGS: (playerId) => `/api/players/${playerId}/openings`,
  },

  // Analysis endpoints
  ANALYSIS: {
    BASE: '/api/analysis',
    POSITION: '/api/analysis/position',
    GAME: (gameId) => `/api/analysis/game/${gameId}`,
    OPENING_STATS: '/api/analysis/opening-stats',
    SIMILAR_GAMES: '/api/analysis/similar-games',
    MOVE_COUNTS: '/api/analysis/move-counts',
    POPULAR_OPENINGS: '/api/analysis/popular-openings',
  },

  // Database endpoints
  DATABASE: {
    BASE: '/api/database',
    METRICS: '/api/database/metrics'
  },
};

/**
 * Cache timeout configurations (in milliseconds)
 */
export const CACHE_TIMEOUTS = {
  SHORT: 1 * 60 * 1000,      // 1 minute
  MEDIUM: 5 * 60 * 1000,     // 5 minutes
  LONG: 15 * 60 * 1000,      // 15 minutes
  VERY_LONG: 60 * 60 * 1000, // 1 hour
};

/**
 * API configuration constants
 */
export const API_CONFIG = {
  DEFAULT_LIMIT: 50,
  MAX_LIMIT: 100,
  MAX_ANALYSIS_DEPTH: 30,
  MAX_VARIATIONS: 5,
  MOVE_NOTATION: 'san',
};

/**
 * HTTP Status codes
 */
export const STATUS_CODES = {
  OK: 200,
  BAD_REQUEST: 400,
  UNAUTHORIZED: 401,
  FORBIDDEN: 403,
  NOT_FOUND: 404,
  INTERNAL_SERVER_ERROR: 500,
};
