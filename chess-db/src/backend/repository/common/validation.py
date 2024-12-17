# repository/common/validation.py
from typing import TypeVar, Generic, Optional, List, Dict, Any, Type
from datetime import datetime, date
from pydantic import BaseModel, ValidationError
import logging
from fastapi import HTTPException

T = TypeVar('T', bound=BaseModel)

class DataValidator(Generic[T]):
    """
    Generic data validator for repository entities.
    
    Provides validation logic using Pydantic models with
    detailed error reporting.
    """
    
    def __init__(self, model_class: Type[T]):
        """
        Initialize validator with model class.
        
        Args:
            model_class: Pydantic model class for validation
        """
        self.model_class = model_class
        self.logger = logging.getLogger(__name__)
    
    def validate(self, data: Dict[str, Any]) -> Optional[T]:
        """
        Validate data against model schema.
        
        Args:
            data: Dictionary of data to validate
            
        Returns:
            Validated model instance or None if validation fails
        """
        try:
            return self.model_class(**data)
        except ValidationError as e:
            self.logger.error(f"Validation error: {str(e)}")
            return None

    def validate_partial(
        self,
        data: Dict[str, Any],
        exclude_unset: bool = True
    ) -> T:
        """
        Validate partial data update.
        
        Args:
            data: Dictionary of data to validate
            exclude_unset: Whether to exclude unset fields
            
        Returns:
            Validated model instance
            
        Raises:
            ValidationError: If validation fails
        """
        try:
            return self.model_class.parse_obj(data)
        except ValidationError as e:
            raise ValidationError(
                str(e),
                errors=[error.dict() for error in e.errors()]
            )


class DateHandler:
    """Handler for date validation and parsing"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.date_formats = [
            "%Y-%m-%d",
            "%Y/%m/%d",
            "%d-%m-%Y",
            "%d/%m/%Y"
        ]
    
    def validate_and_parse_date(
        self,
        date_str: Optional[str],
        field_name: str
    ) -> Optional[str]:
        """
        Validate and parse date string into standard format.
        
        Args:
            date_str: Date string to validate
            field_name: Name of field for error messages
            
        Returns:
            Validated date string in YYYY-MM-DD format or None if not provided
            
        Raises:
            HTTPException: If date string is invalid
        """
        self.logger.debug(f"Validating date for {field_name}: {date_str}")
        
        if date_str is None or date_str.strip() == '':
            self.logger.debug(f"No date provided for {field_name}")
            return None
            
        date_str = date_str.strip()
        for fmt in self.date_formats:
            try:
                parsed_date = datetime.strptime(date_str, fmt)
                result = parsed_date.date().isoformat()
                self.logger.debug(f"Successfully parsed date {date_str} as {result}")
                return result
            except ValueError:
                continue
                
        self.logger.error(f"Invalid date format for {field_name}: {date_str}")
        raise HTTPException(
            status_code=400,
            detail=f"Invalid date format for {field_name}. Expected format: YYYY-MM-DD"
        )
