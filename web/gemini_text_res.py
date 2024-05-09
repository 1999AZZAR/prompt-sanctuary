import os
from dotenv import load_dotenv
import google.generativeai as genai
from typing import List, Dict

# class config for the gemini chat model
class GeminiChatConfig:

    _current_key_index = 0
    _api_keys = []
    INSTRUCTION_FILE = './instruction/medusa.txt'

    # model initialization
    @staticmethod
    def initialize_genai_api():
        load_dotenv()
        GeminiChatConfig._api_keys = os.getenv('GENAI_API_KEY').split(',')

        def get_current_api_key():
            key = GeminiChatConfig._api_keys[GeminiChatConfig._current_key_index]
            GeminiChatConfig._current_key_index = (GeminiChatConfig._current_key_index + 1) % len(GeminiChatConfig._api_keys)
            return key

        genai.configure(api_key=get_current_api_key())

    # model configuration
    @staticmethod
    def gemini_generation_config():
        return {
            'temperature': 0.90,        # Controls the randomness of generated responses
            'candidate_count': 1,       # Number of candidate responses to generate
            'top_k': 35,                # Top-k filtering parameter for token sampling
            'top_p': 0.65,              # Top-p (nucleus) sampling parameter
            'max_output_tokens': 2048,  # Maximum number of tokens in the generated response
            'stop_sequences': [],       # Sequences to stop generation at
        }

    # safety settings
    @staticmethod
    def gemini_safety_settings():
        return [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"}
        ]

    # instruction for the model
    @staticmethod
    def chat_instruction():
        with open(GeminiChatConfig.INSTRUCTION_FILE, 'r') as file:
            return file.read()

# gemini chat config
class GeminiChat:
    # load the config and history
    def __init__(self):
        GeminiChatConfig.initialize_genai_api()
        self.history = []
        self.model = None  # Initialize model as None

    # generate chat
    def generate_chat(self, user_input: str) -> str:
        if user_input.strip().lower() == "reset":
            self.history.clear()  # Clear history
            self.model = None  # Reset model
            return "Reset success, and history has been cleared."

        if self.model is None:
            # Get generation configuration and safety settings
            generation_config = GeminiChatConfig.gemini_generation_config()
            safety_settings = GeminiChatConfig.gemini_safety_settings()
            instruction = GeminiChatConfig.chat_instruction()
        else:
            instruction = ""  # If model is already initialized, no need for instruction

        try:
            if self.model is None:
                # Initialize the GenerativeModel for Gemini Chat
                self.model = genai.GenerativeModel(
                    model_name="gemini-1.5-pro-latest",
                    generation_config=generation_config,
                    safety_settings=safety_settings
                )

            # Prepare user input for AI model and generate response
            chat = self.model.start_chat(history=self.history)
            response = chat.send_message(instruction + user_input)
            response = f"{response.text}"
            # Update conversation history
            self.history.append({"role": "user", "parts": [user_input]})
            self.history.append({"role": "model", "parts": [response]})
            return response

        except Exception as e:
            return f"An error occurred: {str(e)}"

    # generate the tittle from user input
    def generate_tittle(self, user_input):
        generation_config = GeminiChatConfig.gemini_generation_config()
        safety_settings = GeminiChatConfig.gemini_safety_settings()
        model = genai.GenerativeModel(
            model_name="gemini-1.5-pro-latest",
            generation_config=generation_config,
            safety_settings=safety_settings
        )
        chat = model.start_chat(history=[])

        # process the input
        try:
            input = f'give this a tittle, here the description : {user_input}. use only max to 5 word'
            response = chat.send_message(input)
            return response.text

        # error exception
        except Exception as e:
            return f"An error occurred: {str(e)}"