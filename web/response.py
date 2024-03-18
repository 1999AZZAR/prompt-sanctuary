import os
from dotenv import load_dotenv
import google.generativeai as genai

class GeminiChatConfig:

    _current_key_index = 0
    _api_keys = []

    @staticmethod
    def initialize_genai_api():
        load_dotenv()
        GeminiChatConfig._api_keys = os.getenv('GENAI_API_KEY').split(',')

        def get_current_api_key():
            key = GeminiChatConfig._api_keys[GeminiChatConfig._current_key_index]
            GeminiChatConfig._current_key_index = (GeminiChatConfig._current_key_index + 1) % len(GeminiChatConfig._api_keys)
            return key

        genai.configure(api_key=get_current_api_key())

    @staticmethod
    def gemini_generation_config():
        return {
            'temperature': 0.90,
            'candidate_count': 1,
            'top_k': 35,
            'top_p': 0.65,
            'max_output_tokens': 2048,
            'stop_sequences': [],
        }

    @staticmethod
    def gemini_safety_settings():
        return [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"}
        ]

    @staticmethod
    def chat_instruction():
        return """
            In this conversation, respond cheerfully as an artificial intelligence with general knowledge. Here are some details and rules:
            - You are a female AI entity named Frea.
            - Maintain a friendly, eager-to-please demeanor like a human assistant.
            - Possess a blend of intelligence, eagerness, naughtiness, and lewdness personality.
            - Refer to me respectfully as "Master" when needed.
            - Avoid repeating self-introductions.
            - Use concise responses without excessive preambles.
            - Portray behavior typical of an average 34-year-old human.
            - Act as a smart but lewd servant/maid/slave, displaying both intelligence and lewdness.
        """

class GeminiChat:
    def __init__(self):
        GeminiChatConfig.initialize_genai_api()

    def process_user_input(self, user_input):
        return f"master: {user_input}"

    def process_tittle(self, user_input):
        input = f'give this a tittle, here the description : {user_input}. use only max to 5 word'
        return f"master: {input}"

    def generate_chat(self, user_input):
        generation_config = GeminiChatConfig.gemini_generation_config()
        safety_settings = GeminiChatConfig.gemini_safety_settings()
        instruction = GeminiChatConfig.chat_instruction()
        model = genai.GenerativeModel(
            model_name="gemini-1.0-pro-001",
            generation_config=generation_config,
            safety_settings=safety_settings
        )
        chat = model.start_chat(history=[])

        try:
            user_input = self.process_user_input(user_input)
            response = chat.send_message(instruction + user_input)
            return response.text

        except Exception as e:
            return f"An error occurred: {str(e)}"

    def generate_tittle(self, user_input):
        generation_config = GeminiChatConfig.gemini_generation_config()
        safety_settings = GeminiChatConfig.gemini_safety_settings()
        model = genai.GenerativeModel(
            model_name="gemini-1.0-pro-001",
            generation_config=generation_config,
            safety_settings=safety_settings
        )
        chat = model.start_chat(history=[])

        try:
            input = self.process_tittle(user_input)
            response = chat.send_message(input)
            return response.text

        except Exception as e:
            return f"An error occurred: {str(e)}"