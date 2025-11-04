from flask import Blueprint, request, jsonify, session, url_for
from functools import wraps
import random
# IMPLEMENTAÇÃO 3: Importar o genai
import google.generativeai as genai
from .models import Subject, User
from .extensions import db, csrf 

api_bp = Blueprint('api', __name__)

# Lista de Dicas para o ENEM e SSA
DICAS = [
    "Revise as funções logarítmicas — elas caem muito no ENEM!",
    "Leia uma redação nota 1000 e anote as estruturas usadas.",
    "Treine sua interpretação de texto em inglês.",
    "Reveja os ciclos biogeoquímicos (SSA 2 adora cobrar isso!).",
    "Não se esqueça de estudar a história de Pernambuco para o SSA.",
    "Pratique a resolução da prova do ENEM por área de conhecimento, cronometrando o tempo.",
    "Crie flashcards para memorizar fórmulas de Física e QuíMica."
]

# Decorator para exigir login nas rotas da API
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({"error": "Autenticação necessária"}), 401
        return f(*args, **kwargs)
    return decorated_function

@api_bp.route('/dica_do_dia')
@login_required
def dica_do_dia():
    """
    Retorna uma dica de estudo aleatória da lista de DICAS.
    """
    return jsonify(dica=random.choice(DICAS))


# NÍVEL 2.2: ESTA ROTA AGORA CRIA APENAS MATÉRIAS PESSOAIS
@api_bp.route('/add_subject', methods=['POST'])
@csrf.exempt
@login_required
def add_subject_api():
    """
    Cria uma nova matéria PESSOAL para o utilizador logado.
    """
    data = request.get_json()
    subject_name = data.get('subject_name')

    if not subject_name:
        return jsonify({"error": "O nome da matéria não pode estar vazio."}), 400

    # NÍVEL 2.1: Define explicitamente o user_id (matéria pessoal)
    new_subject = Subject(name=subject_name, user_id=session['user_id'])
    db.session.add(new_subject)
    db.session.commit()

    subject_data = {
        "id": new_subject.id,
        "name": new_subject.name,
        "color": new_subject.color,
        "urls": {
            "pastas": url_for('visoes.pastas_page', subject_id=new_subject.id),
            "delete": url_for('visoes.delete_subject', subject_id=new_subject.id),
            "update_color": url_for('visoes.update_subject_color', subject_id=new_subject.id)
        }
    }
    return jsonify({"subject": subject_data}), 201


@api_bp.route('/chat', methods=['POST'])
@csrf.exempt
@login_required
def chat_api():
    user_message = request.json.get('message')
    if not user_message:
        return jsonify({"error": "Mensagem ausente"}), 400
    
    try:
        # --- IMPLEMENTAÇÃO 3: Lógica real da API Gemini ---
        
        # 1. Define o modelo (já configurado no __init__.py)
        # Recomendo usar um modelo mais recente se disponível, ex: 'gemini-1.5-flash'
        model = genai.GenerativeModel('gemini-1.0-pro') 
        
        # 2. (Opcional) Define um contexto/prompt de sistema
        #    Isto é MUITO importante para fazer a IA se comportar como um tutor.
        system_prompt = (
            "Você é o 'Educa AI', um assistente de estudos inteligente e amigável. "
            "Seu público são estudantes de pré-vestibular (ENEM e SSA). "
            "Responda às suas dúvidas de forma didática, clara e encorajadora. "
            "Use formatação markdown (como **negrito** e *itálico*) para organizar a resposta. "
            "Seja direto e foque no conteúdo acadêmico."
        )

        # 3. Gera a resposta
        # Para um chat simples, podemos usar generate_content
        full_prompt = f"{system_prompt}\n\nDúvida do Aluno: {user_message}"
        response = model.generate_content(full_prompt)
        
        # 4. Retorna a resposta
        return jsonify(response=response.text)
        # --- FIM DA IMPLEMENTAÇÃO 3 ---

    except Exception as e:
        print(f"Erro na API Gemini: {e}")
        return jsonify({"error": "Ocorreu um erro ao processar sua solicitação com a IA.", "details": str(e)}), 500