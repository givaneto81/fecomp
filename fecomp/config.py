import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'santacruzfutebolclube'
    SQLALCHEMY_DATABASE_URI = os.environ.get('SQLALCHEMY_DATABASE_URI') or 'sqlite:///site.db'
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = 'fecomp/uploads'
    GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
    DEBUG = True
    MAX_CONTENT_LENGTH = 100 * 1024 * 1024