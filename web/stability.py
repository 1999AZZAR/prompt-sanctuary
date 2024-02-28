import os
import base64
import requests
from PIL import Image, ImageEnhance
from dotenv import load_dotenv
import logging
from typing import Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
WATERMARK_IMAGE_PATH = './static/icon/sanctuary.png'
OUTPUT_IMAGE_DIR = "./static/image"
STABILITY_API_URL = "https://api.stability.ai/v1/generation/stable-diffusion-xl-1024-v1-0/text-to-image"

# Load environment variables
load_dotenv()

class ImageGen:
    def __init__(self):
        self.api_key = os.getenv('STABILITY_API_KEY')
        if not self.api_key:
            raise ValueError("STABILITY_API_KEY environment variable not set.")

    def add_watermark(self, input_image_path: str, output_image_path: str, watermark_image_path: str, transparency: int = 25) -> None:
        """Add a watermark to the generated image."""
        if not os.path.exists(watermark_image_path):
            logger.warning("Watermark image not found. Saving original image without watermark.")
            Image.open(input_image_path).save(output_image_path)
            return

        try:
            original_image = Image.open(input_image_path)
            watermark = Image.open(watermark_image_path)
            min_dimension = min(original_image.width, original_image.height)
            watermark_size = (int(min_dimension * 0.14), int(min_dimension * 0.14))
            watermark = watermark.resize(watermark_size).convert('RGBA')

            image_with_watermark = original_image.copy()
            position = (0, original_image.size[1] - watermark.size[1])
            image_with_watermark.paste(watermark, position, watermark)

            alpha = watermark.split()[3]
            alpha = ImageEnhance.Brightness(alpha).enhance(transparency / 100.0)
            watermark.putalpha(alpha)
            image_with_watermark.save(output_image_path)

        except Exception as e:
            logger.error(f"Error adding watermark: {e}")
            Image.open(input_image_path).save(output_image_path)

    def generate_image(self, prompt: str) -> Optional[str]:
        """Generate an image based on the user's prompt."""
        common_params = {
            "samples": 1,
            "steps": 50,
            "cfg_scale": 5.5,
            "clip_guidance_preset": "FAST_BLUE",
            "height": 1024,
            "width": 1024,
            "text_prompts": [
                {"text": prompt, "weight": 1},
                {
                    "text": "The artwork showcases excellent anatomy with a clear, complete, and appealing "
                            "depiction. It has well-proportioned and polished details, presenting a unique "
                            "and balanced composition. The high-resolution image is undamaged and well-formed, "
                            "conveying a healthy and natural appearance without mutations or blemishes. The "
                            "positive aspect of the artwork is highlighted by its skillful framing and realistic "
                            "features, including a well-drawn face and hands. The absence of signatures contributes "
                            "to its seamless and authentic quality, and the depiction of straight fingers adds to "
                            "its overall attractiveness.",
                    "weight": 0.3
                },
                {
                    "text": "2 faces, 2 heads, bad anatomy, blurry, cloned face, cropped image, cut-off, deformed hands, "
                            "disconnected limbs, disgusting, disfigured, draft, duplicate artifact, extra fingers, extra limb, "
                            "floating limbs, gloss proportions, grain, gross proportions, long body, long neck, low-res, mangled, "
                            "malformed, malformed hands, missing arms, missing limb, morbid, mutation, mutated, mutated hands, "
                            "mutilated, mutilated hands, multiple heads, negative aspect, out of frame, poorly drawn, poorly drawn "
                            "face, poorly drawn hands, signatures, surreal, tiling, twisted fingers, ugly",
                    "weight": -1
                },
            ],
        }

        try:
            response = requests.post(
                STABILITY_API_URL,
                headers={
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                    "Authorization": f"Bearer {self.api_key}",
                },
                json=common_params,
            )

            if response.status_code != 200:
                raise Exception(f"Non-200 response: {response.text}")

            data = response.json()
            artifacts = data.get("artifacts", [])
            if not artifacts:
                raise Exception("No artifacts returned by the API")

            if not os.path.exists(OUTPUT_IMAGE_DIR):
                os.makedirs(OUTPUT_IMAGE_DIR)

            file_name = f'{data["artifacts"][0]["seed"]}.png'
            generated_image_path = f'{OUTPUT_IMAGE_DIR}/{file_name}'
            with open(generated_image_path, "wb") as f:
                f.write(base64.b64decode(data["artifacts"][0]["base64"]))

            self.add_watermark(generated_image_path, generated_image_path, WATERMARK_IMAGE_PATH, transparency=25)
            self.downsize_image(generated_image_path)

            return file_name

        except Exception as e:
            logger.error(f"Error generating image: {e}")
            return None

    def downsize_image(self, image_path: str) -> None:
        """Downsize the image to improve performance."""
        try:
            img = Image.open(image_path)
            img.thumbnail((img.size[0] // 3, img.size[1] // 3))
            img.save(image_path, quality=100)
        except Exception as e:
            logger.error(f"Error downsizing image: {e}")

# Initialize the ImageGen instance
image_gen = ImageGen()