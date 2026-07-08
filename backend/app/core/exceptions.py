"""
CloudWise AI - Custom Exceptions
Domain-specific exception classes with HTTP status code mapping.
"""

from fastapi import HTTPException, status


class CloudWiseException(Exception):
    """Base exception for CloudWise application."""

    def __init__(
        self, message: str = "An error occurred", code: str = "INTERNAL_ERROR"
    ):
        self.message = message
        self.code = code
        super().__init__(self.message)


class EntityNotFoundError(CloudWiseException):
    """Raised when a requested entity does not exist."""

    def __init__(self, entity: str, entity_id: str):
        super().__init__(
            message=f"{entity} with id '{entity_id}' not found",
            code="NOT_FOUND",
        )
        self.entity = entity
        self.entity_id = entity_id


class DuplicateEntityError(CloudWiseException):
    """Raised when attempting to create a duplicate entity."""

    def __init__(self, entity: str, field: str, value: str):
        super().__init__(
            message=f"{entity} with {field} '{value}' already exists",
            code="DUPLICATE",
        )


class AuthenticationError(CloudWiseException):
    """Raised on authentication failures."""

    def __init__(self, message: str = "Invalid credentials"):
        super().__init__(message=message, code="AUTH_FAILED")


class AuthorizationError(CloudWiseException):
    """Raised when user lacks required permissions."""

    def __init__(self, message: str = "Insufficient permissions"):
        super().__init__(message=message, code="FORBIDDEN")


class AWSIntegrationError(CloudWiseException):
    """Raised when an AWS API call fails."""

    def __init__(self, service: str, message: str):
        super().__init__(
            message=f"AWS {service} error: {message}",
            code="AWS_ERROR",
        )


class ValidationError(CloudWiseException):
    """Raised on business logic validation failures."""

    def __init__(self, message: str):
        super().__init__(message=message, code="VALIDATION_ERROR")


class AIServiceError(CloudWiseException):
    """Raised when AI/ML service encounters an error."""

    def __init__(self, message: str = "AI service unavailable"):
        super().__init__(message=message, code="AI_ERROR")


# --- HTTP Exception Factories ---


def not_found(entity: str, entity_id: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"{entity} with id '{entity_id}' not found",
    )


def unauthorized(message: str = "Not authenticated") -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=message,
        headers={"WWW-Authenticate": "Bearer"},
    )


def forbidden(message: str = "Insufficient permissions") -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail=message,
    )


def bad_request(message: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=message,
    )
