# import the necessary libraries
import os
import base64
import requests
from PIL import Image, ImageEnhance
from dotenv import load_dotenv

# load the .env file
load_dotenv()

# class for the image generation
class Image_gen:

    # add watermark to the generated image.
    def add_watermark(self, input_image_path, output_image_path, watermark_image_path, transparency=25):
        if watermark_image_path is None or not os.path.exists(watermark_image_path):
            original_image = Image.open(input_image_path)
            original_image.save(output_image_path)
            return

        #
        try:
            original_image = Image.open(input_image_path)
            watermark = Image.open(watermark_image_path)
            min_dimension = min(original_image.width, original_image.height)
            watermark_size = (int(min_dimension * 0.14), int(min_dimension * 0.14))
            watermark = watermark.resize(watermark_size)
            if watermark.mode != 'RGBA':
                watermark = watermark.convert('RGBA')

            #
            image_with_watermark = original_image.copy()
            position = (0, original_image.size[1] - watermark.size[1])
            image_with_watermark.paste(watermark, position, watermark)
            alpha = watermark.split()[3]
            alpha = ImageEnhance.Brightness(alpha).enhance(transparency / 100.0)
            watermark.putalpha(alpha)
            image_with_watermark.save(output_image_path)

        # 
        except Exception as e:
            print(f"Error adding watermark: {e}")
            original_image.save(output_image_path)

    # generate the image using user input.
    def generate_image(self, prompt):
        api_key = os.getenv('STABILITY_API_KEY')
        common_params = {
            "samples": 1,
            "steps": 50,
            "cfg_scale": 5.5,
            "clip_guidance_preset": "FAST_BLUE",
            "height": 1024,
            "width": 1024,
            # user input prompt and additional prompt
            "text_prompts": [
                # user input prompt
                {
                    "text"  : prompt, 
                    "weight": 1
                },
                # neutral additional prompt
                {
                    "text"  :   "The artwork showcases excellent anatomy with a clear, complete, and appealing "
                                "depiction. It has well-proportioned and polished details, presenting a unique "
                                "and balanced composition. The high-resolution image is undamaged and well-formed, "
                                "conveying a healthy and natural appearance without mutations or blemishes. The "
                                "positive aspect of the artwork is highlighted by its skillful framing and realistic "
                                "features, including a well-drawn face and hands. The absence of signatures contributes "
                                "to its seamless and authentic quality, and the depiction of straight fingers adds to "
                                "its overall attractiveness.",
                    "weight": 0.3
                },
                # negative additional prompt
                {
                    "text"  :   "2 faces, 2 heads, bad anatomy, blurry, cloned face, cropped image, cut-off, deformed hands, "
                                "disconnected limbs, disgusting, disfigured, draft, duplicate artifact, extra fingers, extra limb, "
                                "floating limbs, gloss proportions, grain, gross proportions, long body, long neck, low-res, mangled, "
                                "malformed, malformed hands, missing arms, missing limb, morbid, mutation, mutated, mutated hands, "
                                "mutilated, mutilated hands, multiple heads, negative aspect, out of frame, poorly drawn, poorly drawn "
                                "face, poorly drawn hands, signatures, surreal, tiling, twisted fingers, ugly",
                    "weight": -1
                },
            ],
        }

        # 
        try:
            response = requests.post(
                "https://api.stability.ai/v1/generation/stable-diffusion-xl-1024-v1-0/text-to-image",
                headers={
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                    "Authorization": f"Bearer {api_key}",
                },
                json=common_params,
            )

            if response.status_code != 200:
                raise Exception("Non-200 response: " + str(response.text))

            # get the log
            data = response.json()            
            artifacts = data.get("artifacts", [])
            if not artifacts:
                raise Exception("No artifacts returned by the API")   

            # set the output dir
            output_directory = "web/static/image"
            if not os.path.exists(output_directory):
                os.makedirs(output_directory)

            # save the image
            file_name = f'{data["artifacts"][0]["seed"]}.png'
            generated_image_path = f'{output_directory}/{file_name}'
            with open(generated_image_path, "wb") as f:
                f.write(base64.b64decode(data["artifacts"][0]["base64"]))

            # add watermark
            watermark_image_path = 'web/static/icon/sanctuary.png' 
            output_with_watermark_path = generated_image_path
            self.add_watermark(generated_image_path, output_with_watermark_path, watermark_image_path, transparency=25)
            # Downsize/scale the image
            self.downsize_image(output_with_watermark_path)

            # return the response
            return file_name
        except Exception as e:
            print(f"Error in generate_image: {e}")
            return None

    # resize the image to make it faster when send back to the user.
    def downsize_image(self, image_path):
        try:
            img = Image.open(image_path)
            # Resize the image to be 3 times smaller or to a maximum size of 200KB
            img.thumbnail((img.size[0] // 3, img.size[1] // 3))
            img.save(image_path, quality=100)
        except Exception as e:
            print(f"Error downsizing image: {e}")

image_gen = Image_gen()
