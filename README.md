# Educa AI - Repositório Acadêmico Inteligente

Educa AI é uma aplicação web desenvolvida em Flask que funciona como um repositório acadêmico pessoal. A plataforma permite que estudantes organizem seus materiais de estudo por matérias e pastas, além de oferecer um chatbot integrado com a API do Google Gemini para auxiliar nos estudos.

## Features

- **Autenticação de Usuários:** Sistema completo de registro, login e logout.
- **Organização por Matérias:** Crie matérias personalizadas para cada disciplina que você está estudando.
- **Sistema de Pastas:** Dentro de cada matéria, crie pastas para organizar seus arquivos, como resumos, listas de exercícios e anotações.
- **Upload de Arquivos:** Faça o upload de seus materiais de estudo diretamente para as pastas correspondentes.
- **Chatbot com IA:** Converse com um assistente de estudos inteligente (powered by Google Gemini) para tirar dúvidas e obter explicações sobre os mais variados tópicos.
- **Customização:** Personalize a cor de suas matérias e pastas para uma melhor organização visual.
- **Gerenciamento de Perfil:** Atualize seu nome, altere sua senha ou exclua sua conta com facilidade.
- **Interface Responsiva:** Acesse a plataforma de qualquer dispositivo.

## Getting Started

Para rodar o projeto localmente, siga os passos abaixo.

### Pré-requisitos

- Python 3.6+
- PostgreSQL (ou outro banco de dados de sua preferência, com o devido ajuste na URI de conexão)

### Instalação

1. **Clone o repositório:**
   ```bash
   git clone https://github.com/seu-usuario/educa-ai.git
   cd educa-ai
   ```

2. **Crie e ative um ambiente virtual:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # No Windows, use `venv\Scripts\activate`
   ```

3. **Instale as dependências:**
   ```bash
   pip install -r requirements.txt
   ```
   ** Requirements.txt: **
   ```md
   Flask
   Flask-SQLAlchemy
   psycopg2-binary  # ou o driver do seu banco
   google-generativeai
   werkzeug
   ```

4. **Configure o Banco de Dados:**
   - Crie um banco de dados no PostgreSQL.
   - Atualize a string de conexão `SQLALCHEMY_DATABASE_URI` no arquivo `main.py` com suas credenciais:
     ```python
     app.config['SQLALCHEMY_DATABASE_URI'] = "postgresql://SEU_USUARIO:SUA_SENHA@localhost/SEU_BANCO"
     ```

5. **Configure a API do Gemini:**
   - Obtenha uma chave de API do [Google AI Studio](https://aistudio.google.com/).
   - Insira sua chave no campo `GEMINI_API_KEY` em `main.py`:
     ```python
     GEMINI_API_KEY = "SUA_CHAVE_API_AQUI"
     ```

6. **Inicialize o Banco de Dados:**
   - Abra um shell Python no seu terminal e execute o seguinte para criar as tabelas:
     ```python
     from main import app, db
     with app.app_context():
     db.create_all()
     ```

### Executando a Aplicação

Para iniciar o servidor Flask, execute:

```bash
python main.py
```

Acesse a aplicação em `http://127.0.0.1:5000` no seu navegador.

## Tecnologias Utilizadas

- **Backend:** Flask
- **Banco de Dados:** PostgreSQL com SQLAlchemy
- **Inteligência Artificial:** Google Gemini Pro
- **Frontend:** HTML, CSS, JavaScript
- **Ícones:** Feather Icons
