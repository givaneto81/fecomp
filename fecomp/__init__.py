import os
import google.generativeai as genai
from flask import Flask, session, redirect, url_for, flash, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail
from authlib.integrations.flask_client import OAuth
from functools import wraps
from config import Config

db = SQLAlchemy()
mail = Mail()
oauth = OAuth()

def create_app():
    app = Flask(__name__, template_folder='../templates', static_folder='../static')
    app.config.from_object(Config)

    # Inicializa as extensões
    db.init_app(app)
    mail.init_app(app)
    oauth.init_app(app)

    # Configura o cliente OAuth do Google
    oauth.register(
        name='google',
        client_id=app.config['GOOGLE_CLIENT_ID'],
        client_secret=app.config['GOOGLE_CLIENT_SECRET'],
        server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
        client_kwargs={'scope': 'openid email profile'}
    )

    # Configura a API do Gemini
    if app.config['GEMINI_API_KEY']:
        genai.configure(api_key=app.config['GEMINI_API_KEY'])
    else:
        print("AVISO: Chave da API do Gemini não encontrada. O chat não funcionará.")

    with app.app_context():
        from . import models

        # Cria as tabelas do banco de dados se não existirem
        db.create_all()

        # Importa e registra os Blueprints
        from .auth import auth_bp
        from .views import views_bp
        from .api import api_bp

        app.register_blueprint(auth_bp, url_prefix='/')
        app.register_blueprint(views_bp, url_prefix='/')
        app.register_blueprint(api_bp, url_prefix='/api')

        # --- REGISTRO DOS HANDLERS DE ERRO ---
        @app.errorhandler(404)
        def not_found_error(error):
            return render_template('errors/404.html'), 404

        @app.errorhandler(500)
        def internal_error(error):
            # Em caso de erro 500, é importante fazer rollback da sessão do DB
            # para evitar estados inconsistentes.
            db.session.rollback()
            return render_template('errors/500.html'), 500

        # --- CABEÇALHOS DE SEGURANÇA ---
        @app.after_request
        def add_security_headers(response):
            response.headers['X-Frame-Options'] = 'SAMEORIGIN'
            response.headers['X-Content-Type-Options'] = 'nosniff'
            response.headers['Content-Security-Policy'] = (
                "default-src 'self'; "
                "script-src 'self' https://fonts.googleapis.com; "
                "style-src 'self' https://fonts.googleapis.com; "
                "font-src 'self' https://fonts.gstatic.com; "
                "img-src 'self' data: https://lh3.googleusercontent.com;" # Permite imagens do próprio domínio, data URIs e avatares do Google
            )
            response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
            return response

        return app

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Por favor, faça login para acessar esta página.', 'error')
            return redirect(url_for('auth.login_page'))

        # Adiciona verificação de email verificado
        from .models import User
        user = User.query.get(session['user_id'])
        if not user or not user.is_verified:
            flash('Por favor, verifique seu e-mail para continuar.', 'warning')
            # O ideal é ter uma página específica para notificar sobre a verificação
            return redirect(url_for('auth.login_page'))

        return f(*args, **kwargs)
    return decorated_function