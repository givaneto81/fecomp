import os
from flask import Flask
from .config import Config
from .extensions import db, csrf

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    csrf.init_app(app)

    if not app.config['OPENAI_API_KEY']:
        print("AVISO: Chave da API do OpenAi não encontrada.")
        
    if not app.config['YOUTUBE_API_KEY']:
        print("AVISO: Chave da API do Youtube não encontrada.")

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