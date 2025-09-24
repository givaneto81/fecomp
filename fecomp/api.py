from flask import Blueprint, request, jsonify
import google.generativeai as genai
from google.api_core import exceptions as google_exceptions
from . import login_required

api_bp = Blueprint('api', __name__)

@api_bp.route('/chat', methods=['POST'])
@login_required
def chat_api():
    user_message = request.json.get('message')
    if not user_message:
        return jsonify({"error": "A mensagem não pode estar vazia."}), 400

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

        # Acessa o texto da resposta de forma segura
        bot_response = ""
        if response.parts:
            bot_response = response.parts[0].text
        else:
            # Caso a resposta não tenha conteúdo (ex: filtro de segurança)
            bot_response = "Não consegui gerar uma resposta para isso. Tente outra pergunta."

        return jsonify({"response": bot_response})

    except google_exceptions.GoogleAPICallError as e:
        # Erro na chamada da API (ex: problema de conexão)
        print(f"Erro na API do Gemini (Chamada): {e}")
        return jsonify({"error": "Houve um problema ao se comunicar com o serviço de IA. Tente novamente mais tarde."}), 503
    except google_exceptions.InvalidArgument as e:
        # Erro com os argumentos da requisição (ex: prompt bloqueado)
        print(f"Erro na API do Gemini (Argumento Inválido): {e}")
        return jsonify({"error": "Sua solicitação foi bloqueada por questões de segurança. Por favor, reformule sua pergunta."}), 400
    except Exception as e:
        # Outros erros inesperados
        print(f"Erro inesperado na API do Gemini: {e}")
        return jsonify({"error": "Ocorreu um erro inesperado no servidor de IA. Por favor, tente novamente."}), 500