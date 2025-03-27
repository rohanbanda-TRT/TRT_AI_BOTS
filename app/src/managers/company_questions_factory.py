import logging
from functools import lru_cache
from ..core.config import get_settings
from .company_questions_manager import CompanyQuestionsManager

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@lru_cache()
def get_company_questions_manager():
    """
    Factory function to get the company questions manager
    
    Returns:
        CompanyQuestionsManager
    """
    logger.info("Using MongoDB for company questions storage")
    return CompanyQuestionsManager()
