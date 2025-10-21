import os
import google.generativeai as genai
from flask import Flask
from .config import Config
from .extensions import db, csrf

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    csrf.init_app(app)

    if app.config['GEMINI_API_KEY']:
        genai.configure(api_key=app.config['GEMINI_API_KEY'])
    else:
        print("AVISO: Chave da API do Gemini não encontrada.")

    from .autenticacao import auth_bp
    from .visoes import views_bp
    from .api import api_bp
    from .tutorial import tutorial_bp
    # NÍVEL 4.3: Importa o novo blueprint
    from .admin import admin_bp 

    app.register_blueprint(auth_bp)
    app.register_blueprint(views_bp)
    app.register_blueprint(api_bp, url_prefix='/api')
    app.register_blueprint(tutorial_bp)
    # NÍVEL 4.3: Regista o novo blueprint
    app.register_blueprint(admin_bp) 

    with app.app_context():
        db.create_all()

    return app