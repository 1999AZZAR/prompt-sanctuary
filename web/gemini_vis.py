import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv('GENAI_API_KEY')
genai.configure(api_key=api_key)

generation_config = {
    "temperature": 0.6,
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
