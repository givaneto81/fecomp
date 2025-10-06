from flask import Blueprint, request, jsonify, session, url_for
from functools import wraps
from .models import Subject, User
from .extensions import db 

api_bp = Blueprint('api', __name__)

# Decorator para exigir login nas rotas da API
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({"error": "Autenticação necessária"}), 401
        return f(*args, **kwargs)
    return decorated_function

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

    # Prepara a resposta JSON que o home.js espera
    subject_data = {
        "id": new_subject.id,
        "name": new_subject.name,
        "color": new_subject.color,
        "urls": {
            "pastas": url_for('views.pastas_page', subject_id=new_subject.id),
            "delete": url_for('views.delete_subject', subject_id=new_subject.id),
            "update_color": url_for('views.update_subject_color', subject_id=new_subject.id)
        }
    }
    return jsonify({"subject": subject_data}), 201


@api_bp.route('/chat', methods=['POST'])
@login_required
def chat_api():
    # ... (seu código de chat existente) ...
    # Nenhuma alteração necessária aqui
    user_message = request.json.get('message')
    if not user_message:
        return jsonify({"error": "Mensagem ausente"}), 400
    try:
        # (seu código Gemini aqui)
        pass 
    except Exception as e:
        print("Erro Gemini:", e)
        return jsonify({"error": str(e)}), 500