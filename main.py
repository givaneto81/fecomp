from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

# Simulação de um usuário no "banco de dados"
# Você pode mudar o email e a senha aqui
usuario_teste = {
    "email": "admin@admin",
    "senha": "admin"
}

# Rota para a página de login (index.html)
@app.route('/')
def login_page():
    return render_template('index.html')

# Rota para processar o formulário de login
@app.route('/login', methods=['POST'])
def login():
    email = request.form['email']
    senha = request.form['senha']

    # Lógica de verificação do usuário (sem SQL)
    if email == usuario_teste["email"] and senha == usuario_teste["senha"]:
        # Login bem-sucedido, redireciona para a página principal
        return redirect(url_for('home_page'))
    else:
        # Login falhou, mostra uma mensagem de erro
        return "Login falhou. Tente novamente."

# Rota para a página principal (home)
@app.route('/home')
def home_page():
    return render_template('home.html')

if __name__ == '__main__':
    app.run(debug=True)