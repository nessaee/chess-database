from datetime import datetime
from typing import Any, List, Dict, Optional, Union
from pydantic import BaseModel, Field, validator, ConfigDict, ValidationError as PydanticValidationError
from dataclasses import asdict, is_dataclass
from ..models.opening import AnalysisInsight as OpeningAnalysisInsight

class ValidationError(Exception):
    """Custom validation error."""
    pass

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

    def _convert_to_dict(self, obj: Any) -> Dict[str, Any]:
        """Convert various types to dictionary."""
        try:
            if isinstance(obj, dict):
                return obj
            if isinstance(obj, (OpeningAnalysisInsight, BaseModel)):
                return obj.model_dump()
            if is_dataclass(obj):
                return asdict(obj)
            if hasattr(obj, '__dict__'):
                return obj.__dict__
            raise ValidationError(f"Cannot convert {type(obj)} to dictionary")
        except Exception as e:
            raise ValidationError(f"Error converting object to dictionary: {str(e)}")

    def validate_analysis_insight(self, insight: Any) -> Dict[str, Any]:
        """Validate and convert analysis insight to dictionary."""
        try:
            if isinstance(insight, OpeningAnalysisInsight):
                return insight.model_dump()
                
            # Convert to dictionary if needed
            insight_dict = self._convert_to_dict(insight)
            
            # Validate using the OpeningAnalysisInsight model
            try:
                validated = OpeningAnalysisInsight(**insight_dict)
                return validated.model_dump()
            except PydanticValidationError as e:
                raise ValidationError(f"Invalid analysis insight data: {str(e)}")
            
        except ValidationError:
            raise
        except Exception as e:
            raise ValidationError(f"Error validating analysis insight: {str(e)}")

    def validate_analysis_response(self, response: Any) -> Dict[str, Any]:
        """Validate complete analysis response."""
        try:
            if not isinstance(response, dict):
                response = self._convert_to_dict(response)
                
            if 'analysis' in response:
                response['analysis'] = [
                    self.validate_analysis_insight(insight)
                    for insight in response['analysis']
                ]
                
            return response
        except ValidationError:
            raise
        except Exception as e:
            raise ValidationError(f"Error validating analysis response: {str(e)}")
