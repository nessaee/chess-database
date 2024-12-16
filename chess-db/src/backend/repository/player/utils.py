# repository/player/utils.py
from typing import Dict, Any, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

def validate_date_param(
    date_str: Optional[str],
    param_name: str
) -> Optional[str]:
    """
    Validate and format date parameter.
    
    Args:
        date_str: Date string to validate (YYYY-MM-DD)
        param_name: Parameter name for error messages
        
    Returns:
        Validated date string or None
        
    Raises:
        ValueError: If date format is invalid
    """
    if not date_str:
        return None
        
    try:
        date = datetime.strptime(date_str, '%Y-%m-%d')
        return date.strftime('%Y-%m-%d')
    except ValueError:
        raise ValueError(
            f"{param_name} must be in YYYY-MM-DD format"
        )

def prepare_query_params(
    params: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Prepare and validate query parameters.
    
    Args:
        params: Raw parameter dictionary
        
    Returns:
        Validated and processed parameters
        
    Raises:
        ValueError: If parameter values are invalid
    """
    processed = {}
    
    for key, value in params.items():
        if value is None:
            continue
            
        if key.endswith('_date'):
            processed[key] = validate_date_param(value, key)
        elif isinstance(value, (int, float)):
            if value < 0:
                raise ValueError(f"{key} must be non-negative")
            processed[key] = value
        else:
            processed[key] = value
            
    return processed