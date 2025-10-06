from flask import Blueprint, request, jsonify, session, url_for
from functools import wraps
import random # Importa a biblioteca random
from .models import Subject, User
from .extensions import db

api_bp = Blueprint('api', __name__)

# Lista de Dicas para o ENEM e SSA
DICAS = [
    "Revise as funções logarítmicas — elas caem muito no ENEM!",
    "Leia uma redação nota 1000 e anote as estruturas usadas.",
    "Treine sua interpretação de texto em inglês.",
    "Reveja os ciclos biogeoquímicos (SSA 2 adora cobrar isso!).",
    "Não se esqueça de estudar a história de Pernambuco para o SSA.",
    "Pratique a resolução da prova do ENEM por área de conhecimento, cronometrando o tempo.",
    "Crie flashcards para memorizar fórmulas de Física e Química."
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


@api_bp.route('/add_subject', methods=['POST'])
@login_required
def add_subject_api():
    data = request.get_json()
    subject_name = data.get('subject_name')

    if not subject_name:
        return jsonify({"error": "O nome da matéria não pode estar vazio."}), 400

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
@login_required
def chat_api():
    user_message = request.json.get('message')
    if not user_message:
        return jsonify({"error": "Mensagem ausente"}), 400
    try:
        # (código Gemini aqui)
        # Por enquanto, devolvemos uma resposta de exemplo
        resposta_simulada = f"Recebi a sua mensagem: '{user_message}'. A minha integração final ainda está em progresso."
        return jsonify(response=resposta_simulada)
    except Exception as e:
        print("Erro Gemini:", e)
        return jsonify({"error": str(e)}), 500