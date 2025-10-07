from flask import Blueprint, render_template, redirect, url_for, session, flash, jsonify
from .models import User
from .extensions import db, csrf
from .visoes import login_required 

# Cria o Blueprint do tutorial
tutorial_bp = Blueprint('tutorial', __name__)

@tutorial_bp.route('/tutorial')
@login_required
def pagina_tutorial():
    """
    Renderiza a página do tutorial.
    Se o utilizador já o concluiu, redireciona para a página inicial.
    """
    utilizador = User.query.get(session['user_id'])
    if utilizador.tutorial_concluido:
        return redirect(url_for('visoes.pagina_inicio'))
    
    return render_template('tutorial.html')

@tutorial_bp.route('/api/utilizador/concluir_tutorial', methods=['POST'])
@csrf.exempt
@login_required
def concluir_tutorial():
    """
    Endpoint da API para marcar o tutorial como concluído no banco de dados.
    """
    try:
        utilizador = User.query.get(session['user_id'])
        if utilizador:
            utilizador.tutorial_concluido = True
            db.session.commit()
            return jsonify(sucesso=True, mensagem="Tutorial concluído com sucesso!"), 200
        return jsonify(sucesso=False, erro="Utilizador não encontrado."), 404
    except Exception as e:
        db.session.rollback()
        return jsonify(sucesso=False, erro=str(e)), 500