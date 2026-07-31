class ApplicationError(Exception):
    """Base exception for all application errors."""
    code: str = "INTERNAL_ERROR"
    status_code: int = 500

    def __init__(self, message: str, details: list = None):
        super().__init__(message)
        self.message = message
        self.details = details or []


class NotFoundError(ApplicationError):
    code = "NOT_FOUND"
    status_code = 404


class ValidationError(ApplicationError):
    code = "VALIDATION_ERROR"
    status_code = 422


class AuthenticationError(ApplicationError):
    code = "AUTHENTICATION_FAILED"
    status_code = 401


class AuthorizationError(ApplicationError):
    code = "ACCESS_DENIED"
    status_code = 403


class ConflictError(ApplicationError):
    code = "RESOURCE_CONFLICT"
    status_code = 409


class DomainError(ApplicationError):
    code = "DOMAIN_ERROR"
    status_code = 400


class InfrastructureError(ApplicationError):
    code = "INFRASTRUCTURE_ERROR"
    status_code = 503


class ExternalServiceError(ApplicationError):
    code = "EXTERNAL_SERVICE_ERROR"
    status_code = 502
