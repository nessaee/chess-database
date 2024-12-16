def validate_opening_stats(
        self,
        stats: OpeningStats
    ) -> ValidationResult:
        """
        Validate chess opening statistics.
        
        Performs comprehensive validation of opening statistics including:
        - Game count consistency
        - Win rate calculations
        - ECO code validity
        - Performance metrics
        
        Args:
            stats: OpeningStats object to validate
            
        Returns:
            ValidationResult with detailed error information
        """
        errors = []
        context: Dict[str, Any] = {}

        # Validate ECO code format
        if not stats.eco or not len(stats.eco) == 3:
            errors.append("Invalid ECO code length")
            context["eco"] = stats.eco
        elif not (stats.eco[0].isalpha() and stats.eco[1:].isdigit()):
            errors.append("Invalid ECO code format (should be letter + 2 digits)")
            context["eco"] = stats.eco

        # Validate game counts
        if stats.games_played < 0:
            errors.append("Games played cannot be negative")
            context["games_played"] = stats.games_played

        total_games = stats.wins + stats.losses + stats.draws
        if total_games != stats.games_played:
            errors.append(
                f"Sum of outcomes ({total_games}) does not match "
                f"games played ({stats.games_played})"
            )
            context["game_count_mismatch"] = {
                "total": total_games,
                "games_played": stats.games_played
            }

        # Validate win rate
        win_rate_result = self._validate_percentage(
            stats.win_rate,
            "win_rate"
        )
        if not win_rate_result.is_valid:
            errors.extend(win_rate_result.errors)
            if win_rate_result.context:
                context.update(win_rate_result.context)

        # Validate calculated win # repository/player/validation.py
from dataclasses import dataclass
from datetime import datetime, date
from typing import (
    Dict, List, Optional, Any, Set, Protocol, 
    runtime_checkable, TypeVar, Generic
)
import logging

from .types import (
    PlayerDB,
    PlayerStats,
    PlayerAnalysis,
    PerformanceMetrics,
    OpeningStats,
    RatingProgression
)
from ..common.errors import ValidationError

@dataclass
class ValidationResult:
    """
    Result of a validation operation with detailed error information.
    
    Attributes:
        is_valid: Whether the validation passed
        errors: List of validation error messages
        field: Optional field name that failed validation
        context: Optional additional context about the validation
    """
    is_valid: bool
    errors: List[str]
    field: Optional[str] = None
    context: Optional[Dict[str, Any]] = None

    def __bool__(self) -> bool:
        """Allow direct boolean usage of validation result."""
        return self.is_valid

T = TypeVar('T')

@runtime_checkable
class ValidatorProtocol(Protocol[T]):
    """Protocol defining the interface for validators."""
    
    def validate(self, value: T) -> ValidationResult:
        """Validate a value and return detailed results."""
        ...

class BaseValidator:
    """
    Base class for validators providing common utility methods.
    
    This class implements shared validation logic and utilities
    that can be used by specific validator implementations.
    """
    
    def __init__(self):
        """Initialize validator with logging configuration."""
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    def _validate_date(
        self,
        date_value: Any,
        field_name: str,
        allow_future: bool = False
    ) -> ValidationResult:
        """
        Validate a date value with configurable constraints.
        
        Args:
            date_value: Date value to validate
            field_name: Name of field being validated for error messages
            allow_future: Whether future dates are allowed
            
        Returns:
            ValidationResult indicating validity and any errors
        """
        if not isinstance(date_value, (date, datetime)):
            return ValidationResult(
                is_valid=False,
                errors=[f"{field_name} must be a valid date"],
                field=field_name
            )

        if not allow_future and date_value > datetime.now():
            return ValidationResult(
                is_valid=False,
                errors=[f"{field_name} cannot be in the future"],
                field=field_name,
                context={"value": date_value}
            )

        return ValidationResult(is_valid=True, errors=[])

    def _validate_rating(
        self,
        rating: Any,
        field_name: str,
        min_rating: int = 0,
        max_rating: int = 3000
    ) -> ValidationResult:
        """
        Validate a chess rating value.
        
        Args:
            rating: Rating value to validate
            field_name: Name of field being validated
            min_rating: Minimum allowed rating
            max_rating: Maximum allowed rating
            
        Returns:
            ValidationResult indicating validity and any errors
        """
        if not isinstance(rating, (int, float)):
            return ValidationResult(
                is_valid=False,
                errors=[f"{field_name} must be a number"],
                field=field_name
            )

        if not (min_rating <= rating <= max_rating):
            return ValidationResult(
                is_valid=False,
                errors=[
                    f"{field_name} must be between {min_rating} and {max_rating}"
                ],
                field=field_name,
                context={"value": rating}
            )

        return ValidationResult(is_valid=True, errors=[])

    def _validate_percentage(
        self,
        value: Any,
        field_name: str
    ) -> ValidationResult:
        """
        Validate a percentage value.
        
        Args:
            value: Percentage value to validate
            field_name: Name of field being validated
            
        Returns:
            ValidationResult indicating validity and any errors
        """
        if not isinstance(value, (int, float)):
            return ValidationResult(
                is_valid=False,
                errors=[f"{field_name} must be a number"],
                field=field_name
            )

        if not (0 <= value <= 100):
            return ValidationResult(
                is_valid=False,
                errors=[f"{field_name} must be between 0 and 100"],
                field=field_name,
                context={"value": value}
            )

        return ValidationResult(is_valid=True, errors=[])

class PlayerValidator(BaseValidator):
    """
    Validator for player-related data structures.
    
    Implements comprehensive validation rules for all player data
    including basic information, statistics, and analysis results.
    """
    
    def validate_player(self, player: PlayerDB) -> ValidationResult:
        """
        Validate player data with comprehensive checks.
        
        Validates:
        - Basic field types and constraints
        - Name format and length
        - Rating range and constraints
        - Game count consistency
        - Date validity
        
        Args:
            player: PlayerDB object to validate
            
        Returns:
            ValidationResult with detailed error information
        """
        errors = []
        context: Dict[str, Any] = {}

        # Validate ID
        if not player.id or player.id <= 0:
            errors.append("Player ID must be a positive integer")
            context["id"] = player.id

        # Validate name
        if not player.name or not player.name.strip():
            errors.append("Player name cannot be empty")
        elif len(player.name) > 100:  # Arbitrary reasonable limit
            errors.append("Player name is too long (max 100 characters)")
            context["name_length"] = len(player.name)

        # Validate stats if present
        if player.stats:
            stats_result = self._validate_player_stats(player.stats)
            if not stats_result.is_valid:
                errors.extend(stats_result.errors)
                if stats_result.context:
                    context.update(stats_result.context)

        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            context=context if context else None
        )

    def _validate_player_stats(
        self,
        stats: PlayerStats
    ) -> ValidationResult:
        """
        Validate player statistics data.
        
        Args:
            stats: PlayerStats object to validate
            
        Returns:
            ValidationResult with detailed error information
        """
        errors = []
        context: Dict[str, Any] = {}

        # Validate total games
        if stats.total_games < 0:
            errors.append("Total games cannot be negative")
            context["total_games"] = stats.total_games

        # Validate rating if present
        if stats.current_rating is not None:
            rating_result = self._validate_rating(
                stats.current_rating,
                "current_rating"
            )
            if not rating_result.is_valid:
                errors.extend(rating_result.errors)
                if rating_result.context:
                    context.update(rating_result.context)

        # Validate last active date if present
        if stats.last_active:
            date_result = self._validate_date(
                stats.last_active,
                "last_active"
            )
            if not date_result.is_valid:
                errors.extend(date_result.errors)
                if date_result.context:
                    context.update(date_result.context)

        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            context=context if context else None
        )

    def validate_performance_metrics(
        self,
        metrics: PerformanceMetrics
    ) -> ValidationResult:
        """
        Validate performance metrics with statistical checks.
        
        Validates:
        - Win/loss/draw counts and percentages
        - Rating progression consistency
        - Statistical measure validity
        - Date range constraints
        
        Args:
            metrics: Performance metrics to validate
            
        Returns:
            ValidationResult with detailed error information
        """
        errors = []
        context: Dict[str, Any] = {}

        # Validate game counts
        if metrics.total_games < 0:
            errors.append("Total games cannot be negative")
            context["total_games"] = metrics.total_games

        # Validate game count consistency
        total_outcomes = metrics.wins + metrics.losses + metrics.draws
        if total_outcomes != metrics.total_games:
            errors.append(
                f"Sum of outcomes ({total_outcomes}) does not match "
                f"total games ({metrics.total_games})"
            )
            context["outcome_sum"] = total_outcomes

        # Validate win rate
        win_rate_result = self._validate_percentage(
            metrics.win_rate,
            "win_rate"
        )
        if not win_rate_result.is_valid:
            errors.extend(win_rate_result.errors)
            if win_rate_result.context:
                context.update(win_rate_result.context)

        # Validate ratings if present
        if metrics.current_rating is not None:
            current_rating_result = self._validate_rating(
                metrics.current_rating,
                "current_rating"
            )
            if not current_rating_result.is_valid:
                errors.extend(current_rating_result.errors)
                if current_rating_result.context:
                    context.update(current_rating_result.context)

        if metrics.peak_rating is not None:
            peak_rating_result = self._validate_rating(
                metrics.peak_rating,
                "peak_rating"
            )
            if not peak_rating_result.is_valid:
                errors.extend(peak_rating_result.errors)
                if peak_rating_result.context:
                    context.update(peak_rating_result.context)

            # Validate peak vs current rating consistency
            if (metrics.current_rating and 
                metrics.peak_rating < metrics.current_rating):
                errors.append("Peak rating cannot be less than current rating")
                context["rating_inconsistency"] = {
                    "peak": metrics.peak_rating,
                    "current": metrics.current_rating
                }

        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            context=context if context else None
        )

    def validate_opening_stats(
        self,
        stats: OpeningStats
    ) -> ValidationResult:
        """
        Validate chess opening statistics comprehensively.
        
        Performs detailed validation of opening statistics including:
        - Game count consistency and non-negativity
        - Win rate calculations and percentage constraints
        - ECO code format and validity
        - Performance rating calculations
        - Statistical consistency between metrics
        
        Args:
            stats: OpeningStats object to validate
            
        Returns:
            ValidationResult with detailed error information
            
        Note:
            ECO codes must follow the standard format: one letter (A-E) followed by two digits
        """
        errors: List[str] = []
        context: Dict[str, Any] = {}

        # Validate ECO code format and constraints
        if not stats.eco or not len(stats.eco) == 3:
            errors.append("ECO code must be exactly 3 characters")
            context["eco"] = stats.eco
        elif not stats.eco[0] in 'ABCDE':
            errors.append("ECO code must start with A, B, C, D, or E")
            context["eco_first_char"] = stats.eco[0]
        elif not stats.eco[1:].isdigit():
            errors.append("ECO code must end with two digits")
            context["eco_digits"] = stats.eco[1:]

        # Validate game counts and ensure non-negativity
        if stats.games_played < 0:
            errors.append("Games played cannot be negative")
            context["games_played"] = stats.games_played
        if stats.wins < 0:
            errors.append("Wins cannot be negative")
            context["wins"] = stats.wins
        if stats.losses < 0:
            errors.append("Losses cannot be negative")
            context["losses"] = stats.losses
        if stats.draws < 0:
            errors.append("Draws cannot be negative")
            context["draws"] = stats.draws

        # Validate game count consistency
        total_games = stats.wins + stats.losses + stats.draws
        if total_games != stats.games_played:
            errors.append(
                f"Sum of outcomes ({total_games}) does not match "
                f"games played ({stats.games_played})"
            )
            context["game_count_mismatch"] = {
                "total": total_games,
                "games_played": stats.games_played,
                "breakdown": {
                    "wins": stats.wins,
                    "losses": stats.losses,
                    "draws": stats.draws
                }
            }

        # Validate win rate percentage
        win_rate_result = self._validate_percentage(
            stats.win_rate,
            "win_rate"
        )
        if not win_rate_result.is_valid:
            errors.extend(win_rate_result.errors)
            if win_rate_result.context:
                context.update(win_rate_result.context)

        # Validate win rate calculation accuracy
        if stats.games_played > 0:
            expected_win_rate = (stats.wins / stats.games_played) * 100
            # Allow small floating point differences
            if abs(expected_win_rate - stats.win_rate) > 0.01:
                errors.append("Win rate does not match game outcomes")
                context["win_rate_mismatch"] = {
                    "calculated": expected_win_rate,
                    "provided": stats.win_rate,
                    "difference": abs(expected_win_rate - stats.win_rate)
                }

        # Validate optional performance metrics if present
        if stats.avg_opponent_rating is not None:
            rating_result = self._validate_rating(
                stats.avg_opponent_rating,
                "avg_opponent_rating"
            )
            if not rating_result.is_valid:
                errors.extend(rating_result.errors)
                if rating_result.context:
                    context.update(rating_result.context)

        if stats.performance_rating is not None:
            rating_result = self._validate_rating(
                stats.performance_rating,
                "performance_rating",
                min_rating=1000,  # Reasonable minimum for performance rating
                max_rating=3500   # Allow slightly higher than normal for performance
            )
            if not rating_result.is_valid:
                errors.extend(rating_result.errors)
                if rating_result.context:
                    context.update(rating_result.context)

        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            context=context if context else None
        )

    def validate_complete_analysis(
        self,
        analysis: PlayerAnalysis
    ) -> ValidationResult:
        """
        Validate complete player analysis data holistically.
        
        Performs comprehensive validation of all analysis components:
        - Basic statistics and their consistency
        - Opening repertoire analysis
        - Rating progression data
        - Performance metrics across time periods
        - Cross-validation between different metrics
        
        Args:
            analysis: Complete PlayerAnalysis object to validate
            
        Returns:
            ValidationResult with detailed error information and context
            
        Note:
            This method not only validates individual components but also
            ensures consistency between different aspects of the analysis.
        """
        errors: List[str] = []
        context: Dict[str, Any] = {}

        # Validate overview metrics
        if not self._validate_overview_metrics(
            analysis.overview,
            errors,
            context
        ):
            # Early return if basic metrics are invalid
            return ValidationResult(
                is_valid=False,
                errors=errors,
                context=context
            )

        # Validate rating progression if present
        if analysis.ratings:
            rating_result = self.validate_rating_progression(analysis.ratings)
            if not rating_result.is_valid:
                errors.extend(rating_result.errors)
                if rating_result.context:
                    context["rating_progression"] = rating_result.context

        # Validate opening statistics
        if analysis.openings:
            total_opening_games = sum(
                opening.games_played for opening in analysis.openings
            )
            if total_opening_games > analysis.overview.total_games:
                errors.append(
                    f"Sum of games across openings ({total_opening_games}) "
                    f"exceeds total games ({analysis.overview.total_games})"
                )
                context["opening_games_mismatch"] = {
                    "total_opening_games": total_opening_games,
                    "total_games": analysis.overview.total_games
                }

            # Validate each opening's statistics
            for i, opening in enumerate(analysis.openings):
                opening_result = self.validate_opening_stats(opening)
                if not opening_result.is_valid:
                    errors.extend(
                        f"Opening {i} ({opening.eco}): {error}"
                        for error in opening_result.errors
                    )
                    if opening_result.context:
                        context[f"opening_{i}"] = opening_result.context

        # Validate performance timeline consistency
        if analysis.timeline:
            timeline_result = self._validate_performance_timeline(
                analysis.timeline,
                analysis.overview.total_games
            )
            if not timeline_result.is_valid:
                errors.extend(timeline_result.errors)
                if timeline_result.context:
                    context["timeline"] = timeline_result.context

        # Cross-validate peak ratings
        if (analysis.ratings and analysis.ratings.peak_rating and
            analysis.timeline):
            timeline_peak = max(
                (entry.rating for entry in analysis.timeline 
                if entry.rating is not None),
                default=None
            )
            if (timeline_peak and 
                timeline_peak > analysis.ratings.peak_rating):
                errors.append(
                    "Peak rating inconsistency between overview and timeline"
                )
                context["peak_rating_mismatch"] = {
                    "overview_peak": analysis.ratings.peak_rating,
                    "timeline_peak": timeline_peak
                }

        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            context=context if context else None
        )

    def _validate_overview_metrics(
        self,
        overview: Dict[str, Any],
        errors: List[str],
        context: Dict[str, Any]
    ) -> bool:
        """
        Validate overview metrics for consistency and correctness.
        
        Args:
            overview: Overview metrics dictionary
            errors: List to append errors to
            context: Dictionary to append context to
            
        Returns:
            True if validation passed, False if critical errors found
            
        Note:
            This is a helper method that modifies the provided errors and
            context collections in place.
        """
        try:
            # Validate total games
            if overview["total_games"] < 0:
                errors.append("Total games cannot be negative")
                context["total_games"] = overview["total_games"]
                return False

            # Validate game outcome consistency
            total_outcomes = (
                overview["wins"] +
                overview["draws"] +
                overview["losses"]
            )
            if total_outcomes != overview["total_games"]:
                errors.append(
                    f"Sum of outcomes ({total_outcomes}) does not match "
                    f"total games ({overview['total_games']})"
                )
                context["game_outcomes"] = {
                    "wins": overview["wins"],
                    "draws": overview["draws"],
                    "losses": overview["losses"],
                    "total": total_outcomes,
                    "expected": overview["total_games"]
                }
                return False

            # Validate win rate
            if not (0 <= overview["win_rate"] <= 100):
                errors.append(
                    f"Win rate {overview['win_rate']} is outside valid range"
                )
                context["win_rate"] = overview["win_rate"]
                return False

            # Validate win rate calculation
            expected_win_rate = (
                overview["wins"] / overview["total_games"] * 100
                if overview["total_games"] > 0 else 0.0
            )
            if abs(expected_win_rate - overview["win_rate"]) > 0.01:
                errors.append("Win rate does not match game outcomes")
                context["win_rate_calculation"] = {
                    "expected": expected_win_rate,
                    "actual": overview["win_rate"]
                }
                return False

            return True

        except KeyError as e:
            errors.append(f"Missing required field in overview metrics: {e}")
            context["missing_field"] = str(e)
            return False
        except Exception as e:
            errors.append(f"Error validating overview metrics: {str(e)}")
            context["validation_error"] = str(e)
            return False