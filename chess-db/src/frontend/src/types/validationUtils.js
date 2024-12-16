// src/types/validationUtils.js

/**
 * Validates a date range to ensure start date is before or equal to end date
 * @param {string} start - Start date in YYYY-MM-DD format
 * @param {string} end - End date in YYYY-MM-DD format
 * @returns {boolean} True if date range is valid
 */
export const validateDateRange = (start, end) => {
    if (!start || !end) return true; // Allow partial ranges
    
    try {
      const startDate = new Date(start);
      const endDate = new Date(end);
      
      if (isNaN(startDate.getTime()) || isNaN(endDate.getTime())) {
        console.warn('Invalid date format detected');
        return false;
      }
      
      return startDate <= endDate;
    } catch (error) {
      console.error('Date validation error:', error);
      return false;
    }
  };
  
  /**
   * Validates opening analysis data structure
   * @param {Object} data - Opening analysis data to validate
   * @returns {boolean} True if data structure is valid
   */
  export const validateOpeningData = (data) => {
    if (!data || !Array.isArray(data.analysis)) {
      console.warn('Invalid opening data structure');
      return false;
    }
    
    const requiredFields = [
      'total_openings',
      'avg_game_length'
    ];
    
    // Validate required top-level fields
    const hasRequiredFields = requiredFields.every(field => {
      const isValid = field in data && typeof data[field] === 'number';
      if (!isValid) console.warn(`Missing or invalid field: ${field}`);
      return isValid;
    });
    
    if (!hasRequiredFields) return false;
    
    // Validate each opening entry
    return data.analysis.every((opening, index) => {
      try {
        const isValid = (
          opening.eco_code &&
          typeof opening.total_games === 'number' &&
          typeof opening.win_rate === 'number' &&
          opening.win_rate >= 0 &&
          opening.win_rate <= 100
        );
        
        if (!isValid) {
          console.warn(`Invalid opening data at index ${index}:`, opening);
        }
        
        return isValid;
      } catch (error) {
        console.error(`Error validating opening at index ${index}:`, error);
        return false;
      }
    });
  };