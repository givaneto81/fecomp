from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from .models import User
from .extensions import db

# Blueprint renomeado para 'autenticacao'
auth_bp = Blueprint('autenticacao', __name__)

@auth_bp.route('/')
def pagina_login():
    return render_template('index.html')

@auth_bp.route('/registo', methods=['GET', 'POST'])
def pagina_registo():
    if request.method == 'POST':
        nome = request.form.get('name')
        email = request.form.get('email')
        senha = request.form.get('senha')
        utilizador_existe = User.query.filter_by(email=email).first()

        if utilizador_existe:
            flash('Este email já está registado. Tente fazer login.', 'error')
            return redirect(url_for('autenticacao.pagina_login'))

        senha_hash = generate_password_hash(senha)
        novo_utilizador = User(name=nome, email=email, password_hash=senha_hash)
        
        db.session.add(novo_utilizador)
        db.session.commit()
        
        flash('Registo realizado com sucesso! Faça o login.', 'success')
        return redirect(url_for('autenticacao.pagina_login'))
    return render_template('register.html')

@auth_bp.route('/login', methods=['POST'])
def login():
    email = request.form.get('email')
    senha = request.form.get('senha')
    utilizador = User.query.filter_by(email=email).first()

    if utilizador and check_password_hash(utilizador.password_hash, senha):
        session.clear()
        session['user_id'] = utilizador.id
        session['user_name'] = utilizador.name
        
        # TAREFA 4: REDIRECIONAMENTO APÓS LOGIN
        # Se o utilizador ainda não concluiu o tutorial, é redirecionado para lá.
        if not utilizador.tutorial_concluido:
            return redirect(url_for('tutorial.pagina_tutorial'))
        
        # Caso contrário, vai para a página inicial.
        return redirect(url_for('visoes.pagina_inicio'))
    else:
        flash('Email ou senha incorretos.', 'error')
        return redirect(url_for('autenticacao.pagina_login'))

@auth_bp.route('/logout')
def logout():
    session.clear()
    flash('Você saiu da sua conta.', 'success')
    return redirect(url_for('autenticacao.pagina_login'))