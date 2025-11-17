import os
from flask import Blueprint, request, jsonify, session, url_for, current_app
from functools import wraps
import random
import PyPDF2
import docx
import openai
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from .models import Subject, User, Folder
from .extensions import db, csrf 
from .visoes import check_permission, login_required

api_bp = Blueprint('api', __name__)

DICAS = [
    "Revise as funções logarítmicas — elas caem muito no ENEM!",
    "Leia uma redação nota 1000 e anote as estruturas usadas.",
    "Treine sua interpretação de texto em inglês.",
    "Reveja os ciclos biogeoquímicos (SSA 2 adora cobrar isso!).",
    "Não se esqueça de estudar a história de Pernambuco para o SSA.",
    "Pratique a resolução da prova do ENEM por área de conhecimento, cronometrando o tempo.",
    "Crie flashcards para memorizar fórmulas de Física e Química."
]

# --- ROTA DE CHAT GERAL (AGORA COM GPT) ---
@api_bp.route('/chat', methods=['POST'])
@csrf.exempt
@login_required
def chat_api():
    user_message = request.json.get('message')
    if not user_message:
        return jsonify({"error": "Mensagem ausente"}), 400
    
    try:
        # 1. Pega a chave do config
        api_key = current_app.config['OPENAI_API_KEY']
        if not api_key:
            return jsonify({"error": "API da OpenAI não configurada."}), 500
            
        client = openai.OpenAI(api_key=api_key)
        
        # 2. Define o "system prompt" (personalidade)
        system_prompt = (
            "Você é o 'Educa AI', um assistente de estudos inteligente e amigável. "
            "Seu público são estudantes de pré-vestibular (ENEM e SSA). "
            "Responda às suas dúvidas de forma didática, clara e encorajadora. "
            "Use formatação markdown (como **negrito** e *itálico*) para organizar a resposta. "
            "Seja direto e foque no conteúdo acadêmico."
        )
        
        # 3. Faz a chamada para o GPT
        response = client.chat.completions.create(
            model="gpt-3.5-turbo", # Ou "gpt-4", "gpt-4o", etc.
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ]
        )
        
        # 4. Retorna a resposta
        return jsonify(response=response.choices[0].message.content)

    except openai.RateLimitError:
        print("Erro na API OpenAI: Rate Limit (limite estourado)")
        return jsonify({"error": "Limite de uso da API de texto atingido."}), 429
    except Exception as e:
        print(f"Erro na API OpenAI: {e}")
        return jsonify({"error": "Ocorreu um erro ao processar sua solicitação com a IA.", "details": str(e)}), 500

# --- FUNÇÃO HELPER DE RAG (Mantida) ---
def extract_text_from_file(file_path, original_filename):
    text = ""
    try:
        if original_filename.lower().endswith('.pdf'):
            with open(file_path, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                for page in reader.pages:
                    text += page.extract_text() + "\n"
        elif original_filename.lower().endswith('.docx'):
            doc = docx.Document(file_path)
            for para in doc.paragraphs:
                text += para.text + "\n"
        elif original_filename.lower().endswith('.txt'):
            with open(file_path, 'r', encoding='utf-8') as f:
                text = f.read()
    except Exception as e:
        print(f"Erro ao extrair texto do arquivo {original_filename}: {e}")
        return f"[Erro ao ler o arquivo {original_filename}]\n"
    return text

# --- ROTA DE CHAT CONTEXTUAL (RAG/GPT) [MODIFICADA] ---
@api_bp.route('/chat_contextual', methods=['POST'])
@csrf.exempt
@login_required
def chat_contextual_api():
    data = request.json
    user_message = data.get('message')
    folder_id = data.get('folder_id')
    if not user_message or not folder_id:
        return jsonify({"error": "Mensagem ou ID da pasta ausente"}), 400

    folder = Folder.query.get_or_404(folder_id)
    subject = folder.subject

    if not check_permission(subject): # ... (Lógica de permissão mantida)
        user = User.query.get(session['user_id'])
        is_member = False
        if subject.course_id:
            is_member = user.courses.filter_by(id=subject.course_id).first() is not None
        if not is_member:
            return jsonify({"error": "Você não tem permissão para acessar esta pasta."}), 403

    # 2. Extrair contexto (Lógica mantida)
    context = ""
    upload_folder_abs = os.path.join(current_app.root_path, current_app.config['UPLOAD_FOLDER'].split('/')[-1])
    files_in_folder = folder.files
    if not files_in_folder:
         return jsonify(response="Esta pasta está vazia. Não há conteúdo para eu analisar.")

    for file_db in files_in_folder:
        file_path = os.path.join(upload_folder_abs, file_db.filename)
        if os.path.exists(file_path):
            context += f"--- Início do Documento: {file_db.original_filename} ---\n"
            context += extract_text_from_file(file_path, file_db.original_filename)
            context += f"--- Fim do Documento: {file_db.original_filename} ---\n\n"

    if not context.strip():
        return jsonify(response="Não consegui extrair texto legível dos arquivos nesta pasta...")

    # 3. Chamar a IA (RAG com GPT)
    try:
        api_key = current_app.config['OPENAI_API_KEY']
        if not api_key:
            return jsonify({"error": "API da OpenAI não configurada."}), 500
            
        client = openai.OpenAI(api_key=api_key)
        
        system_prompt = (
            "Você é um assistente de estudos focado. Responda à pergunta do aluno usando **única e exclusivamente** as informações fornecidas no 'CONTEXTO' abaixo. "
            "Não use nenhum conhecimento externo."
            "Se a resposta não estiver no contexto, diga: 'Não encontrei essa informação nos documentos desta pasta.' "
            "Seja direto e organize a resposta com markdown."
        )
        
        # Montamos o prompt final para o GPT
        full_prompt = f"CONTEXTO:\n{context}\n\nDÚVIDA DO ALUNO: {user_message}"

        response = client.chat.completions.create(
            model="gpt-3.5-turbo", # Ou o modelo que preferir
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": full_prompt}
            ]
        )
        return jsonify(response=response.choices[0].message.content)

    except openai.RateLimitError:
        print("Erro na API OpenAI (RAG): Rate Limit (limite estourado)")
        return jsonify({"error": "Limite de uso da API de texto atingido."}), 429
    except Exception as e:
        print(f"Erro na API OpenAI (RAG): {e}")
        return jsonify({"error": "Ocorreu um erro ao processar sua solicitação com a IA.", "details": str(e)}), 500


# <<< ROTA DO YOUTUBE (MANTIDA) >>>
@api_bp.route('/buscar_videos', methods=['POST'])
@csrf.exempt
@login_required
def buscar_videos_api():
    query = request.json.get('query')
    if not query:
        return jsonify({"error": "Termo de busca ausente"}), 400
        
    api_key = current_app.config['YOUTUBE_API_KEY']
    if not api_key:
        return jsonify({"error": "API do YouTube não configurada no servidor."}), 500

    try:
        youtube = build('youtube', 'v3', developerKey=api_key)
        search_response = youtube.search().list(
            q=query,
            part='snippet',
            maxResults=3,
            type='video',
            relevanceLanguage='pt',
            regionCode='BR'
        ).execute()
        
        videos = []
        for item in search_response.get('items', []):
            videos.append({
                'title': item['snippet']['title'],
                'video_id': item['id']['videoId'],
                'thumbnail': item['snippet']['thumbnails']['medium']['url'],
                'channel': item['snippet']['channelTitle']
            })
            
        return jsonify(videos=videos)

    except Exception as e:
        print(f"Erro na busca de vídeo: {e}")
        return jsonify(videos=[], error=str(e))

# OUTRAS ROTAS ----------------------------

@api_bp.route('/dica_do_dia')
@login_required
def dica_do_dia():
    return jsonify(dica=random.choice(DICAS))

@api_bp.route('/user_contexts')
@login_required
def get_user_contexts():
    user = User.query.get(session['user_id'])
    contexts = []
    # Pessoais
    personal_subjects = Subject.query.filter_by(user_id=user.id).order_by(Subject.name).all()
    for subject in personal_subjects:
        for folder in subject.folders:
            contexts.append({
                'id': folder.id,
                'name': f"Pessoal: {subject.name} / {folder.name}"
            })
    # Turmas
    user_course_ids = [c.id for c in user.courses]
    course_subjects = Subject.query.filter(Subject.course_id.in_(user_course_ids)).order_by(Subject.course_id, Subject.name).all()
    for subject in course_subjects:
        for folder in subject.folders:
            contexts.append({
                'id': folder.id,
                'name': f"{subject.course.name}: {subject.name} / {folder.name}"
            })
    return jsonify(contexts=contexts)

@api_bp.route('/add_subject', methods=['POST'])
@csrf.exempt
@login_required
def add_subject_api():
    data = request.get_json()
    subject_name = data.get('subject_name')
    if not subject_name:
        return jsonify({"error": "O nome da matéria não pode estar vazio."}), 400
    new_subject = Subject(name=subject_name, user_id=session['user_id'])
    db.session.add(new_subject)
    db.session.commit()
    subject_data = {
        "id": new_subject.id,
        "name": new_subject.name,
        "color": new_subject.color,
        "urls": {
            "pastas": url_for('visoes.pastas_page', subject_id=new_subject.id),
            "delete": url_for('visoes.delete_subject', subject_id=new_subject.id),
            "update_color": url_for('visoes.update_subject_color', subject_id=new_subject.id)
        }
    }
    return jsonify({"subject": subject_data}), 201