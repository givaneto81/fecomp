from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from .models import User
from .extensions import db

# Cria o Blueprint de autenticação
auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/')
def login_page():
    return render_template('index.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register_page():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        senha = request.form.get('senha')
        user_exists = User.query.filter_by(email=email).first()
        if user_exists:
            flash('Este email já está cadastrado. Tente fazer login.', 'error')
            return redirect(url_for('auth.login_page'))
        hashed_password = generate_password_hash(senha)
        new_user = User(name=name, email=email, password_hash=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        flash('Cadastro realizado com sucesso! Faça o login.', 'success')
        return redirect(url_for('auth.login_page'))
    return render_template('register.html')

@auth_bp.route('/login', methods=['POST'])
def login():
    email = request.form.get('email')
    senha = request.form.get('senha')
    user = User.query.filter_by(email=email).first()
    if user and check_password_hash(user.password_hash, senha):
        session.clear()
        session['user_id'] = user.id
        session['user_name'] = user.name
        return redirect(url_for('views.home_page'))
    else:
        flash('Email ou senha incorretos.', 'error')
        return redirect(url_for('auth.login_page'))

@auth_bp.route('/logout')
def logout():
    session.clear()
    flash('Você saiu da sua conta.', 'success')
    return redirect(url_for('auth.login_page'))