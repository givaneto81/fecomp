# fecomp/main.py

import os
import google.generativeai as genai
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps

# Nota: Mantivemos o dotenv aqui para o futuro, mas as chaves estão diretas no código por enquanto.
from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())

app = Flask(__name__)

# --- CONFIGURAÇÃO DO SERVIDOR ---
app.config['SECRET_KEY'] = "santacruzfutebolclube"
app.config['SQLALCHEMY_DATABASE_URI'] = "postgresql+pg8000://postgres:neto0203@localhost/educa_ai_db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.debug = True

db = SQLAlchemy(app)

# --- DECORATOR PARA EXIGIR LOGIN ---
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Por favor, faça login para acessar esta página.', 'error')
            return redirect(url_for('login_page'))
        return f(*args, **kwargs)
    return decorated_function

# --- MODELOS DO BANCO DE DADOS ---
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    subjects = db.relationship('Subject', backref='user', lazy=True, cascade="all, delete-orphan")

class Subject(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    folders = db.relationship('Folder', backref='subject', lazy=True, cascade="all, delete-orphan")

class Folder(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey('subject.id'), nullable=False)

# --- CONFIGURAÇÃO DA API (AGORA CORRETA) ---
GEMINI_API_KEY = "AIzaSyAgaX9vPj6z6JWY2ArbgeI49gv1WRUQrds"
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
else:
    print("AVISO: Chave da API do Gemini não encontrada. O chat não funcionará.")


# --- ROTAS DE AUTENTICAÇÃO ---
@app.route('/')
def login_page():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register_page():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        senha = request.form.get('senha')

        user_exists = User.query.filter_by(email=email).first()
        if user_exists:
            flash('Este email já está cadastrado. Tente fazer login.', 'error')
            return redirect(url_for('login_page'))

        hashed_password = generate_password_hash(senha)
        new_user = User(name=name, email=email, password_hash=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        flash('Cadastro realizado com sucesso! Faça o login.', 'success')
        return redirect(url_for('login_page'))

    return render_template('register.html')

@app.route('/login', methods=['POST'])
def login():
    email = request.form.get('email')
    senha = request.form.get('senha')
    user = User.query.filter_by(email=email).first()

    if user and check_password_hash(user.password_hash, senha):
        session.clear()
        session['user_id'] = user.id
        session['user_name'] = user.name
        return redirect(url_for('home_page'))
    else:
        flash('Email ou senha incorretos.', 'error')
        return redirect(url_for('login_page'))

@app.route('/logout')
def logout():
    session.clear()
    flash('Você saiu da sua conta.', 'success')
    return redirect(url_for('login_page'))


# --- ROTAS PRINCIPAIS DO APP ---
@app.route('/home')
@login_required
def home_page():
    user_id = session['user_id']
    user_subjects = Subject.query.filter_by(user_id=user_id).order_by(Subject.name).all()
    return render_template('home.html', subjects=user_subjects)

@app.route('/pastas/<int:subject_id>')
@login_required
def pastas_page(subject_id):
    subject = Subject.query.filter_by(id=subject_id, user_id=session['user_id']).first_or_404()
    folders = Folder.query.filter_by(subject_id=subject.id).order_by(Folder.name).all()
    return render_template('pastas.html', subject=subject, folders=folders)

@app.route('/chat')
@login_required
def chat_page():
    return render_template('chat.html')

@app.route('/perfil')
@login_required
def perfil_page():
    user = User.query.get(session['user_id'])
    return render_template('perfil.html', user=user)

# --- ROTAS DE AÇÕES (CRIAR MATÉRIAS E PASTAS) ---
@app.route('/add_subject', methods=['POST'])
@login_required
def add_subject():
    subject_name = request.form.get('subject_name')
    if subject_name:
        new_subject = Subject(name=subject_name, user_id=session['user_id'])
        db.session.add(new_subject)
        db.session.commit()
        flash('Matéria adicionada com sucesso!', 'success')
    else:
        flash('O nome da matéria não pode estar vazio.', 'error')
    return redirect(url_for('home_page'))

@app.route('/add_folder/<int:subject_id>', methods=['POST'])
@login_required
def add_folder(subject_id):
    subject = Subject.query.filter_by(id=subject_id, user_id=session['user_id']).first_or_404()
    folder_name = request.form.get('folder_name')
    if folder_name:
        new_folder = Folder(name=folder_name, subject_id=subject.id)
        db.session.add(new_folder)
        db.session.commit()
        flash('Pasta criada com sucesso!', 'success')
    else:
        flash('O nome da pasta não pode estar vazio.', 'error')
    return redirect(url_for('pastas_page', subject_id=subject_id))

# --- ROTAS PARA GERENCIAMENTO DE PERFIL ---
@app.route('/update_profile', methods=['POST'])
@login_required
def update_profile():
    new_name = request.form.get('new_name')
    if new_name:
        user = User.query.get(session['user_id'])
        user.name = new_name
        db.session.commit()
        session['user_name'] = new_name
        flash('Nome atualizado com sucesso!', 'success')
    else:
        flash('O nome não pode ficar em branco.', 'error')
    return redirect(url_for('perfil_page'))

@app.route('/change_password', methods=['POST'])
@login_required
def change_password():
    current_password = request.form.get('current_password')
    new_password = request.form.get('new_password')
    user = User.query.get(session['user_id'])

    if user and check_password_hash(user.password_hash, current_password):
        if new_password:
            user.password_hash = generate_password_hash(new_password)
            db.session.commit()
            flash('Senha alterada com sucesso!', 'success')
        else:
            flash('A nova senha não pode estar em branco.', 'error')
    else:
        flash('A senha atual está incorreta.', 'error')
    return redirect(url_for('perfil_page'))

@app.route('/delete_account', methods=['POST'])
@login_required
def delete_account():
    user = User.query.get(session['user_id'])
    if user:
        db.session.delete(user)
        db.session.commit()
        session.clear()
        flash('Sua conta foi excluída com sucesso.', 'success')
        return redirect(url_for('login_page'))
    flash('Não foi possível excluir a conta.', 'error')
    return redirect(url_for('perfil_page'))

# --- ROTA DA API DO CHAT ---
@app.route('/api/chat', methods=['POST'])
@login_required
def chat_api():
    user_message = request.json.get('message')
    if not user_message:
        return jsonify({"error": "Mensagem ausente"}), 400
    try:
        instrucao_sistema = (
            "Você é um assistente de estudos para pré-vestibular. Responda sempre em português do Brasil, "
            "de forma clara e didática, com um tom leve e divertido, como um amigo ajudando a estudar. "
            "Use analogias criativas (música, séries, comida, etc.) para facilitar o entendimento. "
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

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)