/**
 * Base service class providing common functionality for API interactions.
 */
export class BaseService {
  constructor(baseUrl = import.meta.env.VITE_API_URL || 'http://localhost:5000') {
    this.baseUrl = baseUrl;
    this.cache = new Map();
    this.cacheTimeout = 5 * 60 * 1000; // 5 minutes
  }

  /**
   * Get cached data or fetch new data if cache is expired.
   * 
   * @param {string} key - Cache key
   * @param {Function} fetchFn - Function to fetch data if cache miss
   * @returns {Promise<any>} Cached or fresh data
   */
  async getCachedData(key, fetchFn) {
    const cached = this.cache.get(key);
    if (cached && (Date.now() - cached.timestamp < this.cacheTimeout)) {
      return cached.data;
    }

    const data = await fetchFn();
    this.cache.set(key, {
      data,
      timestamp: Date.now()
    });
    return data;
  }

  /**
   * Handle API response with error handling.
   * 
   * @param {Response} response - Fetch API response
   * @returns {Promise<any>} Parsed response data
   * @throws {Error} If response is not ok
   */
  async handleResponse(response) {
    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'An unknown error occurred' }));
      throw new Error(error.detail || `HTTP error! status: ${response.status}`);
    }
    return response.json();
  }

  /**
   * Make a GET request to the API.
   * 
   * @param {string} endpoint - API endpoint
   * @param {Object} [params] - Query parameters
   * @returns {Promise<any>} Response data
   */
  async get(endpoint, params = {}) {
    const queryString = new URLSearchParams(params).toString();
    const url = `${this.baseUrl}${endpoint}${queryString ? '?' + queryString : ''}`;
    const response = await fetch(url);
    return this.handleResponse(response);
  }
}
