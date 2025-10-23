import os
import logging
from google.generativeai import GenerativeModel, configure
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load .env file
load_dotenv()
logger.info("Loaded .env file in chat_agent.py")

# Initialize Gemini
try:
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
    GEMINI_MODEL = os.getenv('GEMINI_MODEL', 'gemini-2.0-flash')
    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY not found in .env")
    configure(api_key=GEMINI_API_KEY)
    model = GenerativeModel(GEMINI_MODEL)
    logger.info(f"Gemini initialized with model: {GEMINI_MODEL}")
except Exception as e:
    logger.error(f"Failed to initialize Gemini: {str(e)}")
    raise

def chat_with_gemini(message: str, context: list) -> dict:
    """
    Handle general conversation using Gemini API with context.
    
    Args:
        message (str): User input message
        context (list): List of previous messages for context
        
    Returns:
        dict: {'status': 'success', 'text': response} or {'status': 'error', 'error': message}
    """
    try:
        logger.info(f"Processing chat message: {message}")
        # Format context for Gemini (alternating user/assistant messages)
        prompt = ""
        for entry in context:
            role = 'user' if entry.get('role') == 'user' else 'model'
            prompt += f"{role}: {entry.get('content')}\n"
        prompt += f"user: {message}"

        response = model.generate_content(prompt)
        response_text = response.text.strip()

        logger.info(f"Gemini response: {response_text[:50]}...")
        return {'status': 'success', 'text': response_text}
    except Exception as e:
        logger.error(f"Error in chat_with_gemini: {str(e)}")
        return {'status': 'error', 'error': str(e)}