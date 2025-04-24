import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from openai import OpenAI
from pydub import AudioSegment
import io

app = Flask(__name__)
CORS(app)

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

SYSTEM_PROMPT = """
Meu prompt é esse...
"""

@app.route('/upload', methods=['POST'])
def upload_knowledge():
    upload_dir = os.path.join(os.getcwd(), 'uploads')
    os.makedirs(upload_dir, exist_ok=True)

    if 'knowledge' not in request.files:
        return jsonify({"error": "Nenhum arquivo enviado"}), 400

    file = request.files['knowledge']
    save_path = os.path.join(upload_dir, file.filename)
    file.save(save_path)
    return jsonify({"status": "ok", "filename": file.filename}), 200

@app.route('/pause', methods=['POST'])
def pause_bot():
    return jsonify({"status": "paused"}), 200

@app.route('/resume', methods=['POST'])
def resume_bot():
    return jsonify({"status": "resumed"}), 200

@app.route('/transcribe', methods=['POST'])
def transcribe_audio():
    print("🍪 request.files keys:", request.files.keys())
    if 'audio' not in request.files:
        return jsonify({"error": "Nenhum arquivo de áudio enviado"}), 400

    audio_file = request.files['audio']
    ogg_data = io.BytesIO(audio_file.read())
    audio = AudioSegment.from_file(ogg_data, format="ogg")
    # 2) Exporta para WAV em buffer
    wav_buffer = io.BytesIO()
    audio.export(wav_buffer, format="wav")
    wav_buffer.seek(0)

    try:
        # ── AQUI: usar openai.Audio.transcribe em vez de transcriptions.create
        result = client.audio.transcriptions.create(
            model="whisper-1",
            file=wav_buffer,
            response_format="json"
        )
        print("🔍 Whisper retornou:", result)
        return jsonify({
            "language": result.get("language"),
            "text":     result.get("text")
        }), 200

    except Exception as e:
        print("❌ Erro em /transcribe:", e)
        return jsonify({"error": str(e)}), 500

@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    system_text  = data.get('prompt', SYSTEM_PROMPT)
    user_message = data.get('message', '')
    conversation = data.get('conversation', [])

    messages = [{"role": "system", "content": system_text}]
    messages += conversation
    messages.append({"role": "user", "content": user_message})

    try:
        resp = client.chat.completions.create(
            model="gpt-4.1-nano",
            messages=messages,
            temperature=0.7
        )
        answer = resp.choices[0].message.content
        return jsonify({"response": answer}), 200

    except Exception as e:
        print("❌ Erro em /chat:", e)
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
