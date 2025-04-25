import os, logging
from flask import Flask, request, jsonify
from flask_cors import CORS
import openai
from dotenv import load_dotenv

# Carrega variáveis de ambiente do .env
auth_load = load_dotenv()
openai.api_key = os.getenv('OPENAI_API_KEY')
SYSTEM_PROMPT = os.getenv('SYSTEM_PROMPT', "Meu prompt é esse...")

app = Flask(__name__)
CORS(app)
logging.basicConfig(level=logging.INFO)

@app.route('/upload', methods=['POST'])
def upload_knowledge():
    upload_dir = os.path.join(app.root_path, 'uploads')
    os.makedirs(upload_dir, exist_ok=True)
    file = request.files.get('knowledge')
    if not file:
        return jsonify(error="Nenhum arquivo enviado"), 400
    path = os.path.join(upload_dir, file.filename)
    file.save(path)
    logging.info(f'Arquivo salvo em {path}')
    return jsonify(status="ok", filename=file.filename)

@app.route('/pause', methods=['POST'])
def pause_bot():
    return jsonify(status="paused")

@app.route('/resume', methods=['POST'])
def resume_bot():
    return jsonify(status="resumed")

@app.route('/chat', methods=['POST'])
def chat():
    data = request.get_json(force=True)
    # Se prompt vier como null ou vazio, usa o prompt do sistema
    system_text = data.get('prompt') or SYSTEM_PROMPT
    user_message = data.get('message', '')
    conversation = data.get('conversation', [])

    messages = (
        [{"role": "system", "content": system_text}] +
        conversation +
        [{"role": "user", "content": user_message}]
    )

    try:
        resp = openai.ChatCompletion.create(
            model="gpt-4.1-nano",
            messages=messages,
            temperature=0.7
        )
        answer = resp.choices[0].message.content
        return jsonify(response=answer)

    except Exception as e:
        logging.error("OpenAI error", exc_info=e)
        return jsonify(error=str(e)), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
