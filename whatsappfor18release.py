# -*- coding: utf-8 -*-
"""
Created on Wed Jul  2 15:46:38 2025

@author: AMBRISH A
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_session import Session
import requests
import logging
import os
from pymongo import MongoClient
import secrets
import datetime
from datetime import timedelta
import uuid
import base64
import vertexai
from vertexai.generative_models import GenerativeModel, Part

app = Flask(__name__)

ACCESS_TOKEN = "EAAHT4DmHuroBOxR6kFlLx5ucMzcq9YYMUR3VepFDtLeF4XgFJeBAq8a8dcXT5rM1TSZCjmB4SrdGBO0jK12CgZAw0AEfAvtkIQk8tzfSNZCMZAFz6CMnCyNqYxZASQ2ajJ2iqf9s6qONnO5kpUjUPVcG4IDq2YnJefynxBETc5uXZBFQJkWP6ZA1dynMPVdF91ocQZDZD"
PHONE_NUMBER_ID = "434171459782510"
VERIFY_TOKEN = "12345"
WHATSAPP_API_URL = f'https://graph.facebook.com/v20.0/{PHONE_NUMBER_ID}/messages'

UPLOAD_FOLDER_IMAGES = r'C:\inetpub\viabl\deploymentServer2\apps\_scripts\Whatsapp\images'
UPLOAD_FOLDER_AUDIOS = r'C:\inetpub\viabl\deploymentServer2\apps\_scripts\Whatsapp\audios'
os.makedirs(UPLOAD_FOLDER_IMAGES, exist_ok=True)
os.makedirs(UPLOAD_FOLDER_AUDIOS, exist_ok=True)

CORS(app)
app.config['SESSION_PERMANENT'] = False
app.config['SESSION_TYPE'] = 'filesystem'
Session(app)

MONGO_URI = "mongodb://192.168.1.100:27017/"
client = MongoClient(MONGO_URI)
db = client['PatientSafe']
collection = db['WhatsappNEW']
user_db = client['PatientSafe']
user_login_collection = user_db['UserLogin']
last_report_id = collection.count_documents({})

# Session timeout changed to 1 minute
SESSION_TIMEOUT_MINUTES = 1

languages = {
    'en': {
        'select_language': "Please select your language",
        'language_selected': "Thanks for reaching out to PatientSafe!",
        'select_inquiry_type': "Please select an option to proceed",
        'share_feedback': "How would you like to share your product experience?",
        'record_feedback': "Please record or upload audio of your product experience and send it.",
        'compose_feedback': "Please compose as text and send it.",
        'ask_image_upload': "Do you want to Upload product image?",
        'upload_image': "Please Upload image of medicinal product.",
        'thank_you': "Thank you for your valuable feedback. We appreciate your effort towards Patient Safety!",
        'medical_inquiry_success': "Thank you for your medical inquiry. Our team will get back to you shortly.",
        'next_question': "Next Question",
        'exit': "Exit"
    },
    'ta': {
        'select_language': "Hi, Please select your language - வணக்கம், தயவுசெய்து உங்கள் மொழியைத் தேர்ந்தெடுக்கவும்.",
        'language_selected': "Thanks for reaching out to PatientSafe! - பேஷண்ட் சேஃப்-க்கு அணுகியதற்கு நன்றி!",
        'select_inquiry_type': "Please select an option to proceed - தொடர ஒரு விருப்பத்தைத் தேர்ந்தெடுக்கவும்",
        'share_feedback': "Please select an option to proceed - தயவுசெய்து தொடரும் போது ஒரு விருப்பத்தைத் தேர்ந்தெடுக்கவும்.",
        'record_feedback': "Please record or upload audio of your product experience and send it. - தயவுசெய்து உங்கள் தயாரிப்பு அனுபவத்தை பதிவு செய்து அல்லது ஒளிப்பதிவாக அனுப்பவும்.",
        'compose_feedback': "Please compose as text and send it. - தயவுசெய்து உரையாக அமைத்து அனுப்பவும்.",
        'ask_image_upload': "Do you want to upload a product image? - உங்கள் தயாரிப்பு படத்தை பதிவேற்ற விரும்புகிறீர்களா?",
        'upload_image': "Please upload image of medicinal product. - மருத்துவ தயாரிப்பின் படத்தை பதிவேற்றவும்.",
        'thank_you': "Thank you for your valuable feedback. We appreciate your effort towards Patient Safety! - உங்கள் மதிப்புமிகு கருத்துக்கான நன்றி. பேஷண்ட் பாதுகாப்பு நோக்கில் உங்கள் முயற்சிக்கு நன்றி!",
        'medical_inquiry_success': "Thank you for your medical inquiry. Our team will get back to you shortly. - உங்கள் மருத்துவ விசாரணைக்கு நன்றி. எங்கள் குழு விரைவில் உங்களைத் தொடர்பு கொள்ளும்.",
        'next_question': "அடுத்த கேள்வி",
        'exit': "வெளியேறு"
    },
    'hi': {
        'select_language': "Hi, Please select your language - नमस्ते, कृपया एक भाषा चुनें।",
        'language_selected': "Thanks for reaching out to PatientSafe! - पेशेंटसेफ को संपर्क करने के लिए धन्यवाद।",
        'select_inquiry_type': "Please select an option to proceed - आगे बढ़ने के लिए एक विकल्प चुनें",
        'share_feedback': "Please select an option to proceed - कृपया आगे बढ़ने के लिए एक विकल्प चुनें।",
        'record_feedback': "Please record or upload audio of your product experience and send it. - कृपया अपने उत्पाद अनुभव का ऑडियो रिकॉर्ड या अपलोड करें और भेजें।",
        'compose_feedback': "Please compose as text and send it. - कृपया पाठ के रूप में लिखें और भेजें।",
        'ask_image_upload': "Do you want to upload a product image? - क्या आप उत्पाद छवि अपलोड करना चाहते हैं?",
        'upload_image': "Please upload image of medicinal product. - कृपया औषधीय उत्पाद की छवि अपलोड करें।",
        'thank_you': "Thank you for your valuable feedback. We appreciate your effort towards Patient Safety! - आपके मूल्यवान प्रतिक्रिया के लिए धन्यवाद। हम पेशेंट सुरक्षा की दिशा में आपके प्रयास की कदर करते हैं!",
        'medical_inquiry_success': "Thank you for your medical inquiry. Our team will get back to you shortly. - आपकी चिकित्सा पूछताछ के लिए धन्यवाद। हमारी टीम जल्द ही आपसे संपर्क करेगी।",
        'next_question': "अगला प्रश्न",
        'exit': "बाहर निकलें"
    }
}


def decrypt_user_data(encrypted_data):
    """
    Decrypt user data using the decryption API
    """
    try:
        print(f"DEBUG: Attempting to decrypt data: {encrypted_data[:50]}..." if len(str(encrypted_data)) > 50 else f"DEBUG: Attempting to decrypt data: {encrypted_data}")
        
        decryption_url = 'http://127.0.0.1:6666/decrypt'
        
        headers = {
            'Content-Type': 'application/json'
        }
        
        payload = {
            'text': encrypted_data
        }
        
        print(f"DEBUG: Sending payload to decryption API: {payload}")
        
        response = requests.post(
            decryption_url,
            json=payload,
            headers=headers,
            timeout=50
        )
        
        print(f"DEBUG: Decryption API response status: {response.status_code}")
        print(f"DEBUG: Decryption API response: {response.text}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"DEBUG: Parsed JSON response: {result}")
            
            # The actual response structure is: {"text": [{"first": "name", "last": "surname", ...}]}
            if 'text' in result and len(result['text']) > 0:
                user_data = result['text'][0]
                first_name = user_data.get('first', '')
                last_name = user_data.get('last', '')
                print(f"DEBUG: Extracted names - First: {first_name}, Last: {last_name}")
                return {
                    'first': first_name,
                    'last': last_name,
                    'full_name': f"{first_name} {last_name}".strip()
                }
            else:
                logging.error(f"Unexpected decryption response structure: {result}")
                print(f"DEBUG: Unexpected response structure: {result}")
                return None
        else:
            logging.error(f"Decryption API failed: {response.status_code} - {response.text}")
            print(f"DEBUG: API call failed with status {response.status_code}")
            return None
            
    except requests.exceptions.Timeout:
        logging.error("Decryption API request timed out")
        print("DEBUG: API request timed out")
        return None
    except requests.exceptions.RequestException as e:
        logging.error(f"Error calling decryption API: {e}")
        print(f"DEBUG: Request exception: {e}")
        return None
    except Exception as e:
        logging.error(f"Unexpected error in decrypt_user_data: {e}")
        print(f"DEBUG: Unexpected error: {e}")
        return None
    
def send_inquiry_type_selection(recipient_id, language):
    button_labels = {
        'en': {'medical_inquiry': "Medical Inquiry", 'product_experience': "Product Experience", 'exit': "Exit"},
        'hi': {'medical_inquiry': "मेडिकल जांच", 'product_experience': "उत्पाद अनुभव", 'exit': "बाहर निकलें"},
        'ta': {'medical_inquiry': "மருத்துவ விசாரணை", 'product_experience': "தயாரிப்பு அனுபவம்", 'exit': "வெளியேறு"}
    }
    buttons = [
        {"type": "reply", "reply": {"id": "medical_inquiry", "title": button_labels[language]['medical_inquiry']}},
        {"type": "reply", "reply": {"id": "product_experience", "title": button_labels[language]['product_experience']}},
        {"type": "reply", "reply": {"id": "exit", "title": button_labels[language]['exit']}}
    ]
    send_whatsapp_message(recipient_id, languages[language]['select_inquiry_type'], buttons)

def is_user_registered(phone_number):
    if phone_number.startswith('91') and len(phone_number) > 2:
        formatted_number = phone_number[2:]
    else:
        formatted_number = phone_number
    user = user_login_collection.find_one({"mobile": formatted_number})
    
    # Debug: Print user data to see what fields are available
    if user:
        print(f"DEBUG: User found for {formatted_number}")
        print(f"DEBUG: User fields: {list(user.keys())}")
        
        # Check for encrypted_data field (adjust field name if different)
        encrypted_field = None
        if 'encrypted_data' in user:
            encrypted_field = 'encrypted_data'
        elif 'encrypted' in user:
            encrypted_field = 'encrypted'
        elif 'enc_data' in user:
            encrypted_field = 'enc_data'
        
        if encrypted_field:
            print(f"DEBUG: Found encrypted field: {encrypted_field}")
            # Decrypt the user data to get the actual name
            decrypted_data = decrypt_user_data(user[encrypted_field])
            if decrypted_data:
                print(f"DEBUG: Decryption successful: {decrypted_data}")
                # Add the decrypted data to the user object for easy access
                user['decrypted_first'] = decrypted_data['first']
                user['decrypted_last'] = decrypted_data['last']
                user['decrypted_full_name'] = decrypted_data['full_name']
            else:
                print("DEBUG: Decryption failed or returned None")
        else:
            print("DEBUG: No encrypted data field found")
            print(f"DEBUG: Available fields: {user.keys()}")
    else:
        print(f"DEBUG: No user found for {formatted_number}")
    
    return user

def send_registration_message(recipient_id):
    registration_link = "https://patientsafe.global-value-web.in:8100/app/C5O5PEEFFQQ7HLUS/main.html?link=test&_s=QKWGJXK2XHQIDOCSPZG8JEZKURGNY3WZ#1"
    message = (
        "You are not registered to use this service. "
        f"Please register using this link: {registration_link}\n\n"
        "After registration, send 'hi' again to start using the service."
    )
    send_whatsapp_message(recipient_id, message)

def send_whatsapp_message(recipient_id, message, buttons=None):
    headers = {'Authorization': f'Bearer {ACCESS_TOKEN}', 'Content-Type': 'application/json'}
    data = {'messaging_product': 'whatsapp', 'to': recipient_id, 'type': 'text', 'text': {'body': message}}
    if buttons:
        data['type'] = 'interactive'
        data['interactive'] = {'type': 'button', 'body': {'text': message}, 'action': {'buttons': buttons}}
    response = requests.post(WHATSAPP_API_URL, json=data, headers=headers)
    logging.debug(f"WhatsApp API Response: {response.text}")
    return response.json()

def is_session_expired(last_activity_time):
    """Check if session has expired based on last activity time"""
    if not last_activity_time:
        return True
    session_timeout = timedelta(minutes=SESSION_TIMEOUT_MINUTES)
    current_time = datetime.datetime.utcnow()
    time_diff = current_time - last_activity_time
    logging.debug(f"Time difference: {time_diff}, Timeout: {session_timeout}")
    return time_diff > session_timeout

def update_user_activity(phone_number):
    """Update the last activity timestamp for the user"""
    collection.update_one(
        {"phone_number": phone_number, "session_active": True},
        {"$set": {"last_activity": datetime.datetime.utcnow()}}
    )

def expire_session(phone_number):
    """Expire the current session and close the report"""
    result = collection.update_one(
        {"phone_number": phone_number, "session_active": True},
        {
            "$set": {
                "session_active": False,
                "session_end_time": datetime.datetime.utcnow(),
                "session_expired": True,
                "report_closed": True
            }
        }
    )
    logging.debug(f"Session expired for {phone_number}. Updated {result.modified_count} documents.")

def create_user(phone_number):
    global last_report_id
    report_id = get_next_report_id()
    current_time = datetime.datetime.utcnow()
    user_data = {
        "phone_number": phone_number,
        "report_id": report_id,
        "language": "en",
        "feedback_method": None,
        "feedback": None,
        "media": {"images": [], "audio": []},
        "audio_inquiries": [],
        "medical_inquiries": [],
        "Audio_Transcripts": [],
        "session_active": True,
        "created_at": current_time,
        "last_activity": current_time,  # Track last activity
        "Updatefollowup": "Yes"
    }
    collection.insert_one(user_data)
    return user_data

@app.route('/webhook', methods=['GET'])
def verify_token():
    mode = request.args.get('hub.mode')
    token = request.args.get('hub.verify_token')
    challenge = request.args.get('hub.challenge')
    if mode and token and mode == 'subscribe' and token == VERIFY_TOKEN:
        logging.debug("Webhook verified successfully")
        return challenge, 200
    logging.debug("Webhook verification failed")
    return 'Forbidden', 403

def get_next_report_id():
    global last_report_id
    last_report_id += 1
    return f"GVW_WA_{last_report_id:05}"

def send_language_selection(recipient_id):
    buttons = [
        {"type": "reply", "reply": {"id": "lang_en", "title": "English"}},
        {"type": "reply", "reply": {"id": "lang_ta", "title": "தமிழ்"}},
        {"type": "reply", "reply": {"id": "lang_hi", "title": "हिंदी"}}
    ]
    send_whatsapp_message(recipient_id, languages['en']['select_language'], buttons)

def send_feedback_method(recipient_id, language, is_medical_inquiry=False):
    button_labels = {
        'en': {'text_input': "Text Input", 'voice_input': "Voice Input", 'exit': "Exit"},
        'hi': {'text_input': "टेक्स्ट इनपुट", 'voice_input': "वॉइस इनपुट", 'exit': "बाहर निकलें"},
        'ta': {'text_input': "உரை உள்ளீடு", 'voice_input': "குரல் உள்ளீடு", 'exit': "வெளியேறு"}
    }
    buttons = [
        {"type": "reply", "reply": {"id": "text_input", "title": button_labels[language]['text_input']}},
        {"type": "reply", "reply": {"id": "voice_input", "title": button_labels[language]['voice_input']}},
        {"type": "reply", "reply": {"id": "exit", "title": button_labels[language]['exit']}}
    ]
    message = "Please choose how you would like to ask your medical question:" if is_medical_inquiry else languages[language]['share_feedback']
    send_whatsapp_message(recipient_id, message, buttons)

def send_feedback_input(recipient_id, method, language, is_medical_inquiry=False):
    if method == 'text_input':
        if is_medical_inquiry:
            send_whatsapp_message(recipient_id, "Please type your medical question.")
        else:
            send_whatsapp_message(recipient_id, languages[language]['compose_feedback'])
    elif method == 'voice_input':
        if language == 'hi':
            bilingual_message = (
                "कृपया अपने उत्पाद अनुभव का ऑडियो रिकॉर्ड या अपलोड करें और भेजें।\n\n"
                "Please record or upload audio of your feedback or question."
            )
            send_whatsapp_message(recipient_id, bilingual_message)
        else:
            send_whatsapp_message(recipient_id, "Please record or upload audio of your feedback or question.")

def send_image_upload_prompt(recipient_id, language):
    button_labels = {
        'en': {'yes': "Yes", 'no': "No", 'exit': "Exit"},
        'hi': {'yes': "हाँ", 'no': "नहीं", 'exit': "बाहर निकलें"},
        'ta': {'yes': "ஆம்", 'no': "இல்லை", 'exit': "வெளியேறு"}
    }
    buttons = [
        {"type": "reply", "reply": {"id": "yes", "title": button_labels[language]['yes']}},
        {"type": "reply", "reply": {"id": "no", "title": button_labels[language]['no']}},
        {"type": "reply", "reply": {"id": "exit", "title": button_labels[language]['exit']}}
    ]
    send_whatsapp_message(recipient_id, languages[language]['ask_image_upload'], buttons)
    
def process_user_input(sender_id, message_data):
    user = collection.find_one({"phone_number": sender_id, "session_active": True})
    
    # Check session expiration using last_activity instead of created_at
    if not user or is_session_expired(user.get('last_activity')):
        if user:  # User exists but session expired
            expire_session(sender_id)
        send_whatsapp_message(sender_id, "Your session has expired. Please send 'hi' to start a new session.")
        return
    
    # Update last activity timestamp
    update_user_activity(sender_id)
    
    language = user.get('language', 'en')
    
    if 'interactive' in message_data and message_data['interactive']['type'] == 'button_reply':
        selected_option = message_data['interactive']['button_reply']['id']
        
        if selected_option == 'exit':
            if user.get('inquiry_type') == 'medical_inquiry':
                if user.get('medical_inquiries'):
                    questions = "\n".join(user['medical_inquiries'])
                    api_response = requests.get(
                        "http://127.0.0.1:8798/process_questions",
                        params={"text": questions}
                    )
                    if api_response.status_code == 200:
                        result = api_response.json().get('result', 'no')
                        if result == 'yes':
                            send_whatsapp_message(sender_id, "We have found AE/PQC in your inquiries.")
                            send_image_upload_prompt(sender_id, language)
                        else:
                            send_whatsapp_message(sender_id, "No significant issues found in your inquiries.")
                            collection.update_one(
                                {"phone_number": sender_id, "session_active": True},
                                {"$set": {"session_active": False, "report_closed": True}}
                            )
                            send_whatsapp_message(sender_id, "Session ended. Send 'hi' to start a new session.")
                    else:
                        send_whatsapp_message(sender_id, "Unable to process your inquiries at this time.")
                        collection.update_one(
                            {"phone_number": sender_id, "session_active": True},
                            {"$set": {"session_active": False, "report_closed": True}}
                        )
                        send_whatsapp_message(sender_id, "Session ended. Send 'hi' to start a new session.")
                else:
                    collection.update_one(
                        {"phone_number": sender_id, "session_active": True},
                        {"$set": {"session_active": False, "report_closed": True}}
                    )
                    send_whatsapp_message(sender_id, "Session ended. Send 'hi' to start a new session.")
            else:
                collection.update_one(
                    {"phone_number": sender_id, "session_active": True},
                    {"$set": {"session_active": False, "report_closed": True}}
                )
                send_whatsapp_message(sender_id, "Session ended. Send 'hi' to start a new session.")
            return
            
        elif selected_option in ['lang_en', 'lang_hi', 'lang_ta']:
            lang_map = {'lang_en': 'en', 'lang_hi': 'hi', 'lang_ta': 'ta'}
            new_lang = lang_map[selected_option]
            collection.update_one(
                {"phone_number": sender_id, "session_active": True},
                {"$set": {"language": new_lang}}
            )
            send_whatsapp_message(sender_id, languages[new_lang]['language_selected'])
            send_inquiry_type_selection(sender_id, new_lang)
        
        elif selected_option in ['medical_inquiry', 'product_experience']:
            collection.update_one(
                {"phone_number": sender_id, "session_active": True},
                {"$set": {"inquiry_type": selected_option}}
            )
            send_feedback_method(sender_id, language, is_medical_inquiry=(selected_option == 'medical_inquiry'))

        elif selected_option in ['text_input', 'voice_input']:
            # Always store feedback_method as 'text_input' for medical inquiries
            feedback_method = 'text_input' if user.get('inquiry_type') == 'medical_inquiry' else selected_option
            collection.update_one(
                {"phone_number": sender_id, "session_active": True},
                {"$set": {"feedback_method": feedback_method}}
            )
            send_feedback_input(sender_id, selected_option, language, is_medical_inquiry=(user.get('inquiry_type') == 'medical_inquiry'))

        elif selected_option in ['yes', 'no']:
            handle_image_upload(sender_id, selected_option, language)

    else:
        handle_feedback_submission(sender_id, message_data, language)

def handle_image_upload(sender_id, selected_option, language):
    user = collection.find_one({"phone_number": sender_id, "session_active": True})
    if not user:
        return

    inquiry_type = user.get('inquiry_type')
    
    if selected_option == 'yes':
        send_whatsapp_message(sender_id, languages[language]['upload_image'])
    elif selected_option == 'no':
        if inquiry_type == 'medical_inquiry':
            if user.get('medical_inquiries'):
                questions = "\n".join(user['medical_inquiries'])
                api_response = requests.get(
                    "http://127.0.0.1:8798/process_questions",
                    params={"text": questions}
                )
                if api_response.status_code == 200:
                    result = api_response.json().get('result', 'no')
                    if result == 'yes':
                        send_whatsapp_message(sender_id, "We have found AE/PQC in your inquiries.")
                        handle_report_request(sender_id)
        else:
            handle_report_request(sender_id)
            
        send_whatsapp_message(sender_id, languages[language]['thank_you'])
        collection.update_one(
            {"phone_number": sender_id, "session_active": True},
            {"$set": {"session_active": False, "report_closed": True}}
        )
        send_whatsapp_message(sender_id, "Session ended. Send 'hi' to start a new session.")

def handle_feedback_submission(sender_id, message_data, language):
    user = collection.find_one({"phone_number": sender_id, "session_active": True})
    
    # Check session expiration
    if not user or is_session_expired(user.get('last_activity')):
        if user:
            expire_session(sender_id)
        send_whatsapp_message(sender_id, "Your session has expired. Please send 'hi' to start a new session.")
        return
    
    # Update activity timestamp
    update_user_activity(sender_id)
        
    report_id = user.get('report_id')
    inquiry_type = user.get('inquiry_type')

    if 'audio' in message_data or ('document' in message_data and message_data['document'].get('mime_type', '').startswith('audio/')):
        if inquiry_type == 'medical_inquiry':
            audio_id = message_data.get('audio', {}).get('id') or message_data['document']['id']
            timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
            audio_filename = f"GVW_WA_{report_id.split('_')[-1]}_medical_audio.ogg"
            saved_filename = save_media(audio_id, sender_id, 'audio', audio_filename.split('.')[0])
            
            if saved_filename:
                collection.update_one(
                    {"phone_number": sender_id, "session_active": True},
                    {
                        "$push": {"audio_inquiries": saved_filename},
                        "$set": {"media.audio": [saved_filename]}
                    }
                )
                try:
                    vertexai.init(project="patientsafe", location="asia-south1")
                    model = GenerativeModel("gemini-1.5-pro-001")
                    
                    audio_path = os.path.join(UPLOAD_FOLDER_AUDIOS, saved_filename)
                    with open(audio_path, 'rb') as audio_file:
                        audio_data = audio_file.read()
                    
                    audio_part = Part.from_data(
                        mime_type="audio/ogg",
                        data=base64.b64encode(audio_data).decode('utf-8')
                    )
                    prompt = """Please transcribe this audio to English. Focus on accuracy and clarity.
                    Guidelines:
                    - Maintain professional medical terminology if present
                    - Ignore background noise or interruptions
                    - Format the text clearly with proper punctuation
                    - If multiple speakers are present, indicate speaker changes
                    - VERY IMPORTANT: Even if the audio is in a non-English language, please TRANSLATE it to English"""
                    
                    responses = model.generate_content(
                        [prompt, audio_part],
                        generation_config={"temperature": 0, "top_p": 0.8, "top_k": 40},
                        stream=True
                    )
                    transcription = ""
                    for response in responses:
                        if hasattr(response, 'candidates') and response.candidates and response.candidates[0].finish_reason == "SAFETY":
                            send_whatsapp_message(sender_id, "Content blocked by safety filters. Please review the audio content.")
                            break
                        if hasattr(response, 'text'):
                            transcription += response.text
                    
                    if transcription:
                        collection.update_one(
                            {"phone_number": sender_id, "session_active": True},
                            {
                                "$push": {
                                    "medical_inquiries": transcription,
                                    "Audio_Transcripts": transcription
                                }
                            }
                        )
                        current_feedback = user.get('feedback', '')
                        new_feedback = f"{current_feedback}, {transcription}" if current_feedback else transcription
                        collection.update_one(
                            {"phone_number": sender_id, "session_active": True},
                            {"$set": {"feedback": new_feedback}}
                        )
                        send_whatsapp_message(sender_id, f"Transcription: {transcription}")
                        api_response = send_to_medical_api(transcription)
                        if api_response:
                            api_response = api_response.replace("Answer:", "").strip()
                            send_whatsapp_message(sender_id, api_response)
                        else:
                            send_whatsapp_message(sender_id, "Failed to process your question. Please try again.")
                    else:
                        response = model.generate_content(
                            [prompt, audio_part],
                            generation_config={"temperature": 0, "top_p": 0.8, "top_k": 40}
                        )
                        if hasattr(response, 'text') and response.text:
                            transcription = response.text
                            collection.update_one(
                                {"phone_number": sender_id, "session_active": True},
                                {
                                    "$push": {
                                        "medical_inquiries": transcription,
                                        "Audio_Transcripts": transcription
                                    }
                                }
                            )
                            current_feedback = user.get('feedback', '')
                            new_feedback = f"{current_feedback}, {transcription}" if current_feedback else transcription
                            collection.update_one(
                                {"phone_number": sender_id, "session_active": True},
                                {"$set": {"feedback": new_feedback}}
                            )
                            send_whatsapp_message(sender_id, f"Transcription: {transcription}")
                            api_response = send_to_medical_api(transcription)
                            if api_response:
                                api_response = api_response.replace("Answer:", "").strip()
                                send_whatsapp_message(sender_id, api_response)
                            else:
                                send_whatsapp_message(sender_id, "Failed to process your question. Please try again.")
                        else:
                            send_whatsapp_message(sender_id, "Unable to transcribe audio. Please try again.")
                except Exception as e:
                    print(f"Error processing audio with Gemini: {e}")
                    send_whatsapp_message(sender_id, "Error processing audio. Our team will assist you.")
                
                buttons = [
                    {"type": "reply", "reply": {"id": "next_question", "title": languages[language]['next_question']}},
                    {"type": "reply", "reply": {"id": "exit", "title": languages[language]['exit']}}
                ]
                send_whatsapp_message(sender_id, "What would you like to do next?", buttons)
            else:
                send_whatsapp_message(sender_id, "Failed to save audio. Please try again.")
        else:
            existing_audio = user.get('media', {}).get('audio')
            if existing_audio:
                send_whatsapp_message(sender_id, "You have already uploaded an audio file. Only one audio is allowed.")
                return
            audio_id = message_data.get('audio', {}).get('id') or message_data['document']['id']
            audio_filename = save_media(audio_id, sender_id, 'audio', report_id)
            if audio_filename:
                collection.update_one(
                    {"phone_number": sender_id, "session_active": True},
                    {"$set": {"media.audio": audio_filename}}
                )
                send_image_upload_prompt(sender_id, language)
            else:
                send_whatsapp_message(sender_id, "Failed to save audio. Please try again.")
    
    elif 'text' in message_data:
        feedback_text = message_data['text']['body']
        if feedback_text.lower() == 'hi':
            return
        if inquiry_type == 'medical_inquiry':
            collection.update_one(
                {"phone_number": sender_id, "session_active": True},
                {"$push": {"medical_inquiries": feedback_text}}
            )
            current_feedback = user.get('feedback', '')
            new_feedback = f"{current_feedback}, {feedback_text}" if current_feedback else feedback_text
            collection.update_one(
                {"phone_number": sender_id, "session_active": True},
                {"$set": {"feedback": new_feedback}}
            )
            api_response = send_to_medical_api(feedback_text)
            if api_response:
                api_response = api_response.replace("Answer:", "").strip()
                send_whatsapp_message(sender_id, api_response)
                buttons = [
                    {"type": "reply", "reply": {"id": "next_question", "title": languages[language]['next_question']}},
                    {"type": "reply", "reply": {"id": "exit", "title": languages[language]['exit']}}
                ]
                send_whatsapp_message(sender_id, "What would you like to do next?", buttons)
            else:
                send_whatsapp_message(sender_id, "Failed to process your question. Please try again.")
        else:
            collection.update_one(
                {"phone_number": sender_id, "session_active": True},
                {"$set": {"feedback": feedback_text}}
            )
            send_image_upload_prompt(sender_id, language)
    
    elif 'interactive' in message_data and message_data['interactive']['type'] == 'button_reply':
        selected_option = message_data['interactive']['button_reply']['id']
        
        if selected_option == 'next_question':
            if inquiry_type == 'medical_inquiry':
                send_feedback_input(sender_id, user.get('feedback_method'), language, is_medical_inquiry=True)
            else:
                send_whatsapp_message(sender_id, "Please provide your next feedback.")
                
        elif selected_option == 'exit' and inquiry_type == 'medical_inquiry':
            if user.get('medical_inquiries'):
                questions = "\n".join(user['medical_inquiries'])
                api_response = requests.get(
                    "http://127.0.0.1:8798/process_questions",
                    params={"text": questions}
                )
                if api_response.status_code == 200:
                    result = api_response.json().get('result', 'no')
                    button_labels = {
                        'en': {'yes': "Yes", 'no': "No"},
                        'hi': {'yes': "हाँ", 'no': "नहीं"},
                        'ta': {'yes': "ஆம்", 'no': "இல்லை"}
                    }
                    buttons = [
                        {"type": "reply", "reply": {"id": "yes_classification", "title": button_labels[language]['yes']}},
                        {"type": "reply", "reply": {"id": "no_classification", "title": button_labels[language]['no']}}
                    ]
                    message = "We have reviewed your inquiries. Do they require further action?" if result == 'yes' else "No significant issues found. Do you still want to proceed?"
                    send_whatsapp_message(sender_id, message, buttons)
                else:
                    send_whatsapp_message(sender_id, "Unable to process your inquiries at this time.")
                    send_image_upload_prompt(sender_id, language)
            else:
                send_whatsapp_message(sender_id, languages[language]['thank_you'])
                collection.update_one(
                    {"phone_number": sender_id, "session_active": True},
                    {"$set": {"session_active": False, "report_closed": True}}
                )
                send_whatsapp_message(sender_id, "Session ended. Send 'hi' to start a new session.")
                
        elif selected_option == 'exit' and inquiry_type != 'medical_inquiry':
            handle_report_request(sender_id)
            send_whatsapp_message(sender_id, languages[language]['thank_you'])
            collection.update_one(
                {"phone_number": sender_id, "session_active": True},
                {"$set": {"session_active": False, "report_closed": True}}
            )
            send_whatsapp_message(sender_id, "Session ended. Send 'hi' to start a new session.")
            
        elif selected_option == 'yes_classification' and inquiry_type == 'medical_inquiry':
            send_image_upload_prompt(sender_id, language)
            
        elif selected_option == 'no_classification' and inquiry_type == 'medical_inquiry':
            send_whatsapp_message(sender_id, languages[language]['thank_you'])
            collection.update_one(
                {"phone_number": sender_id, "session_active": True},
                {"$set": {"session_active": False, "report_closed": True}}
            )
            send_whatsapp_message(sender_id, "Session ended. Send 'hi' to start a new session.")
            
        elif selected_option in ['yes', 'no', 'exit']:
            handle_image_upload(sender_id, selected_option, language)
    
    elif 'image' in message_data or ('document' in message_data and message_data['document'].get('mime_type', '').startswith('image/')):
        existing_images = user.get('media', {}).get('images', [])
        if len(existing_images) >= 2:
            send_whatsapp_message(sender_id, "Maximum of 2 images uploaded.")
            return
        image_id = message_data.get('image', {}).get('id') or message_data['document']['id']
        image_filename = save_media(image_id, sender_id, 'image', f"{report_id}_img{len(existing_images)+1}")
        if image_filename:
            collection.update_one(
                {"phone_number": sender_id, "session_active": True},
                {"$push": {"media.images": image_filename}}
            )
            if len(existing_images) == 0:
                button_labels = {
                    'en': {'yes': "Yes", 'no': "No", 'exit': "Exit"},
                    'hi': {'yes': "हाँ", 'no': "नहीं", 'exit': "बाहर निकलें"},
                    'ta': {'yes': "ஆம்", 'no': "இல்லை", 'exit': "வெளியேறு"}
                }
                buttons = [
                    {"type": "reply", "reply": {"id": "yes", "title": button_labels[language]['yes']}},
                    {"type": "reply", "reply": {"id": "no", "title": button_labels[language]['no']}},
                    {"type": "reply", "reply": {"id": "exit", "title": button_labels[language]['exit']}}
                ]
                send_whatsapp_message(sender_id, "Image uploaded. Would you like to upload another image?", buttons)
            else:
                handle_report_request(sender_id)
                send_whatsapp_message(sender_id, languages[language]['thank_you'])
                collection.update_one(
                    {"phone_number": sender_id, "session_active": True},
                    {"$set": {"session_active": False, "report_closed": True}}
                )
                send_whatsapp_message(sender_id, "Session ended. Send 'hi' to start a new session.")
        else:
            send_whatsapp_message(sender_id, "Failed to save image. Please try again.")
    
    elif 'document' in message_data:
        mime_type = message_data['document'].get('mime_type', '')
        unsupported_types = ['application/pdf', 'application/zip', 'image/gif']
        if any(mime_type.startswith(utype) for utype in unsupported_types):
            send_whatsapp_message(sender_id, f"Sorry, {mime_type} files are not accepted. Please upload images or audio files only.")

def send_to_medical_api(question):
    try:
        print(f"Sending question to medical API: {question}")
        request_id = str(uuid.uuid4())
        print(f"Generated Request ID: {request_id} for question: {question}")
        response = requests.get(
            "http://127.0.0.1:1199/ask_whatsapp",
            params={"question": question, "request_id": request_id}
        )
        print(f"Response Status Code: {response.status_code}")
        print(f"Response Content: {response.text}")
        if response.status_code == 200:
            api_response = response.json()
            print(f"API response received: {api_response}")
            return api_response.get("answer", "No answer found in API response.")
        else:
            logging.error(f"API request failed: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        logging.error(f"Error calling medical API: {e}")
        print(f"Exception: {e}")
        return None

@app.route('/webhook', methods=['POST'])
def webhook():
    logging.debug("Incoming webhook POST request received")
    data = request.json
    logging.debug(f"Incoming data: {data}")

    if 'entry' in data and 'messages' in data['entry'][0]['changes'][0]['value']:
        message_data = data['entry'][0]['changes'][0]['value']['messages'][0]
        sender_id = message_data['from']
        is_hi_message = 'text' in message_data and message_data['text']['body'].lower() == 'hi'

        # Check if user is greeting with 'hi'
        if is_hi_message:
            user_data = is_user_registered(sender_id)
            if user_data:
                print(f"DEBUG: User data found for {sender_id}")
                # Use decrypted first name if available, otherwise fallback to regular greeting
                if 'decrypted_first' in user_data and user_data['decrypted_first']:
                    first_name = user_data['decrypted_first']
                    print(f"DEBUG: Using decrypted first name: {first_name}")
                    send_whatsapp_message(sender_id, f"Hi {first_name} 👋")
                else:
                    # Fallback if decryption failed or no encrypted data
                    print("DEBUG: No decrypted first name, checking for regular 'first' field")
                    first_name = user_data.get('first', '')
                    if first_name:
                        print(f"DEBUG: Using regular first name: {first_name}")
                        send_whatsapp_message(sender_id, f"Hi {first_name} 👋")
                    else:
                        print("DEBUG: No first name found, using generic greeting")
                        send_whatsapp_message(sender_id, f"Hi 👋")
            else:
                print(f"DEBUG: No user data found for {sender_id}")
                send_registration_message(sender_id)
                return jsonify({"status": "registration_required"}), 200

        # Find active session
        user = collection.find_one({"phone_number": sender_id, "session_active": True})
        
        if user:
            # Check if session has expired
            if is_session_expired(user.get('last_activity')):
                expire_session(sender_id)
                if is_hi_message:
                    if is_user_registered(sender_id):
                        user = create_user(sender_id)
                        send_language_selection(sender_id)
                    else:
                        send_registration_message(sender_id)
                else:
                    send_whatsapp_message(sender_id, "Your session has expired. Please send 'hi' to start a new session.")
            else:
                # Session is active, process the input
                process_user_input(sender_id, message_data)
        else:
            # No active session
            if is_hi_message:
                if is_user_registered(sender_id):
                    user = create_user(sender_id)
                    send_language_selection(sender_id)
                else:
                    send_registration_message(sender_id)
            else:
                send_whatsapp_message(sender_id, "Previous session has ended. Please send 'hi' to start a new session.")

    return jsonify({"status": "received"}), 200

def save_media(media_id, sender_id, media_type, report_id):
    headers = {'Authorization': f'Bearer {ACCESS_TOKEN}'}
    media_url_response = requests.get(f'https://graph.facebook.com/v20.0/{media_id}', headers=headers)
    if media_url_response.status_code != 200:
        logging.error(f"Failed to get media URL: {media_url_response.text}")
        return None
    media_url = media_url_response.json().get('url')
    if not media_url:
        logging.error("No media download URL found")
        return None
    media_download_response = requests.get(media_url, headers=headers)
    if media_download_response.status_code == 200:
        file_extension = 'ogg' if media_type == 'audio' else 'jpg'
        filename = f"{report_id}_{media_type}.{file_extension}"
        media_path = os.path.join(
            UPLOAD_FOLDER_IMAGES if media_type == 'image' else UPLOAD_FOLDER_AUDIOS,
            filename
        )
        with open(media_path, 'wb') as f:
            f.write(media_download_response.content)
        logging.debug(f"Media saved at {media_path}")
        return filename
    else:
        logging.error(f"Error downloading media content: {media_download_response.status_code} - {media_download_response.text}")
        return None

def generate_and_share_report_url(sender_id, report_id):
    report_url = f"https://patientsafe.global-value-web.in:8100/site/UTPJXWZHSRGCQIOP?Report_ID={report_id}"
    send_whatsapp_message(sender_id, f"Click on this Consumer Report Form link, Review and Edit as needed: {report_url}")

def handle_report_request(sender_id):
    user = collection.find_one({"phone_number": sender_id, "session_active": True})
    if not user:
        logging.warning(f"No active session found for user {sender_id}")
        send_whatsapp_message(sender_id, "No active session found. Please start a new session by sending 'hi'.")
        return
    report_id = user.get("report_id")
    if not report_id:
        logging.error(f"No report ID found for active session of user {sender_id}")
        send_whatsapp_message(sender_id, "An error occurred. Please try again later.")
        return
    if user.get('feedback') or user.get('media', {}).get('images'):
        generate_and_share_report_url(sender_id, report_id)
        collection.update_one(
            {"phone_number": sender_id, "session_active": True},
            {"$set": {"session_active": False, "session_end_time": datetime.datetime.utcnow(), "report_closed": True}}
        )

@app.route("/upload_audio", methods=["POST"])
def upload_audio():
    if "file" not in request.files:
        return jsonify({"message": "No audio file uploaded"}), 400
    file = request.files["file"]
    email = request.form.get("email")
    if not email:
        return jsonify({"message": "Email is required"}), 400
    file_id = str(uuid.uuid4())
    filename = f"{email}.mp3"
    filepath = os.path.join(UPLOAD_FOLDER_AUDIOS, filename)
    file.save(filepath)
    return jsonify({"message": "Audio uploaded successfully.", "file_id": file_id}), 200

@app.route("/upload_image", methods=["POST"])
def upload_image():
    if "file" not in request.files:
        return jsonify({"message": "No image file uploaded"}), 400
    file = request.files["file"]
    email = request.form.get("email")
    if not email:
        return jsonify({"message": "Email is required"}), 400
    file_id = str(uuid.uuid4())
    filename = f"{email}.png"
    filepath = os.path.join(UPLOAD_FOLDER_IMAGES, filename)
    file.save(filepath)
    return jsonify({"message": "Image uploaded successfully.", "file_id": file_id}), 200

if __name__ == '__main__':
    app.run(port=8000)

 