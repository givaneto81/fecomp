import os
from dotenv import load_dotenv

# Carrega as variáveis de ambiente do arquivo .env
load_dotenv()

class Config:
    """Classe de configuração para a aplicação Flask."""
    # Chave secreta para segurança da sessão
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'santacruzfutebolclube '

    # Configuração do banco de dados PostgreSQL
    SQLALCHEMY_DATABASE_URI = os.environ.get('SQLALCHEMY_DATABASE_URI')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Pasta para uploads de arquivos
    UPLOAD_FOLDER = 'fecomp/uploads'

    # Chave da API do Google Gemini
    GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')

    # Configurações de Debug
    DEBUG = True