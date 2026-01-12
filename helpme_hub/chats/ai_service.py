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

logger = logging.getLogger(__name__)


def initialize_gemini():
    """Initialize Google Gemini API client."""
    if genai is None:
        logger.warning('google-generativeai package not available. AI features will not work.')
        return None
    
    api_key = getattr(settings, 'GOOGLE_GEMINI_API_KEY', '')
    if not api_key:
        logger.warning('GOOGLE_GEMINI_API_KEY not set. AI features will not work.')
        return None
    
    try:
        genai.configure(api_key=api_key)
        return genai
    except Exception as e:
        logger.error(f'Failed to initialize Gemini API: {str(e)}')
        return None


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
        return None
    
    # Get model configuration
    model_name = getattr(settings, 'GEMINI_MODEL', 'gemini-1.5-flash')
    max_tokens = getattr(settings, 'GEMINI_MAX_TOKENS', 1000)
    temperature = getattr(settings, 'GEMINI_TEMPERATURE', 0.7)
    
    try:
        # Get the model
        model = genai_client.GenerativeModel(model_name)
        
        # Build conversation context
        system_prompt = """You are a friendly and patient IT support assistant helping people who may not be very tech-savvy. 

IMPORTANT GUIDELINES:
- Use simple, everyday language - avoid technical jargon
- Break down instructions into clear, numbered steps
- Be encouraging and reassuring - many users are frustrated
- Ask clarifying questions if needed (e.g., "What exactly happens when you try to print?")
- For common issues like printers or screens, provide step-by-step troubleshooting
- If the issue is complex or you're unsure, suggest escalating to a human admin
- Always be polite and understanding

Remember: Many users struggle with technology. Be patient, clear, and helpful."""
        
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
        
        # Extract response text
        if response and response.text:
            return response.text.strip()
        else:
            logger.warning('Empty response from Gemini API')
            return None
            
    except Exception as e:
        error_str = str(e)
        logger.error(f'Error generating AI response: {error_str}')
        
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
