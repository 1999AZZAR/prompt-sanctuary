import os
import time
import logging
import json
import re
import google.generativeai as genai
from dotenv import load_dotenv
import random
from typing import List, Dict, Any, Optional, Tuple


class GenerativeModel:
    def __init__(self):
        """Initialize the GenerativeModel with API keys, configuration, and safety settings."""
        load_dotenv()
        self.api_keys = os.getenv("GENAI_API_KEY").split(",")
        self.current_key_index = 0
        # Allow overriding model via env var; default to stable free-tier friendly model
        self.model_name = os.getenv("GENAI_MODEL_NAME", "gemini-2.5-flash")
        self.user_api_key = None  # For storing user-provided API keys
        self.current_user = None  # For tracking which user is making the request
        self.user_db_path = "database/user.db"  # Default database path
        # Enable streaming by default for better response handling
        self.streaming_enabled = os.getenv("ENABLE_STREAMING", "true").lower() == "true"
        genai.configure(api_key=self.get_current_api_key())

        # Key health telemetry
        self.key_health: Dict[str, Dict[str, Any]] = {}
        for k in self.api_keys:
            self.key_health[self._mask_key(k)] = {
                "successes": 0,
                "failures": 0,
                "last_error": "",
                "last_used": 0.0,
            }

        self.generation_config = {
            "temperature": 0.75,
            "top_p": 0.65,
            "top_k": 35,
            "max_output_tokens": 8192,  # Increased from 2048 to allow longer responses
            "stop_sequences": [],
        }

        self.safety_settings = [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
        ]

        self.model = genai.GenerativeModel(
            model_name=self.model_name,
            generation_config=self.generation_config,
            safety_settings=self.safety_settings,
        )

    def get_current_api_key(self) -> str:
        """Get the current API key and rotate to the next key."""
        key = self.api_keys[self.current_key_index]
        self.current_key_index = (self.current_key_index + 1) % len(self.api_keys)
        return key

    def set_user_api_key(self, api_key: str):
        """Set a user-provided API key to use for generation."""
        self.user_api_key = api_key

    def clear_user_api_key(self):
        """Clear the user-provided API key."""
        self.user_api_key = None
    
    def set_current_user(self, username: str):
        """Set the current user for API key pool management."""
        self.current_user = username
    
    def set_user_db_path(self, db_path: str):
        """Set the user database path for API key pool management."""
        self.user_db_path = db_path

    def get_effective_api_key(self) -> str:
        """Get the API key to use (user key if available, otherwise system key)."""
        return self.user_api_key if self.user_api_key else self.get_current_api_key()
    
    def get_system_api_key(self) -> Tuple[Optional[str], Optional[str]]:
        """Get a system API key from the pool for generating content for other users."""
        try:
            from api_key_pool import use_system_api_key
            return use_system_api_key(self.user_db_path, self.current_user)
        except Exception as e:
            logging.exception("Failed to get system API key from pool")
            return None, None

    def _mask_key(self, key: str) -> str:
        return f"***{key[-4:]}" if key else "(none)"

    def _record_success(self, key: str):
        masked = self._mask_key(key)
        if masked in self.key_health:
            self.key_health[masked]["successes"] += 1
            self.key_health[masked]["last_error"] = ""
            self.key_health[masked]["last_used"] = time.time()

    def _record_failure(self, key: str, error: Exception):
        masked = self._mask_key(key)
        if masked in self.key_health:
            self.key_health[masked]["failures"] += 1
            self.key_health[masked]["last_error"] = str(error)
            self.key_health[masked]["last_used"] = time.time()

    def get_health(self) -> Dict[str, Any]:
        return {
            "model": self.model_name,
            "keys": self.key_health,
        }

    def _resolve_path(self, path: str) -> str:
        """Resolve relative paths against this file's directory."""
        if os.path.isabs(path):
            return path
        base_dir = os.path.dirname(__file__)
        # Strip leading "./" to avoid creating redundant segments
        normalized = path[2:] if path.startswith("./") else path
        return os.path.join(base_dir, normalized)

    def read_prompt_part_from_file(
        self, file_path: str, user_input_text: str = ""
    ) -> str:
        """Read a prompt from a file and optionally replace placeholders with user input."""
        resolved_path = self._resolve_path(file_path)
        with open(resolved_path, "r") as file:
            prompt_part = file.read()
        if user_input_text and "{user_input_text}" in prompt_part:
            prompt_part = prompt_part.replace("{user_input_text}", user_input_text)
        return prompt_part

    def _extract_text(self, response: any) -> str:
        """Safely extract text from Gemini response, even if quick accessor fails."""
        try:
            # Preferred quick accessor
            if hasattr(response, 'text'):
                txt = response.text  # may raise ValueError
                if txt:
                    return self._clean_ai_response(txt)
        except Exception:
            pass

        # Fallback to candidates/parts
        try:
            candidates = getattr(response, 'candidates', None) or []
            for cand in candidates:
                content = getattr(cand, 'content', None)
                parts = getattr(content, 'parts', None) if content else None
                if parts:
                    texts = []
                    for p in parts:
                        t = getattr(p, 'text', None)
                        if t:
                            texts.append(t)
                    if texts:
                        return self._clean_ai_response("\n".join(texts))
        except Exception:
            pass

        return ""

    def _clean_ai_response(self, text: str) -> str:
        """Clean AI response to remove unwanted formatting while preserving markdown structure."""
        if not text:
            return ""

        # Remove any JSON-like structure that might have been accidentally generated
        text = text.strip()

        # If it looks like JSON, try to extract the actual content
        if text.startswith('{') and text.endswith('}'):
            try:
                parsed = json.loads(text)
                # Look for common response keys
                for key in ['response', 'text', 'content', 'message', 'result']:
                    if key in parsed and isinstance(parsed[key], str):
                        text = parsed[key]
                        break
                # If it has success: true, extract the main content
                if 'success' in parsed and parsed.get('success') is True:
                    for key, value in parsed.items():
                        if key != 'success' and isinstance(value, str):
                            text = value
                            break
                elif isinstance(parsed, str):
                    text = parsed
            except (json.JSONDecodeError, TypeError):
                pass

        # Clean up formatting artifacts while preserving markdown structure
        cleaned = text

        # Convert escaped characters to actual characters
        cleaned = cleaned.replace('\\n', '\n')  # Escaped newlines -> actual newlines
        cleaned = cleaned.replace('\\"', '"')   # Escaped quotes -> actual quotes
        cleaned = cleaned.replace('\\\\', '\\') # Escaped backslashes -> actual backslashes
        cleaned = cleaned.replace('\\t', '    ') # Escaped tabs -> 4 spaces (markdown indent)

        # Decode HTML entities
        cleaned = cleaned.replace('&lt;', '<')
        cleaned = cleaned.replace('&gt;', '>')
        cleaned = cleaned.replace('&amp;', '&')
        cleaned = cleaned.replace('&quot;', '"')

        # Normalize line endings for consistent parsing
        cleaned = cleaned.replace('\r\n', '\n').replace('\r', '\n')

        # Fix non-standard markdown formatting (apply in specific order to avoid conflicts)
        # First: Fix double hash with brackets: # # [Header] -> ## Header
        cleaned = re.sub(r'^# # \[([^\]]+)\]$', r'## \1', cleaned, flags=re.MULTILINE)

        # Second: Convert square bracket headers (these take priority)
        cleaned = re.sub(r'^\[([^\]]+)\]\*?$', r'## \1', cleaned, flags=re.MULTILINE)  # Convert [Header]* or [Header] to ## Header

        # Third: Convert standalone asterisks to list markers (but avoid headers)
        cleaned = re.sub(r'^(?!##)([^*]+)\*$', r'- \1', cleaned, flags=re.MULTILINE)  # Convert "text*" to "- text" (but not if it starts with ##)

        # Fourth: Fix indented content with spaces (convert to proper markdown)
        # Handle various indentation levels
        for indent_level in range(1, 10):  # Handle up to 10 levels of indentation
            spaces = ' ' * (indent_level * 4)
            replacement = '    ' * indent_level + '- '
            # Match content that ends with * (since the AI uses * for formatting)
            cleaned = re.sub(r'^' + re.escape(spaces) + r'([^*:\n]+)\*$', replacement + r'\1', cleaned, flags=re.MULTILINE)

        # Fifth: Convert *text* to **text**
        cleaned = re.sub(r'^\*([^*]+)\*$', r'**\1**', cleaned, flags=re.MULTILINE)  # Convert *text* to **text**

        # Fix common markdown formatting issues
        cleaned = re.sub(r'^(#+)([^\s])', r'\1 \2', cleaned, flags=re.MULTILINE)  # Add spacing around headers
        cleaned = re.sub(r'^([*-+])([^\s])', r'\1 \2', cleaned, flags=re.MULTILINE)  # Add spacing around list items
        cleaned = re.sub(r'^(\d+\.)([^\s])', r'\1 \2', cleaned, flags=re.MULTILINE)  # Add spacing around numbered lists

        # Remove excessive newlines at start/end but preserve internal structure
        cleaned = cleaned.strip()
        # Fix multiple consecutive newlines (keep at most 2 for paragraph breaks)
        cleaned = re.sub(r'\n{3,}', '\n\n', cleaned)

        return cleaned

    def _generate_content_with_retry(self, prompt_part: str, api_key: str = None, use_streaming: bool = False) -> str:
        """Generate content with retry logic and optional streaming."""
        if api_key:
            genai.configure(api_key=api_key)
        
        self.model = genai.GenerativeModel(
            model_name=self.model_name,
            generation_config=self.generation_config,
            safety_settings=self.safety_settings,
        )
        
        try:
            if use_streaming:
                # Use streaming for better response handling
                response_stream = self.model.generate_content(prompt_part, stream=True)
                full_text = ""
                for chunk in response_stream:
                    if chunk.text:
                        full_text += chunk.text
                return self._clean_ai_response(full_text)
            else:
                # Use standard generation
                response = self.model.generate_content(prompt_part)
                text = self._extract_text(response)
                return text
        except Exception as e:
            raise e

    def generate_response(self, prompt_file_path: str, user_input_text: str, use_streaming: bool = False) -> str:
        """Generate a response based on a prompt file and user input."""
        prompt_part = self.read_prompt_part_from_file(prompt_file_path, user_input_text)
        last_error = None
        
        # If user has provided an API key, try it first
        if self.user_api_key:
            try:
                text = self._generate_content_with_retry(prompt_part, self.user_api_key, use_streaming)
                if text and text.strip():
                    return text
                else:
                    raise ValueError("Empty response content")
            except Exception as e:
                # If user key fails, fall back to system keys
                last_error = e
        
        # Try to get a system API key from the pool first
        system_api_key, key_owner = self.get_system_api_key()
        if system_api_key:
            try:
                text = self._generate_content_with_retry(prompt_part, system_api_key, use_streaming)
                if text and text.strip():
                    logging.info(f"Generated response using system API key from user {key_owner}")
                    return text
                else:
                    raise ValueError("Empty response content")
            except Exception as e:
                logging.warning(f"System API key from {key_owner} failed: {e}")
                last_error = e
        
        # Fall back to system API keys
        for _ in range(len(self.api_keys)):
            try:
                # Exponential backoff with key rotation
                backoff = 0.5
                for attempt in range(len(self.api_keys)):
                    api_key = self.get_current_api_key()
                    try:
                        text = self._generate_content_with_retry(prompt_part, api_key, use_streaming)
                        if text and text.strip():
                            self._record_success(api_key)
                            return text
                        else:
                            raise ValueError("Empty response content")
                    except Exception as inner:
                        self._record_failure(api_key, inner)
                        time.sleep(backoff)
                        backoff = min(backoff * 2, 4.0)
                        last_error = inner
                        continue
                continue
            except Exception as e:
                last_error = e
                continue
        # As a last resort, return a friendly message instead of raising
        return "No content generated. Please try again."

    def generate_random(self, prompt_file_path: str, use_streaming: bool = False) -> str:
        """Generate a random response based on a prompt file."""
        prompt_part = self.read_prompt_part_from_file(prompt_file_path)
        last_error = None
        
        # If user has provided an API key, try it first
        if self.user_api_key:
            try:
                text = self._generate_content_with_retry(prompt_part, self.user_api_key, use_streaming)
                if text and text.strip():
                    return text
                else:
                    raise ValueError("Empty response content")
            except Exception as e:
                # If user key fails, fall back to system keys
                last_error = e
        
        # Try to get a system API key from the pool first
        system_api_key, key_owner = self.get_system_api_key()
        if system_api_key:
            try:
                text = self._generate_content_with_retry(prompt_part, system_api_key, use_streaming)
                if text and text.strip():
                    logging.info(f"Generated random response using system API key from user {key_owner}")
                    return text
                else:
                    raise ValueError("Empty response content")
            except Exception as e:
                logging.warning(f"System API key from {key_owner} failed: {e}")
                last_error = e
        
        # Fall back to system API keys
        for _ in range(len(self.api_keys)):
            try:
                backoff = 0.5
                for attempt in range(len(self.api_keys)):
                    api_key = self.get_current_api_key()
                    try:
                        text = self._generate_content_with_retry(prompt_part, api_key, use_streaming)
                        if text and text.strip():
                            self._record_success(api_key)
                            return text
                        else:
                            raise ValueError("Empty response content")
                    except Exception as inner:
                        self._record_failure(api_key, inner)
                        time.sleep(backoff)
                        backoff = min(backoff * 2, 4.0)
                        last_error = inner
                        continue
                continue
            except Exception as e:
                last_error = e
                continue
        return "No content generated. Please try again."

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

    def _parse_examples_from_file(self, file_path: str) -> list:
        """Parse Q&A examples from a file with input/output pairs."""
        examples = []
        resolved_path = self._resolve_path(file_path)
        with open(resolved_path, "r") as f:
            content = f.read()
        # Split by double newlines between examples
        pairs = [p.strip() for p in content.split("\n\n") if p.strip()]
        for pair in pairs:
            input_part = ""
            output_part = ""
            for line in pair.split("\n"):
                if line.startswith("input:"):
                    input_part = line[len("input:"):].strip()
                elif line.startswith("output:"):
                    output_part = line[len("output:"):].strip()
            if input_part and output_part:
                examples.append((input_part, output_part))
        return examples

    def _build_imgdesc_prompt_with_examples(self, styles: list, user_input: str = None, examples_file: str = None, num_examples: int = 3) -> list:
        """Build a prompt for image description using styles, user input, and a few examples."""
        prompt = []
        if examples_file:
            examples = self._parse_examples_from_file(examples_file)
            # Randomly select a few examples
            chosen_examples = random.sample(examples, k=min(num_examples, len(examples)))
            for inp, out in chosen_examples:
                prompt.append(f"input: {inp}")
                prompt.append(f"output: {out}")
        # Now add the actual user request
        style_str = f"({', '.join(styles)})"
        if user_input:
            prompt.append(f"input: Start your description with the word 'imagine,' e.g., 'imagine a ...' now write me a detailed possible image description about {user_input}. Incorporate the following styles: {style_str}.")
        else:
            prompt.append(f"input: Start your description with the word 'imagine,' e.g., 'imagine a ...' now write me a detailed possible image description. Incorporate the following styles: {style_str}.")
        prompt.append("output:")
        return prompt

    def generate_imgdescription(
        self, image_styles_file_path: str, user_input_image: str, use_streaming: bool = False
    ) -> str:
        """Generate an image description based on styles, user input, and examples."""
        styles = self._read_styles_from_file(image_styles_file_path)
        chosen_styles = random.sample(styles, k=3)
        prompt_part = self._build_imgdesc_prompt_with_examples(
            chosen_styles, user_input_image, examples_file="./instruction/advance2.txt"
        )
        
        # Use user API key if available
        if self.user_api_key:
            text = self._generate_content_with_retry(prompt_part, self.user_api_key, use_streaming)
            return text
        
        # Try to get a system API key from the pool first
        system_api_key, key_owner = self.get_system_api_key()
        if system_api_key:
            try:
                text = self._generate_content_with_retry(prompt_part, system_api_key, use_streaming)
                logging.info(f"Generated image description using system API key from user {key_owner}")
                return text
            except Exception as e:
                logging.warning(f"System API key from {key_owner} failed: {e}")
        
        # Fall back to system API keys
        text = self._generate_content_with_retry(prompt_part, None, use_streaming)
        return text

    def generate_vrandom(self, image_styles_file_path: str, use_streaming: bool = False) -> str:
        """Generate a random image description based on styles and examples."""
        styles = self._read_styles_from_file(image_styles_file_path)
        chosen_styles = random.sample(styles, k=3)
        prompt_part = self._build_imgdesc_prompt_with_examples(
            chosen_styles, user_input=None, examples_file="./instruction/advance2.txt"
        )
        
        # Use user API key if available
        if self.user_api_key:
            text = self._generate_content_with_retry(prompt_part, self.user_api_key, use_streaming)
            return text
        
        # Try to get a system API key from the pool first
        system_api_key, key_owner = self.get_system_api_key()
        if system_api_key:
            try:
                text = self._generate_content_with_retry(prompt_part, system_api_key, use_streaming)
                logging.info(f"Generated random image description using system API key from user {key_owner}")
                return text
            except Exception as e:
                logging.warning(f"System API key from {key_owner} failed: {e}")
        
        # Fall back to system API keys
        text = self._generate_content_with_retry(prompt_part, None, use_streaming)
        return text

    def generate_response_stream(self, prompt_file_path: str, user_input_text: str):
        """Generate a streaming response based on a prompt file and user input."""
        prompt_part = self.read_prompt_part_from_file(prompt_file_path, user_input_text)
        
        def response_generator():
            try:
                # Use user API key if available
                if self.user_api_key:
                    yield from self._stream_content(prompt_part, self.user_api_key)
                    return
                
                # Try to get a system API key from the pool first
                system_api_key, key_owner = self.get_system_api_key()
                if system_api_key:
                    try:
                        logging.info(f"Streaming response using system API key from user {key_owner}")
                        yield from self._stream_content(prompt_part, system_api_key)
                        return
                    except Exception as e:
                        logging.warning(f"System API key from {key_owner} failed: {e}")
                
                # Fall back to system API keys
                for api_key in self.api_keys:
                    try:
                        yield from self._stream_content(prompt_part, api_key)
                        return
                    except Exception as e:
                        continue
                
                # If all keys fail, yield an error message
                yield "data: No content generated. Please try again.\n\n"
                
            except Exception as e:
                logging.exception("Error in response stream")
                yield f"data: Error: {str(e)}\n\n"
        
        return response_generator()
    
    def _stream_content(self, prompt_part, api_key: str):
        """Stream content using the specified API key."""
        genai.configure(api_key=api_key)
        
        model = genai.GenerativeModel(
            model_name=self.model_name,
            generation_config=self.generation_config,
            safety_settings=self.safety_settings,
        )
        
        try:
            response_stream = model.generate_content(prompt_part, stream=True)
            for chunk in response_stream:
                if chunk.text:
                    # Clean and yield the chunk
                    cleaned_chunk = self._clean_ai_response(chunk.text)
                    yield f"data: {cleaned_chunk}\n\n"
        except Exception as e:
            raise e

    def _read_styles_from_file(self, file_path: str) -> List[str]:
        """Read styles from a file and return them as a list."""
        resolved_path = self._resolve_path(file_path)
        with open(resolved_path, "r") as file:
            return [line.strip() for line in file.readlines()]

    def generate_visual(self, image_styles_file_path: str, image_data: bytes, use_streaming: bool = False) -> str:
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
        
        # Use user API key if available
        if self.user_api_key:
            text = self._generate_content_with_retry(prompt_part, self.user_api_key, use_streaming)
            return text
        
        # Try to get a system API key from the pool first
        system_api_key, key_owner = self.get_system_api_key()
        if system_api_key:
            try:
                text = self._generate_content_with_retry(prompt_part, system_api_key, use_streaming)
                logging.info(f"Generated visual description using system API key from user {key_owner}")
                return text
            except Exception as e:
                logging.warning(f"System API key from {key_owner} failed: {e}")
        
        # Fall back to system API keys
        text = self._generate_content_with_retry(prompt_part, None, use_streaming)
        return text

    def generate_visual2(
        self, image_data: bytes, parameter1: str, parameter2: str, parameter3: str, use_streaming: bool = False
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
        
        # Use user API key if available
        if self.user_api_key:
            text = self._generate_content_with_retry(prompt_part, self.user_api_key, use_streaming)
            return text
        
        # Try to get a system API key from the pool first
        system_api_key, key_owner = self.get_system_api_key()
        if system_api_key:
            try:
                text = self._generate_content_with_retry(prompt_part, system_api_key, use_streaming)
                logging.info(f"Generated visual2 description using system API key from user {key_owner}")
                return text
            except Exception as e:
                logging.warning(f"System API key from {key_owner} failed: {e}")
        
        # Fall back to system API keys
        text = self._generate_content_with_retry(prompt_part, None, use_streaming)
        return text
