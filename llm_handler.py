import os
import logging
import requests
from typing import Optional
from config import config

logger = logging.getLogger(__name__)

class LLMHandler:
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        """
        Initialize LLM handler with Ollama model

        Args:
            api_key: Not used, kept for compatibility
            model: Model name to use (default from config)
        """
        # Get configuration from config file
        current_config = config.get(os.environ.get('FLASK_ENV', 'development'), config['default'])

        self.model_name = model or current_config.LLM_MODEL
        self.max_tokens = current_config.LLM_MAX_TOKENS
        self.temperature = current_config.LLM_TEMPERATURE
        self.ollama_base_url = current_config.OLLAMA_BASE_URL

        # Check if Ollama is available
        self.enabled = self._check_ollama_availability()
        if self.enabled:
            logger.info(f"Initialized Ollama handler for model {self.model_name}")

    def _check_ollama_availability(self) -> bool:
        """Check if Ollama server is running and model is available"""
        try:
            response = requests.get(f"{self.ollama_base_url}/api/tags", timeout=5)
            if response.status_code == 200:
                models = response.json().get('models', [])
                model_names = [model['name'] for model in models]
                if self.model_name in model_names:
                    logger.info(f"Model {self.model_name} is available on Ollama")
                    return True
                else:
                    logger.warning(f"Model {self.model_name} not found in available models: {model_names}")
            else:
                logger.error(f"Ollama server not responding: {response.status_code}")
        except Exception as e:
            logger.error(f"Failed to connect to Ollama: {e}")
        return False

    def generate_response(self, user_message: str, context: Optional[str] = None) -> str:
        """
        Generate a response using Ollama for queries not covered by intents

        Args:
            user_message: The user's message
            context: Optional context about the chatbot/system (ignored in this implementation)

        Returns:
            Generated response or fallback message
        """
        if not self.enabled:
            return "I'm sorry, I'm currently unable to generate responses. Please try again later."

        try:
            # Prepare the request payload for Ollama
            payload = {
                "model": self.model_name,
                "prompt": user_message,
                "max_tokens": self.max_tokens,
                "temperature": self.temperature,
                "stream": False
            }

            # Make request to Ollama API
            response = requests.post(
                f"{self.ollama_base_url}/api/generate",
                json=payload,
                timeout=30
            )

            if response.status_code == 200:
                result = response.json()
                generated_text = result.get('response', '')
                logger.info(f"Generated response for: '{user_message[:50]}...'")
                return generated_text if generated_text else "I'm sorry, I couldn't generate a response. Please try rephrasing your question."
            else:
                logger.error(f"Ollama API error: {response.status_code} - {response.text}")
                return "I'm experiencing technical difficulties. Please try again later or contact customer support."
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return "I'm experiencing technical difficulties. Please try again later or contact customer support."

    def is_available(self) -> bool:
        """Check if Ollama is available"""
        return self.enabled
