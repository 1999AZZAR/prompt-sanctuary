# app.py
from flask import Flask, render_template, request
from gemini_text import generate_response, generate_random, generate_vrandom, generate_imgdescription
from gemini_vis import generate_content


app = Flask(__name__)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/generate')
def generate():
    return render_template('prompts/generator/generator.html', result=None)

@app.route('/generate/tprompt', methods=['POST'])
def process():
    user_input = request.form['user_input']
    response_text = generate_response(user_input)
    return render_template('prompts/generator/generator.html', result=response_text)

@app.route('/generate/trandom', methods=['POST'])
def random_prompt():
    response_text = generate_random()
    return render_template('prompts/generator/generator.html', result=response_text)

@app.route('/generate/iprompt', methods=['POST'])
def vprocess():
    user_input = request.form['user_input']
    response_text = generate_imgdescription(user_input)
    return render_template('prompts/generator/generator.html', result=response_text)

@app.route('/generate/irandom', methods=['POST'])
def vrandom_prompt():
    response_text = generate_vrandom()
    return render_template('prompts/generator/generator.html', result=response_text)

@app.route('/reverse')
def reverse():
    return render_template('prompts/generator/reverse.html', result=None)

@app.route('/reverse/image', methods=['POST'])
def reverse_image():
    try:
        image_file = request.files['image']
        image_data = image_file.read()

        prompt_parts = [
            "\nPlease write a detailed description in proper English to recreate this image in 120 to 340 word. Include the style, mood, lighting, and other key details. Use complete sentences and proofread for spelling and grammar mistakes:",
            {"mime_type": "image/jpeg", "data": image_data},
            "\nAlso select the main artistic style from this list (you can choose more than one): \n",
            "1. Photographic\n2. Enhanced\n3. Anime\n4. Digital art\n5. Comic book\n6. Fantasy art\n",  
            "7. Line art\n8. Analog film\n9. Neon punk\n10. Isometric\n11. Low poly\n12. Origami\n",
            "13. Modeling compound\n14. Cinematic\n15. 3D model\n16. Pixel art\n17. Tile texture\n"
        ]

        generated_text = generate_content(prompt_parts)
        return render_template('prompts/generator/reverse.html', response=generated_text)

    except Exception as e:
        return f"Error: {str(e)}"

@app.route('/library')
def index():
    return render_template('prompts/library.html')

@app.route('/library/promptimpro')
def promptinmpro():
    return render_template('prompts/global/prompt_improve.html')

@app.route('/library/adjust')
def adjust():
    return render_template('prompts/global/adjustable_iq.html')

@app.route('/library/aerea')
def aerea():
    return render_template('prompts/global/aerea.html')

@app.route('/library/ultimate')
def ultimate():
    return render_template('prompts/global/ultimate_knowladge.html')

@app.route('/library/webdev')
def webdev():
    return render_template('prompts/global/web_des.html')

@app.route('/library/mutation')
def mutation():
    return render_template('prompts/global/mutation.html')

@app.route('/library/createch')
def createch():
    return render_template('prompts/Writers_and_editors/CreaTech.html')

@app.route('/library/enhancement')
def enhancement():
    return render_template('prompts/Writers_and_editors/enhancement.html')

@app.route('/library/journalist')
def journalist():
    return render_template('prompts/Writers_and_editors/journalist.html')

@app.route('/library/paraphrase')
def paraphrase():
    return render_template('prompts/Writers_and_editors/paraphrase.html')

@app.route('/library/emdev')
def emdev():
    return render_template('prompts/coding_companion/emdev.html')

@app.route('/library/queria')
def queria():
    return render_template('prompts/coding_companion/queria.html')

@app.route('/library/standard')
def standard():
    return render_template('prompts/coding_companion/standard.html')

if __name__ == '__main__':
    app.run(host="0.0.0.0",port=5000, debug=True)
