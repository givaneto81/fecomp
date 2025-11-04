from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from .models import User
from .extensions import db
from .forms import EmptyForm 
auth_bp = Blueprint('autenticacao', __name__)

@auth_bp.route('/')
def pagina_login():
    form = EmptyForm()
    return render_template('index.html', form=form)

@auth_bp.route('/registo', methods=['GET', 'POST'])
def pagina_registo():
    form = EmptyForm()
    if form.validate_on_submit():
        nome = request.form.get('name')
        email = request.form.get('email')
        senha = request.form.get('senha')
        
        role = request.form.get('role', 'aluno')

        utilizador_existe = User.query.filter_by(email=email).first()

        if utilizador_existe:
            flash('Este email já está registado. Tente fazer login.', 'error')
            return redirect(url_for('autenticacao.pagina_login'))
        
        if role not in ['aluno', 'professor']:
            flash('Função inválida selecionada.', 'error')
            return redirect(url_for('autenticacao.pagina_registo'))

        senha_hash = generate_password_hash(senha)
        
        novo_utilizador = User(name=nome, 
                             email=email, 
                             password_hash=senha_hash, 
                             role=role)
        
        db.session.add(novo_utilizador)
        db.session.commit()
        
        flash('Cadastro realizado com sucesso! Faça o login.', 'success')
        return redirect(url_for('autenticacao.pagina_login'))
    return render_template('register.html', form=form)

@auth_bp.route('/login', methods=['POST'])
def login():
    form = EmptyForm()
    if form.validate_on_submit():
        email = request.form.get('email')
        senha = request.form.get('senha')
        utilizador = User.query.filter_by(email=email).first()

        if utilizador and check_password_hash(utilizador.password_hash, senha):
            
            """if utilizador.email == 'admin@admin' and utilizador.role != 'admin':
                utilizador.role = 'admin'
                db.session.commit()
                flash('Privilégios de Administrador concedidos!', 'success')""" 

            session.clear()
            session['user_id'] = utilizador.id
            session['user_name'] = utilizador.name
            session['user_role'] = utilizador.role
            
            if not utilizador.tutorial_concluido:
                return redirect(url_for('tutorial.pagina_tutorial'))
            
            return redirect(url_for('visoes.pagina_inicio'))
        else:
            flash('Email ou senha incorretos.', 'error')
            return redirect(url_for('autenticacao.pagina_login'))
    else:
        flash('Sessão inválida ou expirada. Por favor, tente novamente.', 'error')
        return redirect(url_for('autenticacao.pagina_login'))

@auth_bp.route('/logout')
def logout():
    session.clear()
    flash('Você saiu da sua conta.', 'success')
    return redirect(url_for('autenticacao.pagina_login'))