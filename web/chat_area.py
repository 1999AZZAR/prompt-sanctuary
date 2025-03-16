import os
from dotenv import load_dotenv
import google.generativeai as genai
from typing import List, Dict, Optional
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
INSTRUCTION_FILE = "./instruction/simulat.txt"


class GeminiChatConfig:
    _current_key_index = 0
    _api_keys: List[str] = []

    @staticmethod
    def initialize_genai_api():
        """Initialize the GenAI API with the API keys from environment variables."""
        load_dotenv()
        api_keys = os.getenv("GENAI_API_KEY")
        if api_keys:
            GeminiChatConfig._api_keys = api_keys.split(",")
        else:
            raise ValueError("GENAI_API_KEY environment variable not set.")

    @staticmethod
    def get_current_api_key() -> str:
        """Get the current API key and rotate to the next key."""
        if not GeminiChatConfig._api_keys:
            raise ValueError("No API keys available.")
        key = GeminiChatConfig._api_keys[GeminiChatConfig._current_key_index]
        GeminiChatConfig._current_key_index = (
            GeminiChatConfig._current_key_index + 1
        ) % len(GeminiChatConfig._api_keys)
        return key

    @staticmethod
    def gemini_generation_config() -> Dict:
        """Get the generation configuration for the Gemini model."""
        return {
            "temperature": 0.90,
            "candidate_count": 1,
            "top_k": 35,
            "top_p": 0.65,
            "max_output_tokens": 2048,
            "stop_sequences": [],
        }

    @staticmethod
    def gemini_safety_settings() -> List[Dict]:
        """Get the safety settings for the Gemini model."""
        return [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
        ]

    @staticmethod
    def chat_instruction() -> str:
        """Read the instruction file for the chat model."""
        try:
            with open(INSTRUCTION_FILE, "r") as file:
                return file.read()
        except Exception as e:
            logger.error(f"Error reading instruction file: {e}")
            return ""


class GeminiChat:
    def __init__(self):
        """Initialize the GeminiChat with configuration and history."""
        GeminiChatConfig.initialize_genai_api()
        self.history: List[Dict] = []
        self.model: Optional[genai.GenerativeModel] = None

    def _initialize_model(self):
        """Initialize the Gemini model if not already initialized."""
        if self.model is None:
            generation_config = GeminiChatConfig.gemini_generation_config()
            safety_settings = GeminiChatConfig.gemini_safety_settings()
            self.model = genai.GenerativeModel(
                model_name="gemini-1.5-pro",
                generation_config=generation_config,
                safety_settings=safety_settings,
            )

    def generate_chat(self, user_input: str) -> str:
        """Generate a chat response based on user input."""
        if user_input.strip().lower() == "reset":
            self.history.clear()
            self.model = None
            return "Reset success, and history has been cleared."

        self._initialize_model()
        instruction = GeminiChatConfig.chat_instruction()

        try:
            chat = self.model.start_chat(history=self.history)
            response = chat.send_message(instruction + user_input)
            response_text = f"{response.text}"
            self.history.append({"role": "user", "parts": [user_input]})
            self.history.append({"role": "model", "parts": [response_text]})
            return response_text
        except Exception as e:
            logger.error(f"Error generating chat response: {e}")
            return f"An error occurred: {str(e)}"

    def generate_title(self, user_input: str) -> str:
        """Generate a title based on user input."""
        self._initialize_model()
        try:
            input_text = f"Give this a title, here is the description: {user_input}. Use a maximum of 5 words."
            chat = self.model.start_chat(history=[])
            response = chat.send_message(input_text)
            return response.text
        except Exception as e:
            logger.error(f"Error generating title: {e}")
            return f"An error occurred: {str(e)}"
