"""
Centralized error handling utilities for SyrHousing backend.
"""

from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from pydantic import ValidationError
from typing import Union, Dict, Any
import traceback

from .logging import get_logger

logger = get_logger()


class SyrHousingException(Exception):
    """Base exception for SyrHousing application."""

    def __init__(self, message: str, status_code: int = 500, details: Dict[str, Any] = None):
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class DatabaseError(SyrHousingException):
    """Database operation error."""

    def __init__(self, message: str = "Database operation failed", details: Dict[str, Any] = None):
        super().__init__(message, status_code=500, details=details)


class NotFoundError(SyrHousingException):
    """Resource not found error."""

    def __init__(self, resource: str, identifier: str = None):
        message = f"{resource} not found"
        if identifier:
            message += f": {identifier}"
        super().__init__(message, status_code=404)


class ValidationException(SyrHousingException):
    """Data validation error."""

    def __init__(self, message: str = "Validation failed", details: Dict[str, Any] = None):
        super().__init__(message, status_code=422, details=details)


class AuthorizationError(SyrHousingException):
    """Authorization error."""

    def __init__(self, message: str = "Not authorized to perform this action"):
        super().__init__(message, status_code=403)


class ExternalServiceError(SyrHousingException):
    """External service call error."""

    def __init__(self, service: str, message: str = None):
        msg = f"External service error: {service}"
        if message:
            msg += f" - {message}"
        super().__init__(msg, status_code=502)


async def syrhousing_exception_handler(request: Request, exc: SyrHousingException) -> JSONResponse:
    """Handle SyrHousing custom exceptions."""
    logger.error(
        f"SyrHousing Exception: {exc.message}",
        extra={
            "status_code": exc.status_code,
            "details": exc.details,
            "path": request.url.path,
            "method": request.method,
        }
    )

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.message,
            "details": exc.details,
        }
    )


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Handle FastAPI HTTP exceptions."""
    logger.error(
        f"HTTP Exception: {exc.detail}",
        extra={
            "status_code": exc.status_code,
            "path": request.url.path,
            "method": request.method,
        }
    )

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
        }
    )


async def validation_exception_handler(request: Request, exc: ValidationError) -> JSONResponse:
    """Handle Pydantic validation errors."""
    errors = exc.errors()
    logger.warning(
        f"Validation Error: {len(errors)} validation error(s)",
        extra={
            "errors": errors,
            "path": request.url.path,
            "method": request.method,
        }
    )

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "Validation failed",
            "details": errors,
        }
    )


async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError) -> JSONResponse:
    """Handle SQLAlchemy database errors."""
    logger.error(
        f"Database Error: {str(exc)}",
        extra={
            "exception_type": type(exc).__name__,
            "path": request.url.path,
            "method": request.method,
        },
        exc_info=True
    )

    # Handle specific database errors
    if isinstance(exc, IntegrityError):
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={
                "error": "Database constraint violation",
                "details": "The operation conflicts with existing data.",
            }
        )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Database operation failed",
            "details": "An error occurred while accessing the database.",
        }
    )


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle all other uncaught exceptions."""
    logger.error(
        f"Unhandled Exception: {str(exc)}",
        extra={
            "exception_type": type(exc).__name__,
            "path": request.url.path,
            "method": request.method,
            "traceback": traceback.format_exc(),
        },
        exc_info=True
    )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal server error",
            "details": "An unexpected error occurred. Please try again later.",
        }
    )


def safe_execute(func, *args, default=None, log_error=True, context="", **kwargs):
    """
    Safely execute a function with error handling.

    Args:
        func: Function to execute
        *args: Positional arguments for the function
        default: Default value to return on error
        log_error: Whether to log errors
        context: Context description for logging
        **kwargs: Keyword arguments for the function

    Returns:
        Function result or default value on error
    """
    try:
        return func(*args, **kwargs)
    except Exception as e:
        if log_error:
            logger.error(
                f"Error in safe_execute ({context}): {type(e).__name__}: {str(e)}",
                exc_info=True
            )
        return default


def register_exception_handlers(app):
    """
    Register all exception handlers with the FastAPI app.

    Args:
        app: FastAPI application instance
    """
    app.add_exception_handler(SyrHousingException, syrhousing_exception_handler)
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(ValidationError, validation_exception_handler)
    app.add_exception_handler(SQLAlchemyError, sqlalchemy_exception_handler)
    app.add_exception_handler(Exception, general_exception_handler)

    logger.info("Exception handlers registered")
