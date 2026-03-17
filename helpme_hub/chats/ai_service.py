"""
AI Service for Google Gemini integration.
Handles AI chat responses using Google Gemini API.
"""
try:
    import google.generativeai as genai
except ImportError:
    # Fallback if package not available
    genai = None

from django.conf import settings
from django.utils import timezone
from .models import Chat, ChatMessage
import logging
import json
import os
import time

logger = logging.getLogger(__name__)


def _debug_log(location, message, data, hypothesis_id):
    """Lightweight debug logger for Gemini issues."""
    try:
        log_entry = {
            "sessionId": "c93079",
            "runId": "gemini-debug",
            "hypothesisId": hypothesis_id,
            "location": location,
            "message": message,
            "data": data or {},
            "timestamp": int(time.time() * 1000),
        }
        log_path = "/Users/islamelsayed/Documents/Help Me /.cursor/debug-c93079.log"
        os.makedirs(os.path.dirname(log_path), exist_ok=True)
        with open(log_path, "a") as f:
            f.write(json.dumps(log_entry) + "\n")
    except Exception:
        # Never let debug logging break the app
        pass


def initialize_gemini():
    """Initialize Google Gemini API client."""
    if genai is None:
        logger.warning('google-generativeai package not available. AI features will not work.')
        _debug_log(
            "chats/ai_service.py:initialize_gemini",
            "genai_import_missing",
            {"genai_is_none": True},
            "H1",
        )
        return None
    
    api_key = getattr(settings, 'GOOGLE_GEMINI_API_KEY', '')
    if not api_key:
        logger.warning('GOOGLE_GEMINI_API_KEY not set. AI features will not work.')
        _debug_log(
            "chats/ai_service.py:initialize_gemini",
            "api_key_missing",
            {"has_key": False},
            "H2",
        )
        return None
    
    try:
        genai.configure(api_key=api_key)
        _debug_log(
            "chats/ai_service.py:initialize_gemini",
            "genai_configured",
            {"has_key": True},
            "H2",
        )
        return genai
    except Exception as e:
        logger.error(f'Failed to initialize Gemini API: {str(e)}')
        _debug_log(
            "chats/ai_service.py:initialize_gemini",
            "genai_config_failed",
            {"error": str(e)},
            "H3",
        )
        return None


def detect_ticket_intent(user_message):
    """
    Lightweight, rule‑based detector for ticket‑creation intents.

    Returns a small dict when an intent is detected:
        {
            'intent': 'create_ticket',
            'category': 'printer' | 'account' | 'device' | 'general',
        }
    or None when no ticket‑related intent is found.
    """
    if not user_message:
        return None

    text = user_message.strip().lower()

    # Core intent phrases – asking explicitly to open/create/submit a ticket.
    intent_triggers = [
        "open a ticket",
        "create a ticket",
        "submit a ticket",
        "log a ticket",
        "raise a ticket",
    ]
    if not any(phrase in text for phrase in intent_triggers):
        return None

    # Category hints based on common words in the same message.
    category = "general"
    if any(word in text for word in ["printer", "print"]):
        category = "printer"
    elif any(word in text for word in ["login", "password", "account"]):
        category = "account"
    elif any(word in text for word in ["device", "promethean", "board", "screen"]):
        category = "device"

    return {
        "intent": "create_ticket",
        "category": category,
    }


def generate_ai_response(chat_id=None, user_message=None, conversation_history=None):
    """
    Generate AI response using Google Gemini.
    
    Args:
        chat_id: ID of the chat (optional, for quick help)
        user_message: The user's message content
        conversation_history: List of previous messages (optional)
    
    Returns:
        str: AI response text, or None if error
    """
    # Initialize Gemini
    genai_client = initialize_gemini()
    if not genai_client:
        _debug_log(
            "chats/ai_service.py:generate_ai_response",
            "initialize_gemini_returned_none",
            {"chat_id": chat_id, "has_message": bool(user_message)},
            "H4",
        )
        return None
    
    # Get model configuration
    model_name = getattr(settings, 'GEMINI_MODEL', 'gemini-1.5-flash')
    max_tokens = getattr(settings, 'GEMINI_MAX_TOKENS', 1000)
    temperature = getattr(settings, 'GEMINI_TEMPERATURE', 0.7)
    
    try:
        _debug_log(
            "chats/ai_service.py:generate_ai_response",
            "before_model_init",
            {"model_name": model_name, "max_tokens": max_tokens, "temperature": temperature},
            "H5",
        )
        # Get the model
        model = genai_client.GenerativeModel(model_name)
        
        # Build conversation context
        system_prompt = """You are a calm, patient IT helper for people with low attention span and very little technical knowledge.

STRICT STYLE RULES (ALWAYS FOLLOW THESE):
- Keep answers short.
- Start with ONE sentence that says what is probably wrong in plain language.
- Then give at most 3–4 VERY short numbered steps.
- Each step must be 1 simple sentence. No long paragraphs.
- Use everyday words. Avoid technical terms unless there is no simple word.
- Prefer actions that take less than 1 minute (check power, restart, try another cable, etc.).
- Never give more than 4 steps at once. If more is needed, say: "If that didn't fix it, tell me and I'll give the next simple steps."
- When you need information, ask ONE clear yes/no or multiple‑choice question at a time.
- Never ask the user for their name; assume the system already knows it.
- If you need contact details, ask for EITHER a room number OR a phone number (not both) in one short question, and only after simple steps fail.

TONE:
- Friendly, encouraging, never blaming.
- Assume the user may be stressed or distracted.
- Good openers: "This sounds frustrating, let's fix it in a few quick steps." or "We'll try a very simple check first."

REMINDER:
- The goal is a quick, easy fix. Short answer plus a few simple steps is always better than long explanations.
- Only give detailed explanations if the user explicitly asks for "why" or "more details"."""
        
        # Prepare conversation history
        # Build the prompt with system context (simple string format works with all API versions)
        prompt_parts = [f"{system_prompt}\n\n"]
        
        if conversation_history:
            # Format conversation history (can be from chat or quick help)
            for msg in conversation_history[-10:]:  # Last 10 messages for context
                # Handle both chat format and quick help format
                if isinstance(msg, dict):
                    if 'sender_type' in msg:
                        # Chat format
                        sender = 'User' if msg['sender_type'] == 'user' else 'Assistant'
                        content = msg.get('content', '')
                    elif 'role' in msg:
                        # Already formatted (quick help format)
                        sender = 'User' if msg['role'] == 'user' else 'Assistant'
                        content = msg.get('content', '')
                    else:
                        continue
                else:
                    continue
                
                prompt_parts.append(f"{sender}: {content}\n")
        
        # Add current user message
        prompt_parts.append(f"User: {user_message}\n\nAssistant:")
        
        # Combine all parts into a single prompt string
        full_prompt = "".join(prompt_parts)
        
        # Generate response
        generation_config = {
            'temperature': temperature,
            'max_output_tokens': max_tokens,
        }
        
        # Use simple string prompt format (works with all API versions)
        response = model.generate_content(
            full_prompt,
            generation_config=generation_config
        )
        _debug_log(
            "chats/ai_service.py:generate_ai_response",
            "after_generate_content",
            {"has_response": bool(response), "has_text": bool(getattr(response, "text", None))},
            "H6",
        )
        
        # Extract response text
        if response and response.text:
            return response.text.strip()
        else:
            logger.warning('Empty response from Gemini API')
            _debug_log(
                "chats/ai_service.py:generate_ai_response",
                "empty_response",
                {},
                "H6",
            )
            return None
            
    except Exception as e:
        error_str = str(e)
        logger.error(f'Error generating AI response: {error_str}')
        _debug_log(
            "chats/ai_service.py:generate_ai_response",
            "exception_from_generate_content",
            {"error": error_str},
            "H7",
        )
        
        # Check for quota/billing errors and provide helpful messages
        if '429' in error_str or 'quota' in error_str.lower() or 'billing' in error_str.lower():
            logger.warning('AI quota/billing limit reached. User needs to check Google Cloud billing settings.')
            # Return None - the calling code will handle showing appropriate error message
        elif '401' in error_str or '403' in error_str or 'invalid' in error_str.lower():
            logger.warning('AI API key issue. Check GOOGLE_GEMINI_API_KEY configuration.')
        
        return None


def process_ai_response(chat_id, user_message):
    """
    Process user message and generate AI response, then save to chat.
    
    Args:
        chat_id: ID of the chat
        user_message: The user's message content
    
    Returns:
        ChatMessage: The created AI message, or None if error
    """
    try:
        # Get chat
        chat = Chat.objects.get(id=chat_id)
        
        # Get conversation history
        previous_messages = ChatMessage.objects.filter(
            chat=chat
        ).order_by('created_at')[:20]  # Last 20 messages
        
        conversation_history = [
            {
                'sender_type': msg.sender_type,
                'content': msg.content
            }
            for msg in previous_messages
        ]
        
        # Generate AI response
        ai_response_text = generate_ai_response(
            chat_id=chat_id,
            user_message=user_message,
            conversation_history=conversation_history
        )
        
        if not ai_response_text:
            logger.warning(f'Failed to generate AI response for chat {chat_id}')
            return None
        
        # Create AI message
        ai_message = ChatMessage.objects.create(
            chat=chat,
            sender=None,  # AI messages don't have a sender user
            sender_type='ai',
            content=ai_response_text,
            is_read=False
        )
        
        # Update chat's updated_at timestamp
        chat.save(update_fields=['updated_at'])
        
        return ai_message
        
    except Chat.DoesNotExist:
        logger.error(f'Chat {chat_id} not found')
        return None
    except Exception as e:
        logger.error(f'Error processing AI response: {str(e)}')
        return None
