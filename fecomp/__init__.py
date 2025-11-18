import os
from flask import Flask
from .config import Config
from .extensions import db, csrf
from flask_migrate import Migrate

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    csrf.init_app(app)
    
    migrate = Migrate(app, db, render_as_batch=True) 

    if not app.config['OPENAI_API_KEY']:
        print("AVISO: Chave da API do OpenAi não encontrada.")
        
    if not app.config['YOUTUBE_API_KEY']:
        print("AVISO: Chave da API do Youtube não encontrada.")

    from .autenticacao import auth_bp
    from .visoes import views_bp
    from .api import api_bp
    from .tutorial import tutorial_bp
    from .admin import admin_bp 

    app.register_blueprint(auth_bp)
    app.register_blueprint(views_bp)
    app.register_blueprint(api_bp, url_prefix='/api')
    app.register_blueprint(tutorial_bp)
    app.register_blueprint(admin_bp) 

    @app.context_processor
    def inject_static_version():
        def get_version(filename):
            try:
                file_path = os.path.join(app.root_path, 'static', filename)
                timestamp = int(os.path.getmtime(file_path))
                return timestamp
            except Exception as e:
                return 1
        return dict(get_version=get_version)

    with app.app_context():
        pass

    return app