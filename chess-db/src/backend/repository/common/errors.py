# repository/common/errors.py
from typing import Optional, Any

class RepositoryError(Exception):
    """Base exception class for repository errors."""
    pass

class DatabaseOperationError(RepositoryError):
    """Raised when a database operation fails."""
    def __init__(self, message: str, cause: Optional[Exception] = None):
        super().__init__(message)
        self.cause = cause

class ValidationError(RepositoryError):
    """Raised when data validation fails."""
    def __init__(self, message: str, field: Optional[str] = None):
        super().__init__(message)
        self.field = field

class ResourceNotFoundError(RepositoryError):
    """Raised when a requested resource is not found."""
    def __init__(self, resource_type: str, identifier: Any):
        message = f"{resource_type} with identifier {identifier} not found"
        super().__init__(message)
        self.resource_type = resource_type
        self.identifier = identifier

class EntityNotFoundError(ResourceNotFoundError):
    """Raised when an entity is not found in the database."""
    def __init__(self, entity_type: str, identifier: Any):
        super().__init__(entity_type, identifier)
        self.entity_type = entity_type
        self.identifier = identifier

class ConcurrencyError(RepositoryError):
    """Raised when concurrent operations conflict."""
    pass
