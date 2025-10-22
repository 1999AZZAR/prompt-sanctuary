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
        return False, "Invalid API key format. Gemini API keys should start with 'AI' and be at least 20 characters long."
    
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
            return False, "Invalid API key. Please check your key and try again."
        elif "quota" in error_msg or "limit" in error_msg:
            return False, "API key quota exceeded. Please check your usage limits."
        elif "permission" in error_msg:
            return False, "API key lacks required permissions. Please ensure your key has Gemini API access."
        elif "billing" in error_msg:
            return False, "Billing account required. Please set up billing for your Google Cloud project."
        elif "region" in error_msg:
            return False, "API not available in your region. Please check Gemini API availability."
        else:
            logger.exception(f"Unexpected error validating API key: {e}")
            return False, f"Validation failed: {str(e)}"


def test_api_key_quota(api_key: str) -> Tuple[bool, str]:
    """
    Test if the API key has available quota for making requests.
    
    Args:
        api_key (str): The API key to test
        
    Returns:
        Tuple[bool, str]: (has_quota, message)
    """
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.5-flash')
        
        # Make a minimal test request
        response = model.generate_content("Test")
        
        if response and response.text:
            return True, "API key has available quota"
        else:
            return False, "API key quota may be exhausted"
            
    except Exception as e:
        error_msg = str(e).lower()
        if "quota" in error_msg or "limit" in error_msg:
            return False, "API key quota exceeded"
        else:
            return False, f"Quota check failed: {str(e)}"


def get_api_key_info(api_key: str) -> dict:
    """
    Get information about the API key (quota, permissions, etc.).
    
    Args:
        api_key (str): The API key to analyze
        
    Returns:
        dict: Information about the API key
    """
    info = {
        'is_valid': False,
        'has_quota': False,
        'model_available': False,
        'error_message': None
    }
    
    try:
        # Test basic validation
        is_valid, message = validate_gemini_api_key(api_key)
        info['is_valid'] = is_valid
        if not is_valid:
            info['error_message'] = message
            return info
        
        # Test quota
        has_quota, quota_message = test_api_key_quota(api_key)
        info['has_quota'] = has_quota
        if not has_quota:
            info['error_message'] = quota_message
            return info
        
        # Test model availability
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.5-flash')
        response = model.generate_content("Hello")
        
        if response and response.text:
            info['model_available'] = True
            info['error_message'] = None
        else:
            info['error_message'] = "Model not responding properly"
            
    except Exception as e:
        info['error_message'] = f"API key analysis failed: {str(e)}"
    
    return info
