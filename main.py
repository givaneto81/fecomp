import os
import google.generativeai as genai
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
# from dotenv import load_dotenv, find_dotenv
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps

# Carrega as variáveis de ambiente do arquivo .env
# load_dotenv(find_dotenv())

app = Flask(__name__)

# --- CONFIGURAÇÃO DEFINITIVA ---
app.config['SECRET_KEY'] = "santacruzfutebolclube"
DATABASE_URL = "postgresql+pg8000://postgres:neto0203@localhost/educa_ai_db"

# Cria o "motor" da conexão com a codificação correta
engine = create_engine(DATABASE_URL, connect_args={"client_encoding": "utf8"})

# Associa o motor à configuração do Flask
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.debug = True

# Inicializa o db, mas agora ele usará o nosso motor configurado
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
# A definição das classes precisa vir ANTES das rotas que as utilizam.

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

# --- CONFIGURAÇÃO DA API ---
GEMINI_API_KEY = "AIzaSyAgaX9vPj6z6JWY2ArbgeI49gv1WRUQrds"
genai.configure(api_key=GEMINI_API_KEY)

# --- ROTAS DE AUTENTICAÇÃO E PÁGINAS ---

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

# --- ROTAS PROTEGIDAS DO APP ---

@app.route('/home')
@login_required
def home_page():
    user_id = session['user_id']
    user_subjects = Subject.query.filter_by(user_id=user_id).order_by(Subject.name).all()
    return render_template('home.html', subjects=user_subjects)

@app.route('/pastas/<int:subject_id>')
@login_required
def pastas_page(subject_id):
    # primeiro busca a página e dps a matéria
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
    # Lógica do perfil será adicionada depois
    return render_template('perfil.html')

@app.route('/add_subject', methods=['POST'])
@login_required
def add_subject():
    subject_name = request.form.get('subject_name')
    if subject_name:
        user_id = session['user_id']
        new_subject = Subject(name=subject_name, user_id=user_id)
        db.session.add(new_subject)
        db.session.commit()
        flash('Matéria adicionada com sucesso!', 'success')
    else:
        flash('O nome da matéria não pode estar vazio.', 'error')
    return redirect(url_for('home_page'))

@app.route('/add_folder/<int:subject_id>', methods=['POST'])
@login_required
def add_folder(subject_id):
    # Verifica se a matéria pertence ao usuário para segurança
    subject = Subject.query.filter_by(id=subject_id, user_id=session['user_id']).first_or_404()
    
    folder_name = request.form.get('folder_name')
    if folder_name:
        new_folder = Folder(name=folder_name, subject_id=subject.id)
        db.session.add(new_folder)
        db.session.commit()
        flash('Pasta criada com sucesso!', 'success')
    else:
        flash('O nome da pasta não pode estar vazio.', 'error')
    
    # Redireciona de volta para a mesma página de pastas
    return redirect(url_for('pastas_page', subject_id=subject_id))

# --- ROTA DA API DO CHAT ---

@app.route('/api/chat', methods=['POST'])
@login_required
def chat_api():
    user_message = request.json.get('message')

    if not user_message:
        return jsonify({"error": "Mensagem de usuário ausente"}), 400

    try:
        instrucao_sistema = "Você é um assistente de estudos para pré-vestibular. Responda sempre em português do Brasil, de forma clara e didática."

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