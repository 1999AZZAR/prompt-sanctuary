# app.py
from flask import Flask, render_template, request
from generative_model import generate_response, generate_random, generate_vrandom, generate_imgdescription

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
