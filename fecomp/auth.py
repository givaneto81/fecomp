from flask import Blueprint, render_template, request, redirect, url_for, flash, session, current_app
from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadTimeSignature
from . import db, mail, oauth
from .models import User
from flask_mail import Message

auth_bp = Blueprint('auth', __name__)

# --- ROTAS DE AUTENTICAÇÃO ---
@auth_bp.route('/')
def login_page():
    return render_template('index.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register_page():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip().lower()
        senha = request.form.get('senha')

        if not name or not email or not senha:
            flash('Todos os campos são obrigatórios.', 'error')
            return render_template('register.html', name=name, email=email)

        # Adicionar validação de e-mail (simples)
        if '@' not in email or '.' not in email:
            flash('Formato de e-mail inválido.', 'error')
            return render_template('register.html', name=name, email=email)

        user_exists = User.query.filter_by(email=email).first()
        if user_exists:
            flash('Este email já está cadastrado. Tente fazer login.', 'error')
            return redirect(url_for('auth.login_page'))

        hashed_password = generate_password_hash(senha)
        new_user = User(name=name, email=email, password_hash=hashed_password)
        db.session.add(new_user)
        db.session.commit()

        try:
            send_verification_email(new_user.email)
            flash('Cadastro realizado! Um link de verificação foi enviado para o seu e-mail.', 'success')
        except Exception as e:
            # Em caso de falha no envio de e-mail, o usuário não deve ser bloqueado
            # O ideal seria ter um mecanismo para reenviar o e-mail
            print(f"Falha ao enviar e-mail de verificação para {email}: {e}")
            flash('Cadastro realizado com sucesso! Houve um problema ao enviar o e-mail de verificação. Contate o suporte.', 'warning')

        return redirect(url_for('auth.login_page'))

    return render_template('register.html')

@auth_bp.route('/login', methods=['POST'])
def login():
    email = request.form.get('email', '').strip().lower()
    senha = request.form.get('senha')

    if not email or not senha:
        flash('Email e senha são obrigatórios.', 'error')
        return redirect(url_for('auth.login_page'))

    user = User.query.filter_by(email=email).first()

    if user and user.password_hash and check_password_hash(user.password_hash, senha):
        if not user.is_verified:
            flash('Sua conta não foi verificada. Por favor, verifique seu e-mail.', 'warning')
            return redirect(url_for('auth.login_page'))

        session.clear()
        session['user_id'] = user.id
        session['user_name'] = user.name
        # Adiciona proteção contra fixação de sessão
        session.permanent = True
        return redirect(url_for('views.home_page'))
    else:
        flash('Email ou senha incorretos.', 'error')
        return redirect(url_for('auth.login_page'))

@auth_bp.route('/logout')
def logout():
    session.clear()
    flash('Você saiu da sua conta.', 'success')
    return redirect(url_for('auth.login_page'))

# --- ROTAS DE VERIFICAÇÃO DE E-MAIL ---
def send_verification_email(email):
    serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    token = serializer.dumps(email, salt='email-confirm')

    link = url_for('auth.verify_email', token=token, _external=True)

    msg = Message(
        'Confirme seu E-mail - Educa AI',
        sender=current_app.config['MAIL_USERNAME'],
        recipients=[email],
        body=f'Clique no link para verificar seu e-mail: {link}'
    )
    mail.send(msg)

@auth_bp.route('/verify_email/<token>')
def verify_email(token):
    serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    try:
        email = serializer.loads(
            token,
            salt='email-confirm',
            max_age=3600  # Token válido por 1 hora
        )
    except (SignatureExpired, BadTimeSignature):
        flash('O link de verificação é inválido ou expirou.', 'error')
        return redirect(url_for('auth.login_page'))

    user = User.query.filter_by(email=email).first_or_404()
    if user.is_verified:
        flash('Sua conta já foi verificada. Faça o login.', 'info')
    else:
        user.is_verified = True
        db.session.commit()
        flash('Seu e-mail foi verificado com sucesso! Você já pode fazer login.', 'success')

    return redirect(url_for('auth.login_page'))

# --- ROTAS DE LOGIN COM GOOGLE (OAUTH) ---
@auth_bp.route('/google-login')
def google_login():
    redirect_uri = url_for('auth.authorize', _external=True)
    return oauth.google.authorize_redirect(redirect_uri)

@auth_bp.route('/authorize')
def authorize():
    try:
        token = oauth.google.authorize_access_token()
        user_info = oauth.google.parse_id_token(token)
    except Exception as e:
        flash(f"Erro durante a autenticação com o Google: {e}", "error")
        return redirect(url_for('auth.login_page'))

    email = user_info['email']
    name = user_info['name']

    user = User.query.filter_by(email=email).first()
    if not user:
        # Cria um novo usuário se não existir
        user = User(
            email=email,
            name=name,
            is_verified=True  # Contas do Google são consideradas verificadas
        )
        db.session.add(user)
        db.session.commit()
        flash('Conta criada com sucesso através do Google!', 'success')
    elif not user.is_verified:
        # Se o usuário já existia mas não era verificado
        user.is_verified = True
        db.session.commit()

    session.clear()
    session['user_id'] = user.id
    session['user_name'] = user.name
    return redirect(url_for('views.home_page'))