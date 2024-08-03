import os
import google.generativeai as genai
from dotenv import load_dotenv
import random

class GenerativeModel:
    def __init__(self):
        # Load the .env file
        load_dotenv()
        self.api_keys = os.getenv('GENAI_API_KEY').split(',')
        self.current_key_index = 0

        # Get the API key
        genai.configure(api_key=self.get_current_api_key())

        # Set up the model
        self.generation_config = {
            "temperature": 0.75,
            "top_p": 0.65,
            "top_k": 35,
            "max_output_tokens": 2048,
            'stop_sequences': [],
        }

        # Safety settings
        self.safety_settings = [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"}
        ]

        # Model settings
        self.model = genai.GenerativeModel(
            model_name="gemini-1.5-pro",
            generation_config=self.generation_config,
            safety_settings=self.safety_settings,
        )

    def get_current_api_key(self):
        key = self.api_keys[self.current_key_index]
        self.current_key_index = (self.current_key_index + 1) % len(self.api_keys)
        return key

    def read_prompt_part_from_file(self, file_path, user_input_text=''):
        with open(file_path, 'r') as file:
            prompt_part = file.read()
        # Replace {user_input_text} with actual user input if provided
        if user_input_text:
            if '{user_input_text}' in prompt_part:
                prompt_part = prompt_part.replace('{user_input_text}', user_input_text)
        return prompt_part

    def generate_response(self, prompt_file_path, user_input_text):
        prompt_part = self.read_prompt_part_from_file(prompt_file_path, user_input_text)
        response = self.model.generate_content(prompt_part)
        return response.text

    def generate_random(self, prompt_file_path):
        prompt_part = self.read_prompt_part_from_file(prompt_file_path)
        response = self.model.generate_content(prompt_part)
        return response.text

    def generate_imgdescription(self, image_styles_file_path, user_input_image):
        with open(image_styles_file_path, 'r') as file:
            image_styles = [line.strip() for line in file.readlines()]

        chosen_styles = random.sample(image_styles, k=3)
        prompt_part = [
            " ",
            f"Input: Use the following styles ({', '.join(chosen_styles)}) to create a compelling image description about {user_input_image}. if possible Incorporate elements all of those styles into your description. Your narrative should be between 200 to 400 characters, evoking a vivid and imaginative scene. Start your description with the word 'imagine,' e.g., 'imagine a hyperrealistic portrait in a dreamlike landscape...'",
            "Output: ",
        ]
        response = self.model.generate_content(prompt_part)
        return response.text

    def generate_vrandom(self, image_styles_file_path):
        with open(image_styles_file_path, 'r') as file:
            image_styles = [line.strip() for line in file.readlines()]

        chosen_styles = random.sample(image_styles, k=3)
        prompt_part = [
            " ",
            f"Input: Use the following styles ({', '.join(chosen_styles)}) to create a compelling image description. if possible Incorporate elements all of those styles into your description. Your narrative should be between 200 to 1000 characters, evoking a vivid and imaginative scene. Start your description with the word 'imagine,' e.g., 'imagine a hyperrealistic portrait in a dreamlike landscape...'",
            "Output: ",
        ]
        response = self.model.generate_content(prompt_part)
        return response.text

    def generate_visual(self, image_styles_file_path, image_data):
        with open(image_styles_file_path, 'r') as file:
            image_styles = [line.strip() for line in file.readlines()]

        chosen_styles = random.sample(image_styles, k=3)
        prompt_part = [
            "\nPlease provide a detailed description, written in proper English, to recreate this image in 250 to 500 words. Include information about the style, mood, lighting, and other important details. Ensure your sentences are complete and free from spelling and grammar errors:",
            {"mime_type": "image/jpeg", "data": image_data},
            f"\nPlease select and use up to four different artistic styles from the following list: \n{', '.join(image_styles)}\nYou can choose the same style multiple times if desired.",
            "Try to make your description as similar as possible to the original image, just like an audio describer would. Remember to begin your description with the word 'imagine.' For example, 'imagine a red-hooded woman in the forest...'",
        ]
        response = self.model.generate_content(prompt_part)
        return response.text

    def generate_visual2 (self, image_data, parameter1, parameter2, parameter3):
        prompt_part = [
            "\nPlease provide a detailed description in proper English to recreate this image in 250 to 500 words. Include information about the style, mood, lighting, and other key details. Ensure your sentences are complete and free from spelling and grammar errors:",
            {"mime_type": "image/jpeg", "data": image_data},
            f"\nAdditionally, incorporate the '{parameter1}' mood into the image description.",
            f"\nFor the image style, please adopt the '{parameter2}' style as the main style, with '{parameter3}' serving as the secondary style.",
            "\nEnsure that your description is rich in detail and structure.",
            "\nTry to make your description as similar as possible to the original image with the adjustments I have requested, just like an audio describer would.",
            "\nRemember to begin your description with the word 'imagine.' For example, 'imagine a red-hooded woman in the forest...'",
        ]
        response = self.model.generate_content(prompt_part)
        return response.text
