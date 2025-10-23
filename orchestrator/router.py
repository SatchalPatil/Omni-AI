import logging
import re
import json
import os
from dotenv import load_dotenv
from google.generativeai import GenerativeModel, configure
from agents.chat_agent import chat_with_gemini
from agents.sql_agent import sql_agent_node
from agents.email_agent import email_agent_node
from agents.report_agent import report_agent_node

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment and initialize Gemini for intent detection
load_dotenv()
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
GEMINI_MODEL = os.getenv('GEMINI_MODEL', 'gemini-2.0-flash')
if GEMINI_API_KEY:
    configure(api_key=GEMINI_API_KEY)
    intent_model = GenerativeModel(GEMINI_MODEL)
    logger.info(f"Intent detection model initialized: {GEMINI_MODEL}")
else:
    logger.warning("GEMINI_API_KEY not found, intent detection will fail")
    intent_model = None

def detect_intent_with_gemini(user_input: str, state: dict = None) -> dict:
    """
    Use Gemini to intelligently detect user intent and extract parameters.
    
    Args:
        user_input (str): User's message
        state (dict): Current state (email, pdf_path, etc.)
        
    Returns:
        dict: {'intent': str, 'parameters': dict}
    """
    try:
        if not intent_model:
            logger.warning("Intent model not available, using fallback regex")
            return fallback_regex_intent(user_input)
        
        # Build classification prompt
        state_str = json.dumps(state) if state else '{}'
        prompt = (
            f"Classify the intent of the following user input into one of: 'email', 'sql', 'report', 'voice', 'chat', 'download'. "
            f"Extract relevant parameters such as email address, query question, or modification instruction. "
            f"If the input is 'send email' or similar, set 'send_email' to true and use the email from state if available. "
            f"If the input is 'download' or similar, set intent to 'download'. "
            f"Return ONLY a valid JSON object with 'intent' and a 'parameters' dictionary. Do not include any markdown formatting or code blocks. "
            f"Examples:\n"
            f"- Input: 'Draft an email to HR', Output: {{\"intent\": \"email\", \"parameters\": {{\"prompt\": \"Draft an email to HR\"}}}}\\n"
            f"- Input: 'Show me districts and their total annual recharge', Output: {{\"intent\": \"sql\", \"parameters\": {{\"question\": \"Show me districts and their total annual recharge\"}}}}\\n"
            f"- Input: 'Generate report', Output: {{\"intent\": \"report\", \"parameters\": {{\"prompt\": \"Generate report\"}}}}\\n"
            f"- Input: 'Export to PDF', Output: {{\"intent\": \"report\", \"parameters\": {{\"prompt\": \"Export to PDF\"}}}}\\n"
            f"- Input: 'Download report', Output: {{\"intent\": \"report\", \"parameters\": {{\"prompt\": \"Download report\"}}}}\\n"
            f"- Input: 'send email', State: {{\"to_email\": \"test@gmail.com\"}}, Output: {{\"intent\": \"report\", \"parameters\": {{\"send_email\": true, \"to_email\": \"test@gmail.com\"}}}}\\n"
            f"- Input: 'download', State: {{\"pdf_path\": \"reports/report.pdf\"}}, Output: {{\"intent\": \"download\", \"parameters\": {{\"pdf_path\": \"reports/report.pdf\"}}}}\\n"
            f"Input: '{user_input}'\n"
            f"State: {state_str}\n"
        )
        
        logger.info(f"Detecting intent for: {user_input}")
        response = intent_model.generate_content(prompt)
        response_text = response.text.strip()
        
        # Clean up response (remove markdown code blocks if present)
        if response_text.startswith('```json'):
            response_text = response_text[7:]
        if response_text.startswith('```'):
            response_text = response_text[3:]
        if response_text.endswith('```'):
            response_text = response_text[:-3]
        response_text = response_text.strip()
        
        # Parse JSON response
        intent_data = json.loads(response_text)
        logger.info(f"Detected intent: {intent_data}")
        return intent_data
        
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse intent JSON: {response_text}. Error: {str(e)}")
        return fallback_regex_intent(user_input)
    except Exception as e:
        logger.error(f"Intent detection error: {str(e)}", exc_info=True)
        return fallback_regex_intent(user_input)

def fallback_regex_intent(message: str) -> dict:
    """
    Fallback regex-based intent detection if Gemini fails.
    """
    message_lower = message.lower()
    
    # SQL keywords
    if re.search(r'\b(show|get|find|list|total|count|average|sum|district|state|year|recharge|extraction|groundwater|annual|table|database|query|sql|data|chart)\b', message_lower):
        return {'intent': 'sql', 'parameters': {'question': message}}
    
    # Report keywords
    elif re.search(r'\b(report|pdf|generate\s+report)\b', message_lower):
        return {'intent': 'report', 'parameters': {'prompt': message}}
    
    # Email keywords
    elif re.search(r'\b(email|draft|send|mail)\b', message_lower):
        return {'intent': 'email', 'parameters': {'prompt': message}}
    
    # Default to chat
    else:
        return {'intent': 'chat', 'parameters': {}}

def route_message(input_data: dict) -> dict:
    """
    Detect intent using Gemini and route to appropriate agent.
    Phase 4: Enables email and report intent detection.
    
    Args:
        input_data (dict): {'message': str, 'context': list, 'state': dict (optional)}
        
    Returns:
        dict: Response from the selected agent
    """
    try:
        message = input_data.get('message', '')
        context = input_data.get('context', [])
        state = input_data.get('state', {})
        logger.info(f"[Router] Phase 4 - Routing message: {message[:50]}...")

        # Phase 4: Enable intent detection for SQL queries, email, and reports
        intent_result = detect_intent_with_gemini(message, state)
        intent = intent_result.get('intent', 'chat')
        parameters = intent_result.get('parameters', {})
        logger.info(f"[Router] Detected intent: '{intent}' with parameters: {str(parameters)}")

        # Route based on detected intent
        if intent == 'sql':
            logger.info(f"[Router] Routing to SQL agent")
            # Merge parameters into input_data
            sql_input = {'message': parameters.get('question', message), 'context': context}
            response = sql_agent_node(sql_input)
            # Phase 5: Mark SQL responses with pin_option for dashboard
            if response.get('status') == 'success' and ('chart_data' in response or 'data' in response):
                response['pin_option'] = True
                logger.info("[Router] Added pin_option to SQL response")
            return response
        
        elif intent == 'email':
            logger.info(f"[Router] Routing to Email agent")
            # Merge parameters into input_data for email agent
            email_input = {
                'prompt': parameters.get('prompt', message),
                'to_email': parameters.get('to_email', ''),
                'send_email': parameters.get('send_email', False),
                'attachment_path': parameters.get('attachment_path')
            }
            return email_agent_node(email_input)
        
        elif intent == 'report':
            logger.info(f"[Router] Routing to Report agent")
            # Merge parameters into input_data for report agent
            report_input = {
                'prompt': parameters.get('prompt', message),
                'confirm': parameters.get('confirm', False)
            }
            return report_agent_node(report_input)
        
        elif intent == 'download':
            logger.info("[Router] Download functionality not yet implemented")
            return {'status': 'error', 'error': 'Download not implemented yet'}
        
        else:  # intent == 'chat' or unknown
            logger.info(f"[Router] Routing to chat agent")
            return chat_with_gemini(message, context)

    except Exception as e:
        logger.error(f"[Router] Error in route_message: {str(e)}")
        return {'status': 'error', 'error': str(e)}
