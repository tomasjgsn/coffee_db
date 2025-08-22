"""
Base classes for services to ensure consistent interfaces and logging
"""

from abc import ABC, abstractmethod
import logging
from typing import Any


class BaseService(ABC):
    """Abstract base class for all services"""
    
    def __init__(self):
        self.logger = self._setup_logging()
    
    def _setup_logging(self) -> logging.Logger:
        """Setup standardized logging configuration"""
        logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        return logger


class DataServiceInterface(ABC):
    """Interface for data management services"""
    
    @abstractmethod
    def load_data(self):
        """Load data from storage"""
        pass
    
    @abstractmethod
    def save_data(self, data: Any) -> bool:
        """Save data to storage"""
        pass
    
    @abstractmethod
    def validate_dataframe(self, df: Any) -> list:
        """Validate data integrity"""
        pass


class ProcessingServiceInterface(ABC):
    """Interface for data processing services"""
    
    @abstractmethod
    def process_data(self, data: Any) -> Any:
        """Process data according to business rules"""
        pass


class VisualizationServiceInterface(ABC):
    """Interface for visualization services"""
    
    @abstractmethod
    def create_chart(self, data: Any, **kwargs) -> Any:
        """Create visualization from data"""
        pass
    
    @abstractmethod
    def prepare_chart_data(self, data: Any, **kwargs) -> Any:
        """Prepare data for visualization"""
        pass