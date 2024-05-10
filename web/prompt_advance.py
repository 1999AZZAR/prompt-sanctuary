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
def read_prompt_parts_from_file(file_path, parameter0, parameter1, parameter3):
    with open(file_path, 'r') as file:
        prompt_parts = file.read()
    # replace parameters
    if '{parameter0}' in prompt_parts and parameter0 is not None:
        prompt_parts = prompt_parts.replace('{parameter0}', parameter0)
    if '{parameter1}' in prompt_parts and parameter1 is not None:
        prompt_parts = prompt_parts.replace('{parameter1}', parameter1)
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
    prompt_parts = read_prompt_parts_from_file('./instruction/parameters.txt', parameter0, parameter1, parameter3)
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

    # prompt example and user input
    prompt_parts = [
        " ",
        "input: Start your description with the word 'imagine,' e.g., 'imagine a mystical forest shrouded in fog...'\n\nwrite me a detailed possible image description about a lone traveler on a mist-covered path. The description should convey the mood of solitude, mystery, and anticipation, with a primary style of atmospheric and a secondary stylistic element of surrealism. Elaborate on any relevant details in the image and ensure the tone matches the specified mood.",
        "output: Imagine a lone traveler on a mist-covered path. The scene is filled with an air of solitude, mystery, and anticipation. The primary style is atmospheric, with surrealism as a secondary element. Picture a winding path cutting through a dense forest, its edges disappearing into thick mist. The air is heavy with silence, broken only by the occasional rustle of leaves or distant birdcall. A solitary figure walks along the path, their silhouette barely visible through the fog. They exude determination, yet there's a hint of apprehension in their movements. The mist swirls and shifts, creating an ever-changing landscape that plays tricks on the mind. Shapes loom in the haze, indistinct and fleeting, adding to the sense of mystery and intrigue.",
        "input: Start your description with the word 'imagine,' e.g., 'imagine a futuristic cityscape bathed in neon lights...'\n\nwrite me a detailed possible image description about a cybernetic creature in a futuristic metropolis. The description should convey the mood of awe, wonder, and technological advancement, with a primary style of cyberpunk and a secondary stylistic element of futuristic. Elaborate on any relevant details in the image and ensure the tone matches the specified mood.",
        "output: Imagine a cybernetic creature in a futuristic metropolis. The mood is one of awe, wonder, and technological advancement. The primary style is cyberpunk, with a secondary element of futuristic. Picture a sprawling metropolis of towering skyscrapers and neon-lit streets. Hovercrafts zip through the air, holographic billboards flicker and change, and amidst it all stands a cybernetic creature. Its metallic body gleams in the neon glow as it moves with fluid grace. The cityscape is alive with activity, a symphony of light and sound. Neon signs cast vibrant colors onto the streets below, and flying cars streak through the sky, leaving trails of light in their wake. Drones buzz overhead, performing various tasks, adding to the sense of technological wonder.",
        "input: Start your description with the word 'imagine,' e.g., 'imagine a vast desert under a starry sky...'\n\nwrite me a detailed possible image description about a nomadic tribe camped beneath a canopy of stars. The description should convey the mood of unity, freedom, and wonder, with a primary style of naturalistic and a secondary stylistic element of ethereal. Elaborate on any relevant details in the image and ensure the tone matches the specified mood.",
        "output: Imagine a nomadic tribe camped beneath a canopy of stars. The mood is one of unity, freedom, and wonder. The primary style is naturalistic, with an ethereal quality. Picture a vast desert landscape stretching out in all directions, the sand shimmering in the moonlight. A small encampment sits at the center, with tents and makeshift shelters arranged in a circle. A crackling fire casts a warm glow, its flames dancing in the darkness. The night sky above is a breathtaking sight, filled with countless stars and the faint glow of the Milky Way. The air is alive with the sound of laughter and conversation, as the tribe gathers around the fire, sharing stories and traditions passed down through generations.",
        "input: Start your description with the word 'imagine,' e.g., 'imagine a bustling city street during a rainstorm...'\n\nwrite me a detailed possible image description about a futuristic cityscape during a thunderstorm. The description should convey the mood of intensity, drama, and anticipation, with a primary style of cyberpunk and a secondary stylistic element of dramatic. Elaborate on any relevant details in the image and ensure the tone matches the specified mood.",
        "output: Imagine a futuristic cityscape during a thunderstorm. The mood is one of intensity, drama, and anticipation. The primary style is cyberpunk, with a secondary element of dramatic. Picture towering skyscrapers reaching towards the stormy sky, their sleek surfaces slick with rain. Lightning arcs across the sky, illuminating the city in flashes of electric blue. The streets below are deserted, the usual hustle and bustle replaced by an eerie silence. Rain pours down in sheets, turning the pavement into rivers of water. Thunder rumbles in the distance, echoing off the buildings and adding to the sense of foreboding. Despite the chaos of the storm, there's a beauty to the scene, a raw power that captivates the imagination.",
        "input: Start your description with the word 'imagine,' e.g., 'imagine an ancient ruin hidden in the jungle...'\n\nwrite me a detailed possible image description about an abandoned space station drifting through the cosmos. The description should convey the mood of loneliness, isolation, and cosmic grandeur, with a primary style of futuristic and a secondary stylistic element of surrealism. Elaborate on any relevant details in the image and ensure the tone matches the specified mood.",
        "output: Imagine an abandoned space station drifting through the cosmos. The mood is one of loneliness, isolation, and cosmic grandeur. The primary style is futuristic, with a secondary element of surrealism. Picture a vast expanse of space stretching out in all directions, dotted with stars and distant galaxies. The space station floats silently in the void, its metal hull scarred and pitted from years of neglect. Broken solar panels hang limply from its sides, and shattered windows reveal empty corridors and darkened rooms within. Despite its derelict state, there's a sense of beauty to the station, a reminder of humanity's quest to explore the cosmos. But now, it drifts alone, a silent monument to the vastness of space.",
        f"input: Start your description with the word 'imagine,' e.g., 'imagine a {parameter1} image in a {parameter2} setting with {parameter3} elements...'\n\nwrite me a detailed possible image description about {parameter0}. The description should convey the mood of {parameter1}. and have a primary style of {parameter2} with {parameter3} as a secondary stylistic element. Elaborate on any relevant details in the image and ensure the tone matches the specified mood.",
        "output: ",
    ]

    response = model.generate_content(prompt_parts)
    return response.text