import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()
api_keys = os.getenv('GENAI_API_KEY').split(',')
current_key_index = 0

def get_current_api_key():
    global current_key_index
    key = api_keys[current_key_index]
    current_key_index = (current_key_index + 1) % len(api_keys)
    return key

genai.configure(api_key=get_current_api_key())

generation_config = {
    "temperature": 0.75,
    "top_p": 0.65,
    "top_k": 35,
    "max_output_tokens": 4096,
}

safety_settings = [
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"}
]

model = genai.GenerativeModel(
    model_name="gemini-1.0-pro-vision-latest",
    generation_config=generation_config,
    safety_settings=safety_settings
)

def generate_content(prompt_parts):
    response = model.generate_content(prompt_parts)
    return response.text
