import os
import google.generativeai as genai
from dotenv import load_dotenv


class GenerativeAI:
    def __init__(self):
        """Initialize the GenerativeAI class with configuration and API keys."""
        self.setup()

    def setup(self):
        """Set up the GenerativeAI instance by loading environment variables and configuring the model."""
        load_dotenv()
        api_keys = os.getenv("GENAI_API_KEY", "").strip()
        if not api_keys:
            raise ValueError("No GENAI_API_KEY found in environment variables.")
        self.api_keys = [k.strip() for k in api_keys.split(",") if k.strip()]
        if not self.api_keys:
            raise ValueError("GENAI_API_KEY is empty or improperly formatted.")
        self.current_key_index = 0

        # Allow overriding model via env var; default to stable free-tier friendly model
        self.model_name = os.getenv("GENAI_MODEL_NAME", "gemini-2.5-flash")

        self.generation_config = {
            "temperature": 0.75,  # Controls the randomness of generated responses
            "top_p": 0.65,  # Top-p (nucleus) sampling parameter
            "top_k": 35,  # Top-k filtering parameter for token sampling
            "max_output_tokens": 8192,  # Increased from 2048 to allow longer responses
            "stop_sequences": [],
        }

    def get_current_api_key(self) -> str:
        """Get the current API key and rotate to the next key."""
        if not self.api_keys:
            raise RuntimeError("No API keys available.")
        key = self.api_keys[self.current_key_index]
        self.current_key_index = (self.current_key_index + 1) % len(self.api_keys)
        return key

    def map_threshold(self, parameter_value: str) -> str:
        """Map a parameter value to a safety threshold for the model."""
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
        parameter0: str = "",
        parameter1: str = "",
        parameter2: str = "",
        parameter3: str = "ask me on the conversation",
    ) -> str:
        """
        Read a prompt from a file and replace placeholders with provided parameters.
        Placeholders: {parameter0}, {parameter1}, {parameter2}, {parameter3}
        """
        # Resolve relative paths against this file's directory
        if not os.path.isabs(file_path):
            base_dir = os.path.dirname(__file__)
            normalized = file_path[2:] if file_path.startswith("./") else file_path
            file_path = os.path.join(base_dir, normalized)
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
        """
        Set up the model with safety settings based on the provided parameter.
        parameter2: string indicating the safety threshold (e.g., 'none', 'few', etc.)
        """
        threshold_value = self.map_threshold(parameter2)
        safety_settings = [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": threshold_value},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": threshold_value},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": threshold_value},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": threshold_value},
        ]
        genai.configure(api_key=self.get_current_api_key())
        self.model = genai.GenerativeModel(
            model_name=self.model_name,
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
        """
        Generate a response based on the provided parameters and prompt file.
        Parameters are slotted into the prompt template file.
        """
        prompt_part = self.read_prompt_part_from_file(
            file_path=file_path,
            parameter0=parameter0,
            parameter1=parameter1,
            parameter2=parameter2,
            parameter3=parameter3,
        )
        last_error = None
        for _ in range(len(self.api_keys)):
            self.setup_model(parameter2)
            try:
                response = self.model.generate_content(prompt_part)
                return response.text
            except Exception as e:
                last_error = e
                continue
        raise RuntimeError(f"All API keys failed. Last error: {last_error}")
