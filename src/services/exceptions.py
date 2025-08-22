"""
Custom exceptions for coffee brewing services
"""


class CoffeeServiceError(Exception):
    """Base exception for coffee brewing services"""
    
    def __init__(self, message: str, service: str = None, details: dict = None):
        self.service = service
        self.details = details or {}
        super().__init__(message)


class DataValidationError(CoffeeServiceError):
    """Raised when data validation fails"""
    pass


class DataLoadError(CoffeeServiceError):
    """Raised when data loading fails"""
    pass


class DataSaveError(CoffeeServiceError):
    """Raised when data saving fails"""
    pass


class ProcessingError(CoffeeServiceError):
    """Raised when post-processing fails"""
    pass


class VisualizationError(CoffeeServiceError):
    """Raised when chart creation fails"""
    pass


class ConfigurationError(CoffeeServiceError):
    """Raised when configuration is invalid"""
    pass


class SecurityError(CoffeeServiceError):
    """Raised when security validation fails"""
    pass