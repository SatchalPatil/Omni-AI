import os
import logging
from google.generativeai import GenerativeModel, configure
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load .env file
load_dotenv()
logger.info("[EmailAgent] Loaded .env file")

# Initialize Gemini
try:
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
    GEMINI_MODEL = os.getenv('GEMINI_MODEL', 'gemini-2.0-flash')
    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY not found in .env")
    configure(api_key=GEMINI_API_KEY)
    model = GenerativeModel(GEMINI_MODEL)
    logger.info(f"[EmailAgent] Gemini initialized with model: {GEMINI_MODEL}")
except Exception as e:
    logger.error(f"[EmailAgent] Failed to initialize Gemini: {str(e)}")
    raise

def generate_email_draft(prompt: str) -> dict:
    """
    Generate a well-structured email draft using Gemini.
    Phase 3: Email automation with LLM-powered drafting.
    
    Args:
        prompt (str): User's description of the email to create
        
    Returns:
        dict: {'subject': str, 'body': str, 'to_email': str or None}
    """
    logger.info(f"[EmailAgent] Generating email draft for: {prompt[:50]}...")
    
    structured_prompt = (
        "You are an AI email assistant. Your task is to generate a well-structured and professional email based on the user's input.\n\n"
        "STRICT FORMATTING REQUIREMENTS:\n"
        "1. You MUST use EXACTLY this format with line breaks:\n"
        "   Subject: <email subject>\n"
        "   To: <recipient email if mentioned, otherwise 'Not specified'>\n"
        "   Body:\n"
        "   <email body>\n\n"
        "2. The subject line should be clear and concise (under 10 words).\n"
        "3. The To: line should contain ONLY the email address or 'Not specified'.\n"
        "4. The Body: should be on its own line, followed by the email content.\n"
        "5. Use proper greeting, main content, and closing in the body.\n"
        "6. Use formal language for professional emails, friendly tone for casual ones.\n"
        "7. Do NOT add any extra text before 'Subject:' or after the email body.\n\n"
        "Example Output:\n"
        "Subject: Project Status Update\n"
        "To: Not specified\n"
        "Body:\n"
        "Dear Manager,\n\nI wanted to provide you with an update on the current project status...\n\nBest regards,\n[Your Name]\n\n"
        "User Input:\n"
        f"{prompt}\n\n"
        "Now generate the email:"
    )
    
    try:
        response = model.generate_content(structured_prompt)
        email_content = response.text.strip()
        logger.info(f"[EmailAgent] Email draft generated ({len(email_content)} chars)")
        logger.debug(f"[EmailAgent] Raw response: {email_content[:200]}...")
        
        # Parse the response with improved logic
        subject = "No Subject"
        to_email = None
        body = ""
        
        lines = email_content.split('\n')
        body_started = False
        body_lines = []
        
        for line in lines:
            if line.startswith("Subject:"):
                subject = line.replace("Subject:", "", 1).strip()
            elif line.startswith("To:"):
                to_line = line.replace("To:", "", 1).strip()
                if to_line and to_line.lower() != "not specified" and "@" in to_line:
                    to_email = to_line
            elif line.startswith("Body:"):
                body_started = True
                # Check if body content is on the same line
                body_content = line.replace("Body:", "", 1).strip()
                if body_content:
                    body_lines.append(body_content)
            elif body_started:
                body_lines.append(line)
        
        body = '\n'.join(body_lines).strip()
        
        # Fallback: if parsing failed, try to extract body after "Body:"
        if not body and "Body:" in email_content:
            body = email_content.split("Body:", 1)[1].strip()
        
        # Final fallback: use entire content as body if still empty
        if not body:
            body = email_content
        
        logger.info(f"[EmailAgent] Parsed - Subject: '{subject}', To: '{to_email or 'Not specified'}', Body length: {len(body)}")
        
        return {
            'subject': subject,
            'body': body,
            'to_email': to_email
        }
        
    except Exception as e:
        logger.error(f"[EmailAgent] Error generating email draft: {str(e)}")
        return {
            'subject': "Error",
            'body': f"Failed to generate email: {str(e)}",
            'to_email': None
        }

def modify_email_draft(original_draft: dict, suggestions: str) -> dict:
    """
    Modify an existing email draft based on user suggestions.
    Phase 3: Email modification with Gemini.
    
    Args:
        original_draft (dict): Original draft with subject, body, to_email
        suggestions (str): User's modification requests
        
    Returns:
        dict: Updated draft {'subject': str, 'body': str, 'to_email': str or None}
    """
    logger.info(f"[EmailAgent] Modifying email draft with suggestions: {suggestions[:50]}...")
    
    original_email = f"Subject: {original_draft.get('subject', 'No Subject')}\n"
    if original_draft.get('to_email'):
        original_email += f"To: {original_draft['to_email']}\n"
    original_email += f"Body:\n{original_draft.get('body', '')}"
    
    structured_prompt = (
        "You are an AI email assistant. The following is the current version of an email:\n\n"
        f"{original_email}\n\n"
        "The user has suggested the following changes:\n"
        f"{suggestions}\n\n"
        "Please modify the email accordingly. Maintain the same format:\n"
        "Subject: <email subject>\n"
        "To: <recipient email or keep original if not changed>\n"
        "Body:\n"
        "<email body>"
    )
    
    try:
        response = model.generate_content(structured_prompt)
        new_email_content = response.text.strip()
        logger.info(f"[EmailAgent] Email modified ({len(new_email_content)} chars)")
        
        # Parse the modified email
        subject = original_draft.get('subject', 'No Subject')
        to_email = original_draft.get('to_email')
        body = new_email_content
        
        if "Subject:" in new_email_content:
            subject_part = new_email_content.split("Subject:", 1)[1]
            if "To:" in subject_part:
                subject = subject_part.split("To:", 1)[0].strip()
                to_part = subject_part.split("To:", 1)[1]
                if "Body:" in to_part:
                    to_line = to_part.split("Body:", 1)[0].strip()
                    body = to_part.split("Body:", 1)[1].strip()
                    if to_line and to_line.lower() != "not specified" and "@" in to_line:
                        to_email = to_line.strip()
                else:
                    to_line = to_part.strip()
                    if to_line and to_line.lower() != "not specified" and "@" in to_line:
                        to_email = to_line.strip()
            elif "Body:" in subject_part:
                subject = subject_part.split("Body:", 1)[0].strip()
                body = subject_part.split("Body:", 1)[1].strip()
        
        logger.info(f"[EmailAgent] Modified - Subject: '{subject}', To: '{to_email}'")
        
        return {
            'subject': subject,
            'body': body,
            'to_email': to_email
        }
        
    except Exception as e:
        logger.error(f"[EmailAgent] Error modifying email: {str(e)}")
        return original_draft

def email_agent_node(input_data: dict) -> dict:
    """
    Handle email drafting requests from orchestrator.
    Phase 3: Email automation node for LangGraph.
    
    Args:
        input_data (dict): {'prompt': str, 'to_email': str (optional), 'send_email': bool (optional)}
        
    Returns:
        dict: {
            'status': 'success'/'error',
            'text': str,
            'draft': {'subject': str, 'body': str, 'to_email': str},
            'action': 'draft'/'send'
        }
    """
    try:
        prompt = input_data.get('prompt', '')
        to_email_override = input_data.get('to_email', '')
        send_email = input_data.get('send_email', False)
        
        logger.info(f"[EmailAgent] Phase 3 - Processing email request: {prompt[:50]}...")
        logger.info(f"[EmailAgent] Send immediately: {send_email}, Override recipient: {to_email_override}")
        
        # Generate draft
        draft = generate_email_draft(prompt)
        
        # Override recipient if provided
        if to_email_override:
            draft['to_email'] = to_email_override
            logger.info(f"[EmailAgent] Recipient overridden to: {to_email_override}")
        
        # Build response
        text_response = f"📧 Email Draft Generated:\n\n"
        text_response += f"**Subject:** {draft['subject']}\n"
        text_response += f"**To:** {draft['to_email'] or 'Not specified'}\n\n"
        text_response += f"**Body:**\n{draft['body'][:200]}..."
        
        response = {
            'status': 'success',
            'text': text_response,
            'draft': draft,
            'action': 'send' if send_email else 'draft'
        }
        
        logger.info(f"[EmailAgent] Email draft created - Subject: '{draft['subject']}'")
        
        return response
        
    except Exception as e:
        logger.error(f"[EmailAgent] Error: {str(e)}")
        return {
            'status': 'error',
            'error': f'Email agent error: {str(e)}',
            'text': 'Failed to generate email draft.'
        }
