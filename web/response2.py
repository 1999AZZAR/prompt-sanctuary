import os
import google.generativeai as genai
from dotenv import load_dotenv
from typing import List, Dict, Optional


class GenerativeAI:
    def __init__(self):
        """Initialize the GenerativeAI class with configuration and API keys."""
        self.setup()

    def setup(self):
        """Set up the GenerativeAI instance by loading environment variables and configuring the model."""
        load_dotenv()
        self.api_keys = os.getenv("GENAI_API_KEY").split(",")
        self.current_key_index = 0

        self.generation_config = {
            "temperature": 0.75,  # Controls the randomness of generated responses
            "top_p": 0.65,  # Top-p (nucleus) sampling parameter
            "top_k": 35,  # Top-k filtering parameter for token sampling
            "max_output_tokens": 2048,  # Maximum number of tokens in the generated response
            "stop_sequences": [],  # Sequences to stop generation at
        }

    def get_current_api_key(self) -> str:
        """Get the current API key and rotate to the next key."""
        key = self.api_keys[self.current_key_index]
        self.current_key_index = (self.current_key_index + 1) % len(self.api_keys)
        return key

    def map_threshold(self, parameter_value: str) -> str:
        """Map a parameter value to a safety threshold."""
        threshold_mapping = {
            "none": "BLOCK_NONE",
            "few": "BLOCK_ONLY_HIGH",
            "some": "BLOCK_MEDIUM_AND_ABOVE",
            "most": "BLOCK_LOW_AND_ABOVE",
            "unspecified": "HARM_BLOCK_THRESHOLD_UNSPECIFIED",
        }
        return threshold_mapping.get(parameter_value, "BLOCK_NONE")

    def read_prompt_part_from_file(
        self,
        file_path: str,
        parameter0: str,
        parameter1: str,
        parameter3: str,
        parameter2: Optional[str] = None,
    ) -> str:
        """Read a prompt from a file and replace placeholders with provided parameters."""
        with open(file_path, "r") as file:
            prompt_part = file.read()

        prompt_part = prompt_part.replace("{parameter0}", parameter0 or "")
        prompt_part = prompt_part.replace("{parameter1}", parameter1 or "")
        prompt_part = prompt_part.replace("{parameter2}", parameter2 or "")
        prompt_part = prompt_part.replace(
            "{parameter3}", parameter3 or "ask me on the conversation"
        )

        return prompt_part

    def setup_model(self, parameter2: str):
        """Set up the model with safety settings based on the provided parameter."""
        threshold_value = self.map_threshold(parameter2)

        safety_settings = [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": threshold_value},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": threshold_value},
            {
                "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                "threshold": threshold_value,
            },
            {
                "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                "threshold": threshold_value,
            },
        ]

        genai.configure(api_key=self.get_current_api_key())
        self.model = genai.GenerativeModel(
            model_name="gemini-1.5-pro",
            generation_config=self.generation_config,
            safety_settings=safety_settings,
        )

    def response(
        self,
        parameter0: str,
        parameter1: str,
        parameter2: str,
        parameter3: str,
        file_path: str,
    ) -> str:
        """Generate a response based on the provided parameters and prompt file."""
        self.setup_model(parameter2)
        prompt_part = self.read_prompt_part_from_file(
            file_path, parameter0, parameter1, parameter3, parameter2
        )
        response = self.model.generate_content(prompt_part)
        return response.text
