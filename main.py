from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

# Simula um acesso já que eu não consegui configurar o banco de dados
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

    if email == usuario_teste["email"] and senha == usuario_teste["senha"]:
        return redirect(url_for('home_page'))
    else:
        return "Login falhou. Tente novamente."

@app.route('/home')
def home_page():
    return render_template('home.html')

# ----- Rotas para outras páginas -----

# Rota para a página de Pastas
@app.route('/pastas')
def pastas_page():
    return render_template('pastas.html')

# Rota para a página de chat
@app.route('/chat')
def chat_page():
    return render_template('chat.html')

# Rota para a página de Perfil (em construção) 
@app.route('/perfil')
def perfil_page():
    return "<h1>Página de Perfil em Construção</h1>"

if __name__ == '__main__':
    app.run(debug=True)