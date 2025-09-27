import google.generativeai as genai
import logging
from typing import Tuple

logger = logging.getLogger(__name__)


def validate_gemini_api_key(api_key: str) -> Tuple[bool, str]:
    """
    Validate a Gemini API key by making a test request.
    
    Args:
        api_key (str): The API key to validate
        
    Returns:
        Tuple[bool, str]: (is_valid, message)
    """
    if not api_key or not api_key.strip():
        return False, "API key cannot be empty"
    
    # Basic format validation
    if len(api_key) < 20 or not api_key.startswith('AI'):
        return False, "Invalid API key format"
    
    try:
        # Configure with the provided API key
        genai.configure(api_key=api_key)
        
        # Create a model instance
        model = genai.GenerativeModel('gemini-2.5-flash')
        
        # Make a simple test request
        response = model.generate_content("Say 'API key is valid' if you can read this.")
        
        # Check if we got a valid response
        if response and response.text and "valid" in response.text.lower():
            return True, "API key is valid and working"
        else:
            return False, "API key responded but with unexpected content"
            
    except Exception as e:
        error_msg = str(e).lower()
        if "api key" in error_msg and "invalid" in error_msg:
            return False, "Invalid API key"
        elif "quota" in error_msg or "limit" in error_msg:
            return False, "API key quota exceeded"
        elif "permission" in error_msg:
            return False, "API key lacks required permissions"
        else:
            logger.exception(f"Unexpected error validating API key: {e}")
            return False, f"Validation failed: {str(e)}"
