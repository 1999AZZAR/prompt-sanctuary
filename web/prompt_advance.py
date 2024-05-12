import os
import google.generativeai as genai
from dotenv import load_dotenv

# read the .env file
load_dotenv()
api_keys = os.getenv('GENAI_API_KEY').split(',')
current_key_index = 0

# get the api key for the model
def get_current_api_key():
    global current_key_index
    key = api_keys[current_key_index]
    current_key_index = (current_key_index + 1) % len(api_keys)
    return key

genai.configure(api_key=get_current_api_key())


# general config
generation_config = {
    "temperature": 0.75,        # Controls the randomness of generated responses
    "top_p": 0.65,              # Top-p (nucleus) sampling parameter
    "top_k": 35,                # Top-k filtering parameter for token sampling
    "max_output_tokens": 2048,  # Maximum number of tokens in the generated response
    'stop_sequences': [],       # Sequences to stop generation at
}


# map the threshold
def map_threshold(parameter_value):
    if parameter_value == "none":
        return "BLOCK_NONE"
    elif parameter_value == "few":
        return "BLOCK_ONLY_HIGH"
    elif parameter_value == "some":
        return "BLOCK_MEDIUM_AND_ABOVE"
    elif parameter_value == "most":
        return "BLOCK_LOW_AND_ABOVE"
    elif parameter_value == "unspecified":
        return "HARM_BLOCK_THRESHOLD_UNSPECIFIED"
    else:
        return "BLOCK_NONE"


# Read the prompt parts from the file
def read_prompt_parts_from_file(file_path, parameter0, parameter1, parameter3, parameter2=None):
    with open(file_path, 'r') as file:
        prompt_parts = file.read()
    # replace parameters
    if '{parameter0}' in prompt_parts and parameter0 is not None:
        prompt_parts = prompt_parts.replace('{parameter0}', parameter0)
    if '{parameter1}' in prompt_parts and parameter1 is not None:
        prompt_parts = prompt_parts.replace('{parameter1}', parameter1)
    if '{parameter2}' in prompt_parts and parameter2 is not None:
        prompt_parts = prompt_parts.replace('{parameter2}', parameter2)
    if '{parameter3}' in prompt_parts:
        if parameter3 is not None:
            prompt_parts = prompt_parts.replace('{parameter3}', parameter3)
        else:
            prompt_parts = prompt_parts.replace('{parameter3}', "ask me on the conversation")
    return prompt_parts


# generate text prompt response.
def response(parameter0, parameter1, parameter2, parameter3):
    threshold_value = map_threshold(parameter2)
    
    # safety threshold settings
    safety_settings = [
        {"category": "HARM_CATEGORY_HARASSMENT", "threshold": threshold_value},
        {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": threshold_value},
        {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": threshold_value},
        {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": threshold_value}
    ]

    # model call
    model = genai.GenerativeModel(
        model_name="gemini-1.5-pro-latest",
        generation_config=generation_config,
        safety_settings=safety_settings,
    )

    # prompt part input and examples for the model
    prompt_parts = read_prompt_parts_from_file('./instruction/parameters.txt', parameter0, parameter1, parameter2, parameter3)
    response = model.generate_content(prompt_parts)
    return response.text


# generate image prompt response
def iresponse(parameter0, parameter1, parameter2, parameter3):
    threshold_value = map_threshold("none")
    
    # safety settings
    safety_settings = [
        {"category": "HARM_CATEGORY_HARASSMENT", "threshold": threshold_value},
        {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": threshold_value},
        {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": threshold_value},
        {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": threshold_value}
    ]

    # model settings
    model = genai.GenerativeModel(
        model_name="gemini-1.5-pro-latest",
        generation_config=generation_config,
        safety_settings=safety_settings,
    )

    prompt_parts = read_prompt_parts_from_file('./instruction/parameters2.txt', parameter0, parameter1, parameter2, parameter3)

    response = model.generate_content(prompt_parts)
    return response.text
