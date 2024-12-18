import { CACHE_TIMEOUTS, STATUS_CODES } from './constants';

/**
 * Custom error class for API errors
 */
export class APIError extends Error {
  constructor(message, status, data = null) {
    super(message);
    this.name = 'APIError';
    this.status = status;
    this.data = data;
  }
}

/**
 * Base service class providing common functionality for API interactions.
 */
export class BaseService {
  constructor(baseUrl = import.meta.env.VITE_API_URL || 'http://localhost:5000') {
    this.baseUrl = baseUrl;
    this.cache = new Map();
    this.defaultTimeout = CACHE_TIMEOUTS.MEDIUM;
  }

  /**
   * Get cached data or fetch new data if cache is expired.
   * 
   * @param {string} key - Cache key
   * @param {Function} fetchFn - Function to fetch data if cache miss
   * @param {number} [timeout] - Cache timeout in milliseconds
   * @returns {Promise<any>} Cached or fresh data
   */
  async getCachedData(key, fetchFn, timeout = this.defaultTimeout) {
    const cached = this.cache.get(key);
    if (cached && (Date.now() - cached.timestamp < timeout)) {
      return cached.data;
    }

    try {
      const data = await fetchFn();
      this.cache.set(key, {
        data,
        timestamp: Date.now()
      });
      return data;
    } catch (error) {
      if (cached) {
        console.warn('Error fetching fresh data, returning stale cache:', error);
        return cached.data;
      }
      throw error;
    }
  }

  /**
   * Clear cache for a specific key or all cache if no key provided
   * 
   * @param {string} [key] - Specific cache key to clear
   */
  clearCache(key = null) {
    if (key) {
      this.cache.delete(key);
    } else {
      this.cache.clear();
    }
  }

  /**
   * Handle API response with error handling.
   * 
   * @param {Response} response - Fetch API response
   * @returns {Promise<any>} Parsed response data
   * @throws {APIError} If response is not ok
   */
  async handleResponse(response) {
    let data;
    try {
      data = await response.json();
    } catch (error) {
      throw new APIError(
        'Invalid JSON response from server',
        response.status,
        { originalError: error.message }
      );
    }

    if (!response.ok) {
      throw new APIError(
        data.detail || `HTTP error! status: ${response.status}`,
        response.status,
        data
      );
    }

    return data;
  }

  /**
   * Make a GET request to the API.
   * 
   * @param {string} endpoint - API endpoint
   * @param {Object} [params] - Query parameters
   * @returns {Promise<any>} Response data
   */
  async get(endpoint, params = {}) {
    const url = new URL(this.baseUrl + endpoint);
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null) {
        url.searchParams.append(key, value);
      }
    });

    try {
      const response = await fetch(url.toString(), {
        method: 'GET',
        headers: {
          'Accept': 'application/json',
        },
      });
      return this.handleResponse(response);
    } catch (error) {
      throw new APIError(
        'Network error occurred',
        STATUS_CODES.INTERNAL_SERVER_ERROR,
        { originalError: error.message }
      );
    }
  }

  /**
   * Make a POST request to the API.
   * 
   * @param {string} endpoint - API endpoint
   * @param {Object} data - Request body data
   * @returns {Promise<any>} Response data
   */
  async post(endpoint, data = {}) {
    try {
      const response = await fetch(this.baseUrl + endpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json',
        },
        body: JSON.stringify(data),
      });
      return this.handleResponse(response);
    } catch (error) {
      throw new APIError(
        'Network error occurred',
        STATUS_CODES.INTERNAL_SERVER_ERROR,
        { originalError: error.message }
      );
    }
  }
}
