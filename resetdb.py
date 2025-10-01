from fecomp import create_app, db

# cria uma instância da sua aplicação Flask
app = create_app()

# usa o contexto da aplicação para garantir que as operações do banco de dados funcionem corretamente
with app.app_context():
    print("Apagando todas as tabelas do banco de dados...")
    db.drop_all()
    print("Criando as tabelas novamente com base nos models...")
    db.create_all()
    print("Banco de dados resetado com sucesso!")