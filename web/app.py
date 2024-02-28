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
            "\nuse only English and write me the possible prompt to regenerate this image including the style and feels:\n",
            {"mime_type": "image/jpeg", "data": image_data},
            "\nremember to make it as detailed as possible using from 300 up to 500 character long description.",
            "\nalso give me the main style for that image based on this list (you can choose more than one):\n",
            "1. photographic\n 2. enhance\n 3. anime\n 4. digital-art\n 5. comic-book\n 6. fantasy-art\n",
            "7. line-art\n 8. analog-film\n 9. neon-punk\n 10. isometric\n 11. low-poly\n 12. origami\n",
            "13. modeling-compound\n 14. cinematic\n 15. 3d-model\n 16. pixel-art\n 17. tile-texture\n"
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
