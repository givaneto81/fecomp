import os
import sys
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
sys.path.insert(0, project_root)

from main import app, db

with app.app_context():
    print("Criando tabelas no banco de dados...")
    db.create_all()
    print("Tabelas criadas com sucesso!")