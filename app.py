import os
import logging
from flask import Flask, request, jsonify , render_template
from dotenv import load_dotenv
from orchestrator.router import route_message
from elevenlabs.client import ElevenLabs
from elevenlabs.play import play
from io import BytesIO

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)

# Load .env file
load_dotenv()
logger.info("Loaded .env file in app.py")

# Initialize Vanna at startup (only in main process, not reloader)
if os.environ.get('WERKZEUG_RUN_MAIN') == 'true' or not app.debug:
    logger.info("Initializing Vanna and connecting to database...")
    try:
        from agents.sql_agent import initialize_vanna
        initialize_vanna()
        logger.info("✅ Vanna initialized and trained successfully")
    except Exception as e:
        logger.error(f"⚠️ Failed to initialize Vanna: {str(e)}")
        logger.warning("SQL agent will attempt to initialize on first query")
else:
    logger.info("Skipping Vanna initialization in reloader parent process")

# Initialize ElevenLabs client
ELEVENLABS_API_KEY = os.getenv('ELEVENLABS_API_KEY')
if not ELEVENLABS_API_KEY:
    logger.error("ELEVENLABS_API_KEY not found in .env")
    raise ValueError("ELEVENLABS_API_KEY is required")

try:
    elevenlabs = ElevenLabs(api_key=ELEVENLABS_API_KEY)
    logger.info("ElevenLabs client initialized")
except Exception as e:
    logger.error(f"Failed to initialize ElevenLabs client: {str(e)}")
    raise

@app.route('/', methods=['GET'])
def index():
    """
    Serve the chat interface.
    """
    try:
        logger.info("Serving index.html for root URL")
        return render_template('index.html')  # Use render_template for templates/
    except Exception as e:
        logger.error(f"Error serving index.html: {str(e)}")
        return jsonify({'status': 'error', 'error': str(e)}), 500

@app.route('/chat', methods=['POST'])
def chat():
    """
    Handle text-based chat input, route to appropriate agent, and return response.
    Phase 1: All messages route to chat agent.
    """
    try:
        data = request.get_json()
        message = data.get('message', '')
        context = data.get('context', [])
        enable_tts = data.get('enable_tts', False)  # Only generate TTS if explicitly requested
        logger.info(f"[/chat] Received message: {message[:50]}... (TTS: {enable_tts}, Context size: {len(context)})")

        if not message:
            logger.error("[/chat] No message provided")
            return jsonify({'status': 'error', 'error': 'Message is required'}), 400

        # Route message using orchestrator (Phase 1: all to chat agent)
        logger.info("[/chat] Routing message to orchestrator")
        response = route_message({'message': message, 'context': context})
        logger.info(f"[/chat] Response status: {response.get('status')}")

        # If response is successful and has text, generate TTS only if requested
        if response.get('status') == 'success' and 'text' in response and enable_tts:
            logger.info("[/chat] Generating TTS audio")
            audio_url = generate_tts(response['text'])
            if audio_url:
                response['audio_url'] = audio_url
                logger.info(f"[/chat] TTS audio URL: {audio_url}")
            else:
                logger.warning("[/chat] TTS generation failed")

        logger.info(f"[/chat] Returning response (text length: {len(response.get('text', ''))})")
        return jsonify(response)
    except Exception as e:
        logger.error(f"[/chat] Error: {str(e)}")
        return jsonify({'status': 'error', 'error': str(e)}), 500

@app.route('/stt', methods=['POST'])
def speech_to_text():
    """
    Convert audio to text using ElevenLabs STT.
    Phase 1: Supports voice input for chat.
    """
    try:
        if 'audio' not in request.files:
            logger.error("[/stt] No audio file provided")
            return jsonify({'status': 'error', 'error': 'Audio file is required'}), 400

        audio_file = request.files['audio']
        logger.info(f"[/stt] Received audio file: {audio_file.filename}, MIME: {audio_file.mimetype}, Size: {audio_file.content_length} bytes")

        # Convert audio to text using ElevenLabs SDK
        logger.info("[/stt] Sending audio to ElevenLabs for transcription")
        result = elevenlabs.speech_to_text.convert(
            model_id="scribe_v1",
            file=(audio_file.filename, audio_file.read(), audio_file.content_type)
        )
        
        # Extract text from response
        text = result.text if hasattr(result, 'text') else str(result)
        logger.info(f"[/stt] Transcription successful: {text}")

        return jsonify({'status': 'success', 'text': text})
    except Exception as e:
        logger.error(f"[/stt] Error: {str(e)}")
        return jsonify({'status': 'error', 'error': str(e)}), 500

@app.route('/send_email', methods=['POST'])
def send_email_route():
    """
    Send an email draft with optional attachments. Phase 3: Email automation endpoint.
    """
    try:
        logger.info("[/send_email] ========== EMAIL SEND REQUEST RECEIVED ==========")
        data = request.get_json()
        logger.info(f"[/send_email] Request data: {data}")
        
        to_email = data.get('to_email', '')
        subject = data.get('subject', '')
        body = data.get('body', '')
        attachments = data.get('attachments', [])  # List of file paths
        
        logger.info(f"[/send_email] To: {to_email}")
        logger.info(f"[/send_email] Subject: {subject}")
        logger.info(f"[/send_email] Body length: {len(body)}")
        logger.info(f"[/send_email] Attachments: {attachments}")
        
        if not to_email or not subject or not body:
            logger.error("[/send_email] Missing required fields")
            return jsonify({'status': 'error', 'error': 'Missing required fields'}), 400
        
        # Import send_email from utils
        logger.info("[/send_email] Importing email utils...")
        from utils.email_utils import send_email
        
        # Send email with attachments
        logger.info("[/send_email] Calling send_email function...")
        success = send_email(to_email, subject, body, attachments if attachments else None)
        logger.info(f"[/send_email] send_email returned: {success}")
        
        if success:
            logger.info(f"[/send_email] Email sent successfully to {to_email}")
            return jsonify({'status': 'success', 'message': 'Email sent successfully'})
        else:
            logger.error(f"[/send_email] Failed to send email to {to_email}")
            return jsonify({'status': 'error', 'error': 'Failed to send email'}), 500
            
    except Exception as e:
        logger.error(f"[/send_email] Exception occurred: {str(e)}")
        import traceback
        logger.error(f"[/send_email] Traceback: {traceback.format_exc()}")
        return jsonify({'status': 'error', 'error': str(e)}), 500

@app.route('/modify_email', methods=['POST'])
def modify_email_route():
    """
    Modify an email draft using AI. Phase 3: AI-powered email modification.
    """
    try:
        data = request.get_json()
        original_draft = data.get('draft', {})
        modifications = data.get('modifications', '')
        
        logger.info(f"[/modify_email] Modifying draft with: {modifications[:50]}...")
        
        if not original_draft or not modifications:
            logger.error("[/modify_email] Missing required fields")
            return jsonify({'status': 'error', 'error': 'Missing draft or modifications'}), 400
        
        # Import modify function from email agent
        from agents.email_agent import modify_email_draft
        
        # Modify the draft
        modified_draft = modify_email_draft(original_draft, modifications)
        
        logger.info(f"[/modify_email] Draft modified - New subject: {modified_draft['subject']}")
        
        return jsonify({
            'status': 'success',
            'draft': modified_draft,
            'message': 'Email draft modified successfully'
        })
            
    except Exception as e:
        logger.error(f"[/modify_email] Error: {str(e)}")
        return jsonify({'status': 'error', 'error': str(e)}), 500

@app.route('/generate_report', methods=['POST'])
def generate_report_route():
    """
    Generate PDF report from last SQL query.
    Phase 4: Report generation endpoint.
    """
    try:
        data = request.get_json()
        confirm = data.get('confirm', False)
        title = data.get('title', 'Data Report')
        
        logger.info(f"[/generate_report] Confirm: {confirm}, Title: {title[:30]}...")
        
        # Import report agent
        from agents.report_agent import report_agent_node
        
        # Call report agent
        result = report_agent_node({'prompt': title, 'confirm': confirm})
        
        logger.info(f"[/generate_report] Result status: {result.get('status')}")
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"[/generate_report] Error: {str(e)}")
        return jsonify({'status': 'error', 'error': str(e)}), 500

@app.route('/download_report/<path:filename>', methods=['GET'])
def download_report(filename):
    """
    Download generated PDF report.
    Phase 4: Report download endpoint.
    """
    try:
        from flask import send_file
        
        logger.info(f"[/download_report] Downloading: {filename}")
        
        # Security: Only allow files from reports directory
        if '..' in filename or filename.startswith('/'):
            return jsonify({'error': 'Invalid filename'}), 400
        
        filepath = os.path.join('reports', filename)
        
        if not os.path.exists(filepath):
            return jsonify({'error': 'File not found'}), 404
        
        return send_file(filepath, as_attachment=True)
        
    except Exception as e:
        logger.error(f"[/download_report] Error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/upload_docs', methods=['POST'])
def upload_docs():
    """
    Upload documents (PDF, DOCX, TXT) in chat section.
    Files are stored in uploads/ directory.
    """
    try:
        if 'file' not in request.files:
            logger.error("[/upload_docs] No file provided")
            return jsonify({'status': 'error', 'error': 'No file provided'}), 400
        
        file = request.files['file']
        
        if file.filename == '':
            logger.error("[/upload_docs] Empty filename")
            return jsonify({'status': 'error', 'error': 'Empty filename'}), 400
        
        # Validate file type
        allowed_extensions = {'.pdf', '.docx', '.txt', '.doc'}
        file_ext = os.path.splitext(file.filename)[1].lower()
        
        if file_ext not in allowed_extensions:
            logger.error(f"[/upload_docs] Invalid file type: {file_ext}")
            return jsonify({'status': 'error', 'error': f'Only PDF, DOCX, and TXT files allowed'}), 400
        
        # Create uploads directory if it doesn't exist
        uploads_dir = 'uploads'
        os.makedirs(uploads_dir, exist_ok=True)
        
        # Save file with unique name to avoid conflicts
        from werkzeug.utils import secure_filename
        import time
        timestamp = int(time.time())
        safe_filename = secure_filename(file.filename)
        unique_filename = f"{timestamp}_{safe_filename}"
        filepath = os.path.join(uploads_dir, unique_filename)
        
        file.save(filepath)
        logger.info(f"[/upload_docs] File uploaded: {filepath}")
        
        return jsonify({
            'status': 'success',
            'message': 'File uploaded successfully',
            'filename': unique_filename,
            'filepath': filepath
        })
        
    except Exception as e:
        logger.error(f"[/upload_docs] Error: {str(e)}")
        return jsonify({'status': 'error', 'error': str(e)}), 500

@app.route('/email_report', methods=['POST'])
def email_report():
    """
    Send generated PDF report via email.
    Accepts report filename and email details.
    """
    try:
        data = request.get_json()
        to_email = data.get('to_email', '')
        subject = data.get('subject', 'Your Data Report')
        body = data.get('body', 'Please find the attached report.')
        filename = data.get('filename', '')
        
        logger.info(f"[/email_report] Emailing report {filename} to: {to_email}")
        
        if not to_email or not filename:
            logger.error("[/email_report] Missing required fields")
            return jsonify({'status': 'error', 'error': 'Email and filename required'}), 400
        
        # Security: Only allow files from reports directory
        if '..' in filename or filename.startswith('/'):
            return jsonify({'status': 'error', 'error': 'Invalid filename'}), 400
        
        filepath = os.path.join('reports', filename)
        
        if not os.path.exists(filepath):
            logger.error(f"[/email_report] Report not found: {filepath}")
            return jsonify({'status': 'error', 'error': 'Report not found'}), 404
        
        # Import send_email from utils
        from utils.email_utils import send_email
        
        # Send email with report attachment
        success = send_email(to_email, subject, body, [filepath])
        
        if success:
            logger.info(f"[/email_report] Report emailed successfully to {to_email}")
            return jsonify({'status': 'success', 'message': 'Report sent successfully'})
        else:
            logger.error(f"[/email_report] Failed to email report to {to_email}")
            return jsonify({'status': 'error', 'error': 'Failed to send email'}), 500
            
    except Exception as e:
        logger.error(f"[/email_report] Error: {str(e)}")
        return jsonify({'status': 'error', 'error': str(e)}), 500

# ================== Phase 5: Dashboard Routes ==================

@app.route('/dashboard', methods=['GET'])
def dashboard():
    """
    Serve the dashboard interface.
    Phase 5: Dashboard for pinned charts and reports.
    """
    try:
        logger.info("Serving dashboard.html")
        return render_template('dashboard.html')
    except Exception as e:
        logger.error(f"Error serving dashboard.html: {str(e)}")
        return jsonify({'status': 'error', 'error': str(e)}), 500

@app.route('/pin_chart', methods=['POST'])
def pin_chart():
    """
    Pin a chart or report to the dashboard.
    Phase 5: Save pinned items to data/pins.json.
    """
    try:
        import json
        import uuid
        from datetime import datetime
        
        data = request.get_json()
        title = data.get('title', 'Untitled')
        chart_type = data.get('type', 'chart')  # 'chart' or 'report'
        chart_data = data.get('data', {})
        
        logger.info(f"[/pin_chart] Pinning {chart_type}: {title}")
        
        # Load existing pins
        pins_file = 'data/pins.json'
        if os.path.exists(pins_file):
            with open(pins_file, 'r') as f:
                pins_data = json.load(f)
        else:
            pins_data = {'pins': []}
        
        # Create new pin
        new_pin = {
            'id': str(uuid.uuid4()),
            'title': title,
            'type': chart_type,
            'data': chart_data,
            'created_at': datetime.now().isoformat(),
            'pinned_at': datetime.now().isoformat()
        }
        
        # Add to pins
        pins_data['pins'].append(new_pin)
        
        # Save pins
        os.makedirs('data', exist_ok=True)
        with open(pins_file, 'w') as f:
            json.dump(pins_data, f, indent=2)
        
        logger.info(f"[/pin_chart] Pinned successfully with ID: {new_pin['id']}")
        
        return jsonify({
            'status': 'success',
            'message': 'Item pinned successfully',
            'pin_id': new_pin['id']
        })
        
    except Exception as e:
        logger.error(f"[/pin_chart] Error: {str(e)}")
        return jsonify({'status': 'error', 'error': str(e)}), 500

@app.route('/get_pins', methods=['GET'])
def get_pins():
    """
    Get all pinned charts and reports.
    Phase 5: Retrieve pinned items from data/pins.json.
    """
    try:
        import json
        
        logger.info("[/get_pins] Fetching pinned items")
        
        pins_file = 'data/pins.json'
        if os.path.exists(pins_file):
            with open(pins_file, 'r') as f:
                pins_data = json.load(f)
        else:
            pins_data = {'pins': []}
        
        logger.info(f"[/get_pins] Found {len(pins_data['pins'])} pinned items")
        
        return jsonify({
            'status': 'success',
            'pins': pins_data['pins']
        })
        
    except Exception as e:
        logger.error(f"[/get_pins] Error: {str(e)}")
        return jsonify({'status': 'error', 'error': str(e)}), 500

@app.route('/delete_pin/<pin_id>', methods=['DELETE'])
def delete_pin(pin_id):
    """
    Delete a pinned chart or report.
    Phase 5: Remove item from data/pins.json.
    """
    try:
        import json
        
        logger.info(f"[/delete_pin] Deleting pin: {pin_id}")
        
        pins_file = 'data/pins.json'
        if not os.path.exists(pins_file):
            return jsonify({'status': 'error', 'error': 'No pins found'}), 404
        
        # Load pins
        with open(pins_file, 'r') as f:
            pins_data = json.load(f)
        
        # Find and remove pin
        original_count = len(pins_data['pins'])
        pins_data['pins'] = [p for p in pins_data['pins'] if p['id'] != pin_id]
        
        if len(pins_data['pins']) == original_count:
            logger.warning(f"[/delete_pin] Pin not found: {pin_id}")
            return jsonify({'status': 'error', 'error': 'Pin not found'}), 404
        
        # Save updated pins
        with open(pins_file, 'w') as f:
            json.dump(pins_data, f, indent=2)
        
        logger.info(f"[/delete_pin] Pin deleted successfully: {pin_id}")
        
        return jsonify({
            'status': 'success',
            'message': 'Pin deleted successfully'
        })
        
    except Exception as e:
        logger.error(f"[/delete_pin] Error: {str(e)}")
        return jsonify({'status': 'error', 'error': str(e)}), 500

def generate_tts(text: str) -> str:
    """
    Convert text to audio using ElevenLabs TTS and save to file.
    Phase 1: Returns URL path to the audio file for voice responses.
    
    Args:
        text (str): Text to convert to speech
        
    Returns:
        str: URL path to audio file, or empty string on error
    """
    try:
        logger.info(f"[TTS] Generating audio for text: {text[:50]}...")
        audio = elevenlabs.text_to_speech.convert(
            text=text,
            voice_id="JBFqnCBsd6RMkjVDRZzb",  # Voice ID
            model_id="eleven_multilingual_v2",
            output_format="mp3_44100_128"
        )
        
        # Save audio to file
        audio_path = 'static/audio/response.mp3'
        os.makedirs('static/audio', exist_ok=True)
        logger.info(f"[TTS] Saving audio to {audio_path}")
        
        with open(audio_path, 'wb') as f:
            for chunk in audio:
                f.write(chunk)
        
        logger.info("[TTS] Audio saved successfully")
        return f'/{audio_path}'
    except Exception as e:
        logger.error(f"[TTS] Error generating audio: {str(e)}")
        return ''

if __name__ == '__main__':
    logger.info("Starting Flask app")
    app.run(debug=True, host='0.0.0.0', port=5000)