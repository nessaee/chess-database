# repository/analysis/validation.py
from datetime import datetime
from typing import Any, List, Dict, Optional
from pydantic import BaseModel, Field, validator

class AnalysisValidator:
    """Validator for analysis data and parameters."""
    
    def validate_date(self, date_str: str, field_name: str) -> None:
        """Validate date string format."""
        try:
            datetime.strptime(date_str, '%Y-%m-%d')
        except ValueError:
            raise ValidationError(
                f"Invalid {field_name} format (use YYYY-MM-DD)"
            )

    def validate_rating_range(
        self,
        min_rating: Optional[int],
        max_rating: Optional[int]
    ) -> None:
        """Validate rating range parameters."""
        if min_rating is not None and (
            not isinstance(min_rating, int) or
            min_rating < 0 or
            min_rating > 3000
        ):
            raise ValidationError("min_rating must be between 0 and 3000")
            
        if max_rating is not None and (
            not isinstance(max_rating, int) or
            max_rating < 0 or
            max_rating > 3000
        ):
            raise ValidationError("max_rating must be between 0 and 3000")
            
        if (min_rating is not None and 
            max_rating is not None and 
            min_rating > max_rating
        ):
            raise ValidationError(
                "min_rating cannot be greater than max_rating"
            )

    def validate_eco_code(self, eco: str) -> None:
        """Validate ECO code format."""
        if not (
            len(eco) == 3 and
            eco[0] in 'ABCDE' and
            eco[1:].isdigit()
        ):
            raise ValidationError("Invalid ECO code format")
