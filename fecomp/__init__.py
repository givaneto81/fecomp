import os
import google.generativeai as genai
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from .config import Config

# 1. Inicializa a extensão aqui, mas sem a ligar a uma aplicação
db = SQLAlchemy()

def create_app():
    """Cria e configura uma instância da aplicação Flask."""
    app = Flask(__name__)

    # 2. Carrega a configuração
    app.config.from_object(Config)

    # 3. Agora, liga o 'db' à aplicação que acabámos de criar
    db.init_app(app)

    # Configura a API do Gemini
    if app.config['GEMINI_API_KEY']:
        genai.configure(api_key=app.config['GEMINI_API_KEY'])
    else:
        print("AVISO: Chave da API do Gemini não encontrada. O chat não funcionará.")

    # 4. IMPORTANTE: importei os blueprints AQUI, dentro da função
    from . import auth
    from . import views
    from . import api

    # 5. E agora registamo-los
    app.register_blueprint(auth.auth_bp)
    app.register_blueprint(views.views_bp)
    app.register_blueprint(api.api_bp, url_prefix='/api')

    with app.app_context():
        # Cria as tabelas da base de dados, se não existirem
        db.create_all()

    return app