import os
import google.generativeai as genai
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'santacruzfutebolclube')
app.debug = True

# Simulação de dados de usuário
USUARIO_ADMIN = {
    "email": "admin@admin",
    "senha": "admin"
}

# Configuração da API Key do Gemini
genai.configure(api_key="AIzaSyAgaX9vPj6z6JWY2ArbgeI49gv1WRUQrds")

# --- Rotas do Frontend ---

@app.route('/')
def login_page():
    return render_template('index.html')

@app.route('/home')
def home_page():
    return render_template('home.html')

@app.route('/pastas')
def pastas_page():
    return render_template('pastas.html')

@app.route('/chat')
def chat_page():
    return render_template('chat.html')

@app.route('/perfil')
def perfil_page():
    return render_template('perfil.html')

# --- Lógica de Autenticação ---

@app.route('/login', methods=['POST'])
def login():
    email = request.form.get('email')
    senha = request.form.get('senha')

    if email == USUARIO_ADMIN["email"] and senha == USUARIO_ADMIN["senha"]:
        session['logged_in'] = True
        session['email'] = email
        return redirect(url_for('home_page'))
    else:
        flash('Email ou senha incorretos.', 'error')
        return redirect(url_for('login_page'))

# --- Rota para a API do Gemini s--

@app.route('/api/chat', methods=['POST'])
def chat_api():
    user_message = request.json.get('message')

    if not user_message:
        return jsonify({"error": "Mensagem de usuário ausente"}), 400

    try:
        # Use o nome do modelo listado pelo passo anterior
        model = genai.GenerativeModel('models/gemini-1.5-pro-latest')
        response = model.generate_content(user_message)
        bot_response = getattr(response, "text", None)

        if not bot_response or not bot_response.strip():
            return jsonify({"response": ""}), 200

        return jsonify({"response": bot_response})

    except Exception as e:
        print("Erro Gemini:", e)
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    # Use o servidor de desenvolvimento do Flask
    app.run(host='0.0.0.0', port=5000)