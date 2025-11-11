import os
from flask import Blueprint, request, jsonify, session, url_for, current_app
from functools import wraps
import random
import google.generativeai as genai
import PyPDF2
import docx
from .models import Subject, User, Folder
from .extensions import db, csrf 
from .visoes import check_permission

api_bp = Blueprint('api', __name__)

# Lista de Dicas para o ENEM e SSA
DICAS = [
    "Revise as funções logarítmicas — elas caem muito no ENEM!",
    "Leia uma redação nota 1000 e anote as estruturas usadas.",
    "Treine sua interpretação de texto em inglês.",
    "Reveja os ciclos biogeoquímicos (SSA 2 adora cobrar isso!).",
    "Não se esqueça de estudar a história de Pernambuco para o SSA.",
    "Pratique a resolução da prova do ENEM por área de conhecimento, cronometrando o tempo.",
    "Crie flashcards para memorizar fórmulas de Física e QuíMica."
]

# Decorator para exigir login nas rotas da API
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({"error": "Autenticação necessária"}), 401
        return f(*args, **kwargs)
    return decorated_function

@api_bp.route('/dica_do_dia')
@login_required
def dica_do_dia():
    """
    Retorna uma dica de estudo aleatória da lista de DICAS.
    """
    return jsonify(dica=random.choice(DICAS))

@api_bp.route('/user_contexts')
@login_required
def get_user_contexts():
    """ Retorna as matérias e pastas do usuário para o seletor do chat. """
    user = User.query.get(session['user_id'])
    
    contexts = []
    
    # 1. Matérias Pessoais
    personal_subjects = Subject.query.filter_by(user_id=user.id).order_by(Subject.name).all()
    for subject in personal_subjects:
        for folder in subject.folders:
            contexts.append({
                'id': folder.id,
                'name': f"Pessoal: {subject.name} / {folder.name}"
            })
            
    # 2. Matérias de Turmas
    user_course_ids = [c.id for c in user.courses]
    course_subjects = Subject.query.filter(Subject.course_id.in_(user_course_ids)) \
                                .order_by(Subject.course_id, Subject.name).all()
                                
    for subject in course_subjects:
        for folder in subject.folders:
            contexts.append({
                'id': folder.id,
                'name': f"{subject.course.name}: {subject.name} / {folder.name}"
            })
            
    return jsonify(contexts=contexts)

# NÍVEL 2.2: ESTA ROTA AGORA CRIA APENAS MATÉRIAS PESSOAIS
@api_bp.route('/add_subject', methods=['POST'])
@csrf.exempt
@login_required
def add_subject_api():
    """
    Cria uma nova matéria PESSOAL para o utilizador logado.
    """
    data = request.get_json()
    subject_name = data.get('subject_name')

    if not subject_name:
        return jsonify({"error": "O nome da matéria não pode estar vazio."}), 400

    # NÍVEL 2.1: Define explicitamente o user_id (matéria pessoal)
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


@api_bp.route('/chat', methods=['POST'])
@csrf.exempt
@login_required
def chat_api():
    user_message = request.json.get('message')
    if not user_message:
        return jsonify({"error": "Mensagem ausente"}), 400
    
    try:
        # --- IMPLEMENTAÇÃO 3: Lógica real da API Gemini ---
        
        # --- CORREÇÃO DE DEBUG 4 (Final) ---
        # Usando 'gemini-pro', o mais estável.
        model = genai.GenerativeModel('gemini-pro') 
        # --- FIM DA CORREÇÃO ---
        
        # 2. (Opcional) Define um contexto/prompt de sistema
        system_prompt = (
            "Você é o 'Educa AI', um assistente de estudos inteligente e amigável. "
            "Seu público são estudantes de pré-vestibular (ENEM e SSA). "
            "Responda às suas dúvidas de forma didática, clara e encorajadora. "
            "Use formatação markdown (como **negrito** e *itálico*) para organizar a resposta. "
            "Seja direto e foque no conteúdo acadêmico."
        )

        # 3. Gera a resposta
        full_prompt = f"{system_prompt}\n\nDúvida do Aluno: {user_message}"
        response = model.generate_content(full_prompt)
        
        # 4. Retorna a resposta
        return jsonify(response=response.text)
        # --- FIM DA IMPLEMENTAÇÃO 3 ---

    except Exception as e:
        print(f"Erro na API Gemini: {e}")
        return jsonify({"error": "Ocorreu um erro ao processar sua solicitação com a IA.", "details": str(e)}), 500

# --- NOVA FUNÇÃO HELPER (PROPOSTA 1) ---
def extract_text_from_file(file_path, original_filename):
    """ Extrai texto de arquivos .pdf, .docx e .txt. """
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

# --- NOVA ROTA (PROPOSTA 1) ---
@api_bp.route('/chat_contextual', methods=['POST'])
@csrf.exempt
@login_required
def chat_contextual_api():
    """
    Responde a uma pergunta do usuário baseando-se APENAS
    no conteúdo de texto dos arquivos (.pdf, .docx, .txt) 
    dentro de uma pasta específica.
    """
    data = request.json
    user_message = data.get('message')
    folder_id = data.get('folder_id')

    if not user_message or not folder_id:
        return jsonify({"error": "Mensagem ou ID da pasta ausente"}), 400

    folder = Folder.query.get_or_404(folder_id)
    subject = folder.subject

    # 1. Verificar permissão (reutiliza a função de 'visoes')
    if not check_permission(subject):
        user = User.query.get(session['user_id'])
        is_member = False
        if subject.course_id:
            is_member = user.courses.filter_by(id=subject.course_id).first() is not None
        if not is_member:
            return jsonify({"error": "Você não tem permissão para acessar esta pasta."}), 403

    # 2. Extrair contexto
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
        return jsonify(response="Não consegui extrair texto legível dos arquivos nesta pasta (PDFs de imagem, .png, etc.). Tente com arquivos .txt, .docx ou PDFs baseados em texto.")

    # 3. Chamar a IA com o prompt RAG
    try:
        # --- CORREÇÃO DE DEBUG 4 (Final) ---
        # Usando 'gemini-pro', o mais estável.
        model = genai.GenerativeModel('gemini-pro')
        # --- FIM DA CORREÇÃO ---
        
        system_prompt = (
            "Você é um assistente de estudos focado. Responda à pergunta do aluno usando **única e exclusivamente** as informações fornecidas no 'CONTEXTO' abaixo. "
            "Não use nenhum conhecimento externo."
            "Se a resposta não estiver no contexto, diga: 'Não encontrei essa informação nos documentos desta pasta.' "
            "Seja direto e organize a resposta com markdown (negrito, listas) se necessário."
        )

        full_prompt = f"{system_prompt}\n\nCONTEXTO:\n{context}\n\nDÚVIDA DO ALUNO: {user_message}"
        response = model.generate_content(full_prompt)
        
        return jsonify(response=response.text)

    except Exception as e:
        print(f"Erro na API Gemini (RAG): {e}")
        return jsonify({"error": "Ocorreu um erro ao processar sua solicitação com a IA.", "details": str(e)}), 500