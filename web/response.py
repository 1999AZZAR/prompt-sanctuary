import os
import google.generativeai as genai
from dotenv import load_dotenv
import random
from typing import List, Dict, Any


class GenerativeModel:
    def __init__(self):
        """Initialize the GenerativeModel with API keys, configuration, and safety settings."""
        load_dotenv()
        self.api_keys = os.getenv("GENAI_API_KEY").split(",")
        self.current_key_index = 0
        genai.configure(api_key=self.get_current_api_key())

        self.generation_config = {
            "temperature": 0.75,
            "top_p": 0.65,
            "top_k": 35,
            "max_output_tokens": 2048,
            "stop_sequences": [],
        }

        self.safety_settings = [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
        ]

        self.model = genai.GenerativeModel(
            model_name="gemini-2.5-flash-preview-04-17",
            generation_config=self.generation_config,
            safety_settings=self.safety_settings,
        )

    def get_current_api_key(self) -> str:
        """Get the current API key and rotate to the next key."""
        key = self.api_keys[self.current_key_index]
        self.current_key_index = (self.current_key_index + 1) % len(self.api_keys)
        return key

    def read_prompt_part_from_file(
        self, file_path: str, user_input_text: str = ""
    ) -> str:
        """Read a prompt from a file and optionally replace placeholders with user input."""
        with open(file_path, "r") as file:
            prompt_part = file.read()
        if user_input_text and "{user_input_text}" in prompt_part:
            prompt_part = prompt_part.replace("{user_input_text}", user_input_text)
        return prompt_part

    def generate_response(self, prompt_file_path: str, user_input_text: str) -> str:
        """Generate a response based on a prompt file and user input."""
        prompt_part = self.read_prompt_part_from_file(prompt_file_path, user_input_text)
        last_error = None
        for _ in range(len(self.api_keys)):
            genai.configure(api_key=self.get_current_api_key())
            self.model = genai.GenerativeModel(
                model_name="gemini-2.5-flash-preview-04-17",
                generation_config=self.generation_config,
                safety_settings=self.safety_settings,
            )
            try:
                response = self.model.generate_content(prompt_part)
                return response.text
            except Exception as e:
                last_error = e
                continue
        raise last_error

    def generate_random(self, prompt_file_path: str) -> str:
        """Generate a random response based on a prompt file."""
        prompt_part = self.read_prompt_part_from_file(prompt_file_path)
        last_error = None
        for _ in range(len(self.api_keys)):
            genai.configure(api_key=self.get_current_api_key())
            self.model = genai.GenerativeModel(
                model_name="gemini-2.5-flash-preview-04-17",
                generation_config=self.generation_config,
                safety_settings=self.safety_settings,
            )
            try:
                response = self.model.generate_content(prompt_part)
                return response.text
            except Exception as e:
                last_error = e
                continue
        raise last_error

    def _generate_image_description_prompt(
        self, styles: List[str], user_input: str = None
    ) -> List[Any]:
        """Generate a prompt for image description based on styles and optional user input."""
        prompt_part = [
            " ",
            f"Input: Use the following styles ({', '.join(styles)}) to create a compelling image description{f' about {user_input}' if user_input else ''}. "
            f"Incorporate elements of all those styles into your description. Your narrative should be between 200 to 400 characters, "
            "evoking a vivid and imaginative scene. Start your description with the word 'imagine,' e.g., 'imagine a hyperrealistic portrait in a dreamlike landscape...'",
            "Output: ",
        ]
        return prompt_part

    def generate_imgdescription(
        self, image_styles_file_path: str, user_input_image: str
    ) -> str:
        """Generate an image description based on styles and user input."""
        styles = self._read_styles_from_file(image_styles_file_path)
        chosen_styles = random.sample(styles, k=3)
        prompt_part = self._generate_image_description_prompt(
            chosen_styles, user_input_image
        )
        response = self.model.generate_content(prompt_part)
        return response.text

    def generate_vrandom(self, image_styles_file_path: str) -> str:
        """Generate a random image description based on styles."""
        styles = self._read_styles_from_file(image_styles_file_path)
        chosen_styles = random.sample(styles, k=3)
        prompt_part = self._generate_image_description_prompt(chosen_styles)
        response = self.model.generate_content(prompt_part)
        return response.text

    def _read_styles_from_file(self, file_path: str) -> List[str]:
        """Read styles from a file and return them as a list."""
        with open(file_path, "r") as file:
            return [line.strip() for line in file.readlines()]

    def generate_visual(self, image_styles_file_path: str, image_data: bytes) -> str:
        """Generate a detailed description of an image based on styles and image data."""
        styles = self._read_styles_from_file(image_styles_file_path)
        chosen_styles = random.sample(styles, k=3)
        prompt_part = [
            "\nPlease provide a detailed description, written in proper English, to recreate this image in 250 to 500 words. "
            "Include information about the style, mood, lighting, and other important details. Ensure your sentences are complete "
            "and free from spelling and grammar errors:",
            {"mime_type": "image/jpeg", "data": image_data},
            f"\nPlease select and use up to four different artistic styles from the following list: \n{', '.join(styles)}\n"
            "You can choose the same style multiple times if desired.",
            "Try to make your description as similar as possible to the original image, just like an audio describer would. "
            "Remember to begin your description with the word 'imagine.' For example, 'imagine a red-hooded woman in the forest...'",
        ]
        response = self.model.generate_content(prompt_part)
        return response.text

    def generate_visual2(
        self, image_data: bytes, parameter1: str, parameter2: str, parameter3: str
    ) -> str:
        """Generate a detailed description of an image with specific parameters."""
        prompt_part = [
            "\nPlease provide a detailed description in proper English to recreate this image in 250 to 500 words. "
            "Include information about the style, mood, lighting, and other key details. Ensure your sentences are complete "
            "and free from spelling and grammar errors:",
            {"mime_type": "image/jpeg", "data": image_data},
            f"\nAdditionally, incorporate the '{parameter1}' mood into the image description.",
            f"\nFor the image style, please adopt the '{parameter2}' style as the main style, with '{parameter3}' serving as the secondary style.",
            "\nEnsure that your description is rich in detail and structure.",
            "\nTry to make your description as similar as possible to the original image with the adjustments I have requested, "
            "just like an audio describer would.",
            "\nRemember to begin your description with the word 'imagine.' For example, 'imagine a red-hooded woman in the forest...'",
        ]
        response = self.model.generate_content(prompt_part)
        return response.text
