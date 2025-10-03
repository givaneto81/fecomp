from flask import Blueprint, request, jsonify, session
import google.generativeai as genai
from functools import wraps

api_bp = Blueprint('api', __name__)

# Re-defina o decorator aqui ou importe-o de um arquivo comum
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({"error": "Autenticação necessária"}), 401
        return f(*args, **kwargs)
    return decorated_function

@api_bp.route('/chat', methods=['POST'])
@login_required
def chat_api():
    user_message = request.json.get('message')
    if not user_message:
        return jsonify({"error": "Mensagem ausente"}), 400
    try:
        instrucao_sistema = (
            "Você é um assistente de estudos para pré-vestibular. Responda sempre em português do Brasil, "
            "Seja animado, mas mantenha a seriedade ao explicar conteúdos importantes. "
            "Seja breve em perguntas que não sejam sobre conteúdo de estudo."
        )
        model = genai.GenerativeModel(
            'models/gemini-1.5-flash-latest',
            system_instruction=instrucao_sistema
        )
        response = model.generate_content(user_message)
        bot_response = getattr(response, "text", None) or ""
        return jsonify({"response": bot_response})
    except Exception as e:
        print("Erro Gemini:", e)
        return jsonify({"error": str(e)}), 500