import os
from sqlalchemy import create_engine, Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import sessionmaker, relationship, scoped_session
from sqlalchemy.ext.declarative import declarative_base
from fecomp import create_app
from fecomp.models import User as NewUser, db as new_db

# --- Configuração do Banco de Dados ANTIGO ---
# Define o caminho para o banco antigo que copiamos
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
OLD_DB_PATH = os.path.join(BASE_DIR, 'sitevelho.db')
OLD_DB_URI = 'sqlite:///' + OLD_DB_PATH

# Cria uma "Base" para definir os modelos do banco antigo
OldBase = declarative_base()

# --- Definição dos Modelos ANTIGOS ---
# (Copiado de EducaAi/fecomp/models.py)
# Precisamos definir como era a tabela 'user' antiga
class OldUser(OldBase):
    __tablename__ = 'user'
    id = Column(Integer, primary_key=True)
    name = Column(String(150), nullable=False)
    email = Column(String(150), unique=True, nullable=False)
    password_hash = Column(String(256), nullable=False)
    tutorial_concluido = Column(Boolean, default=False, nullable=False)

# --- Função Principal de Migração ---
def migrate_users():
    print("Iniciando script de migração de usuários...")

    # 1. Conecta ao Banco de Dados ANTIGO
    old_engine = create_engine(OLD_DB_URI)
    OldSession = sessionmaker(bind=old_engine)
    old_session = OldSession()

    # 2. Conecta ao Banco de Dados NOVO (usando o contexto do app)
    app = create_app()
    with app.app_context():
        
        print(f"Conectado ao DB NOVO: {app.config['SQLALCHEMY_DATABASE_URI']}")
        print(f"Conectado ao DB ANTIGO: {OLD_DB_URI}")
        
        # 3. Pega todos os emails que JÁ EXISTEM no banco novo
        try:
            existing_emails = {user.email for user in new_db.session.query(NewUser.email).all()}
            print(f"Encontrados {len(existing_emails)} usuários existentes no banco NOVO.")
        except Exception as e:
            print(f"!!! ERRO ao ler o banco NOVO: {e}")
            print("Verifica se o caminho 'fecompzera/instance/site.db' está correto.")
            return

        # 4. Pega todos os usuários do banco ANTIGO
        try:
            old_users = old_session.query(OldUser).all()
            print(f"Encontrados {len(old_users)} usuários no banco ANTIGO para migrar.")
        except Exception as e:
            print(f"!!! ERRO ao ler o banco ANTIGO: {e}")
            print("Verifica se o arquivo 'sitevelho.db' está na raiz do projeto fecompzera.")
            old_session.close()
            return
            
        new_users_count = 0
        skipped_users_count = 0

        # 5. Loop de Migração
        for old_user in old_users:
            if old_user.email in existing_emails:
                print(f"  [SKIP] Usuário já existe: {old_user.email}")
                skipped_users_count += 1
                continue
            
            # 6. Se o usuário é novo, cria ele no banco NOVO
            print(f"  [ADD] Migrando novo usuário: {old_user.email}")
            
            new_user = NewUser(
                name=old_user.name,
                email=old_user.email,
                password_hash=old_user.password_hash,
                tutorial_concluido=old_user.tutorial_concluido,
                role='aluno'  # <--- AQUI A MÁGICA! Todos entram como aluno.
            )
            new_db.session.add(new_user)
            new_users_count += 1

        # 7. Salva (Commita) tudo no banco NOVO
        if new_users_count > 0:
            try:
                new_db.session.commit()
                print(f"\nSucesso! {new_users_count} novos usuários foram adicionados ao banco de dados.")
            except Exception as e:
                new_db.session.rollback()
                print(f"\n!!! ERRO AO SALVAR NO BANCO NOVO: {e}")
        else:
            print("\nNenhum usuário novo para adicionar.")
            
        print(f"Total de usuários pulados (já existentes): {skipped_users_count}")

    # Fecha a sessão antiga
    old_session.close()
    print("Script finalizado.")

# --- Roda a função ---
if __name__ == '__main__':
    migrate_users()