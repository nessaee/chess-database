/**
 * Format a number as a percentage with one decimal place
 * @param {number} value - The value to format
 * @returns {string} The formatted percentage string
 */
export const formatPercentage = (value) => `${value.toFixed(1)}%`;

/**
 * Format a number with thousands separators
 * @param {number} value - The value to format
 * @returns {string} The formatted number string
 */
export const formatNumber = (value) => 
  new Intl.NumberFormat('en-US').format(value);

/**
 * Format a date in a human-readable format
 * @param {string|Date} date - The date to format
 * @returns {string} The formatted date string
 */
export const formatDate = (date) => 
  new Date(date).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric'
  });
