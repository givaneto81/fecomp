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
    "GERAL: Organize um cronograma semanal realista, que caiba na sua rotina sem sacrificar sua saúde.",
    "GERAL: Faça simulados completos no horário da prova; isso treina resistência mental.",
    "GERAL: Revise sempre seus erros; eles mostram exatamente onde você precisa ajustar.",
    "GERAL: Utilize métodos ativos, como ensinar o conteúdo em voz alta para si mesmo.",
    "GERAL: Estude em blocos curtos com pausas regulares para manter a concentração.",
    "GERAL: Varie entre teoria e prática na mesma sessão de estudo.",
    "GERAL: No começo do estudo de cada dia, revise rapidamente o que estudou no anterior.",
    "GERAL: Use marcadores de cor para diferenciar importância de tópicos.",
    "GERAL: Evite estudar por longos períodos sem descanso; isso compromete a retenção.",
    "GERAL: Priorize assuntos mais cobrados no ENEM e no SSA.",
    "GERAL: Mantenha sua mesa organizada para não perder tempo distraído.",
    "GERAL: Estude longe do celular, ou deixe-o em modo avião.",
    "GERAL: Utilize mapas mentais para resumir conteúdos extensos de forma visual.",
    "GERAL: Não acumule matéria atrasada; reorganize e retome com calma.",
    "GERAL: Faça autoavaliações semanais para acompanhar seu rendimento.",
    "GERAL: Procure estudar sempre no mesmo horário; cria ritmo e disciplina.",
    "GERAL: Evite estudar muitas coisas novas no mesmo dia; distribua corretamente.",
    "GERAL: Descanse bem; noites mal dormidas afetam desempenho cognitivo.",
    "GERAL: Comece o dia com a matéria que exige mais energia mental.",
    "GERAL: Identifique seu estilo de aprendizado e adapte suas técnicas.",
    "GERAL: Revise conteúdos complexos mais de uma vez na semana.",
    "GERAL: Use provas anteriores como guia do tipo de raciocínio exigido.",
    "GERAL: Estabeleça metas claras e possíveis para cada sessão de estudo.",
    "GERAL: Faça revisões de final de semana; elas consolidam o conteúdo.",
    "GERAL: Anote dúvidas enquanto estuda e esclareça-as no mesmo dia se possível.",
    "GERAL: Não deixe assuntos pequenos acumularem; eles também caem.",
    "GERAL: Mantenha hidratação adequada durante os estudos.",
    "GERAL: Intercale matérias exatas e humanas para não saturar.",
    "GERAL: Valorize a constância mais que o volume; estude sempre um pouco.",
    "GERAL: Evite depender apenas de videoaulas; pratique questões.",
    "GERAL: Tenha um caderno separado para fórmulas e resumos essenciais.",
    "GERAL: Faça exercícios sem olhar para a teoria primeiro para testar memória.",
    "GERAL: Relembre rapidamente assuntos antigos a cada novo bloco de estudo.",
    "GERAL: Registre seu progresso para manter a motivação.",
    "GERAL: Evite comparar seu ritmo com o dos outros; respeite seu processo.",
    "GERAL: Estude com propósito, lembrando por que você está nessa caminhada.",
    "GERAL: Reduza distrações e ambientes barulhentos.",
    "GERAL: Releia seus resumos semanalmente para manter o conhecimento ativo.",
    "GERAL: Ao finalizar um tema, tente explicá-lo sem consultar material.",
    "GERAL: Ajuste o cronograma quando perceber que algo não está funcionando.",

    "PORTUGUÊS: Revise regras de acentuação, pois aparecem frequentemente em questões objetivas.",
    "PORTUGUÊS: Estude crase com atenção, entendendo quando ela é obrigatória e quando não ocorre.",
    "PORTUGUÊS: Pratique interpretação de textos variados para desenvolver leitura crítica.",
    "PORTUGUÊS: Identifique tese e argumentos em textos dissertativos; isso cai muito.",
    "PORTUGUÊS: Revise figuras de linguagem com exemplos claros.",
    "PORTUGUÊS: Leia textos jornalísticos para ampliar vocabulário e repertório.",
    "PORTUGUÊS: Treine análise de tirinhas e charges, observando ironia e contexto.",
    "PORTUGUÊS: Relembre regência verbal e nominal, conteúdos recorrentes.",
    "PORTUGUÊS: Revise os tipos de sujeito e predicado.",
    "PORTUGUÊS: Estude concordância verbal com foco nos casos especiais.",
    "PORTUGUÊS: Analise textos publicitários para entender persuasão e intenção.",
    "PORTUGUÊS: Reforce semântica, principalmente sentidos figurados.",
    "PORTUGUÊS: Revise ortografia atualizada para evitar deslizes.",
    "PORTUGUÊS: Estude funções da linguagem com exemplos práticos.",
    "PORTUGUÊS: Pratique análise sintática regularmente para ganhar confiança.",
    "PORTUGUÊS: Observe conectivos e o que eles indicam na estrutura argumentativa.",
    "PORTUGUÊS: Analise gráficos e tabelas inseridos em textos para interpretação correta.",
    "PORTUGUÊS: Leia textos longos com calma antes de tentar agilizar a leitura.",
    "PORTUGUÊS: Revise formação de palavras e processos derivacionais.",
    "PORTUGUÊS: Estude denotação e conotação com exercícios aplicados.",
    "PORTUGUÊS: Relembre vozes verbais e suas transformações.",
    "PORTUGUÊS: Pratique identificação de recursos expressivos em poemas.",
    "PORTUGUÊS: Estude sequência textual conforme o gênero apresentado.",
    "PORTUGUÊS: Revise período composto por subordinação e coordenação.",
    "PORTUGUÊS: Observe como a pontuação altera sentido nas frases.",
    "PORTUGUÊS: Interprete textos opinativos analisando posicionamento do autor.",
    "PORTUGUÊS: Trabalhe leitura crítica avaliando intenção e público-alvo.",
    "PORTUGUÊS: Estude polissemia e ambiguidade com foco em interpretação.",
    "PORTUGUÊS: Treine reescrita de frases mantendo o sentido original.",
    "PORTUGUÊS: Revise coesão referencial e sequencial.",
    "PORTUGUÊS: Pratique questões do ENEM focadas apenas em interpretação.",
    "PORTUGUÊS: Leia títulos e subtítulos com atenção; eles guiam o entendimento.",
    "PORTUGUÊS: Estude adequação e variação linguística.",
    "PORTUGUÊS: Treine reconhecer marcas de oralidade em textos.",
    "PORTUGUÊS: Revise orações reduzidas e suas equivalências.",
    "PORTUGUÊS: Leia resumos de livros clássicos para ampliar repertório textual.",
    "PORTUGUÊS: Pratique reconhecer tópicos frasais e conclusão de parágrafos.",
    "PORTUGUÊS: Estude mecanismos de substituição lexical.",
    "PORTUGUÊS: Aprenda a identificar o objetivo comunicativo de cada texto.",
    "PORTUGUÊS: Resolva questões com foco em análise de intenção comunicativa.",

    "MATEMÁTICA: Relembre funções do 1º grau e seus gráficos.",
    "MATEMÁTICA: Estude funções quadráticas, principalmente vértice e concavidade.",
    "MATEMÁTICA: Treine resolução de sistemas lineares de 2x2 e 3x3.",
    "MATEMÁTICA: Revise problemas de porcentagem contextualizada.",
    "MATEMÁTICA: Pratique regra de três simples e composta em exercícios aplicados.",
    "MATEMÁTICA: Estude juros simples com foco em aplicações práticas.",
    "MATEMÁTICA: Revise juros compostos e montante em investimentos.",
    "MATEMÁTICA: Resolva exercícios de análise combinatória: arranjos, permutações, combinações.",
    "MATEMÁTICA: Estude probabilidade com cenários reais.",
    "MATEMÁTICA: Pratique interpretação de gráficos estatísticos.",
    "MATEMÁTICA: Revise média, mediana e moda com tabelas.",
    "MATEMÁTICA: Trabalhe estatística básica utilizando problemas do ENEM.",
    "MATEMÁTICA: Revise matrizes e operações fundamentais.",
    "MATEMÁTICA: Estude determinantes, especialmente de 2ª e 3ª ordem.",
    "MATEMÁTICA: Pratique frações e conversões entre representações.",
    "MATEMÁTICA: Revise potenciação e radiciação em contextos aplicados.",
    "MATEMÁTICA: Estude função exponencial e comportamento de crescimento.",
    "MATEMÁTICA: Revise função logarítmica com problemas típicos do ENEM.",
    "MATEMÁTICA: Trabalhe PA e PG, incluindo soma e termo geral.",
    "MATEMÁTICA: Estude geometria plana: ângulos, triângulos e quadriláteros.",
    "MATEMÁTICA: Pratique semelhança de triângulos e razões trigonométricas.",
    "MATEMÁTICA: Revise trigonometria no triângulo retângulo.",
    "MATEMÁTICA: Estude área de figuras planas, incluindo círculos.",
    "MATEMÁTICA: Trabalhe volume de prismas, cilindros e cones.",
    "MATEMÁTICA: Revise geometria espacial com desenhos auxiliares.",
    "MATEMÁTICA: Estude equações do 2º grau e relações de Bhaskara.",
    "MATEMÁTICA: Pratique inequações e representação gráfica.",
    "MATEMÁTICA: Revise proporcionalidade com aplicações práticas.",
    "MATEMÁTICA: Estude estatística descritiva com interpretação de dados.",
    "MATEMÁTICA: Trabalhe escala cartográfica e seus usos.",
    "MATEMÁTICA: Revise transformações geométricas básicas.",
    "MATEMÁTICA: Estude sistema monetário e cálculos financeiros simples.",
    "MATEMÁTICA: Pratique operações com números reais.",
    "MATEMÁTICA: Revise análise de variação percentual.",
    "MATEMÁTICA: Estude modelos matemáticos aplicados a situações reais.",
    "MATEMÁTICA: Treine problemas envolvendo razão e proporção.",
    "MATEMÁTICA: Revise progressões aritméticas em contextos de prova.",
    "MATEMÁTICA: Estude progressões geométricas com aplicações modernas.",
    "MATEMÁTICA: Pratique inequações exponenciais e logarítmicas.",
    "MATEMÁTICA: Revise gráficos de funções com mudança de parâmetros.",
    "MATEMÁTICA: Estude unidades de medida e conversões gerais",
    "MATEMÁTICA: Trabalhe aproximações e arredondamentos com cuidado.",
    "MATEMÁTICA: Pratique equações simultâneas aplicadas.",
    "MATEMÁTICA: Revise problemas envolvendo tempo, velocidade e distância.",
    "MATEMÁTICA: Resolva questões ENEM exclusivamente de gráficos e tabelas.",
    "MATEMÁTICA: Treine interpretação de função crescente e decrescente.",
    "MATEMÁTICA: Revise matrizes aplicadas a sistemas lineares.",
    "MATEMÁTICA: Trabalhe com problemas envolvendo otimização básica.",
    "MATEMÁTICA: Pratique estimativa e análise aproximada.",
    "MATEMÁTICA: Treine mistura de conceitos para fortalecer raciocínio.",

    "NATUREZA: Revise leis de Newton com exemplos do cotidiano.",
    "NATUREZA: Estude movimento uniforme e variações de velocidade.",
    "NATUREZA: Revise movimento uniformemente variado com gráficos.",
    "NATUREZA: Estude energia cinética e potencial.",
    "NATUREZA: Revise conservação de energia em sistemas simples.",
    "NATUREZA: Estude quantidade de movimento e colisões.",
    "NATUREZA: Revise circuitos elétricos básicos e cálculos simples.",
    "NATUREZA: Estude tensão, corrente e resistência no dia a dia.",
    "NATUREZA: Revise potências elétrica e mecânica.",
    "NATUREZA: Estude calor e temperatura com foco em processos térmicos.",
    "NATUREZA: Revise leis dos gases.",
    "NATUREZA: Estude ondas, frequência e período.",
    "NATUREZA: Revise óptica geométrica, incluindo espelhos.",
    "NATUREZA: Estude refração da luz e lentes.",
    "NATUREZA: Revise magnetismo e propriedades de ímãs.",
    "NATUREZA: Estude campo magnético e força magnética.",
    "NATUREZA: Revise eletrostática básica.",
    "NATUREZA: Estude pressão e hidrostática com exemplos práticos.",
    "NATUREZA: Revise empuxo e aplicações.",
    "NATUREZA: Estude termodinâmica e conceitos de entropia.",
    "NATUREZA: Revise estrutura atômica.",
    "NATUREZA: Estude ligações químicas e suas características.",
    "NATUREZA: Revise geometria molecular e polaridade.",
    "NATUREZA: Estude ácido-base e ph.",
    "NATUREZA: Revise termoquímica e entalpia.",
    "NATUREZA: Estude radioatividade e meia-vida.",
    "NATUREZA: Revise equilíbrio químico.",
    "NATUREZA: Estude eletroquímica e funcionamento de pilhas.",
    "NATUREZA: Revise concentração de soluções.",
    "NATUREZA: Estude estequiometria com atenção.",
    "NATUREZA: Revise funções orgânicas da química.",
    "NATUREZA: Estude cinética química.",
    "NATUREZA: Revise propriedades da água.",
    "NATUREZA: Estude DNA, RNA e síntese proteica.",
    "NATUREZA: Revise genética mendeliana e exercícios básicos.",
    "NATUREZA: Estude evolução e seleção natural.",
    "NATUREZA: Revise mitose e meiose comparando processos.",
    "NATUREZA: Estude sistemas do corpo humano por tópicos.",
    "NATUREZA: Revise imunologia básica.",
    "NATUREZA: Estude relações ecológicas.",
    "NATUREZA: Revise cadeias e teias alimentares.",
    "NATUREZA: Estude biomas brasileiros.",
    "NATUREZA: Revise ciclos biogeoquímicos.",
    "NATUREZA: Estude impactos ambientais.",
    "NATUREZA: Revise biotecnologia e engenharia genética.",
    "NATUREZA: Estude origem da vida com teorias principais.",
    "NATUREZA: Revise reprodução vegetal.",
    "NATUREZA: Estude fisiologia humana com foco no ENEM.",
    "NATUREZA: Revise doenças relacionadas à água e saneamento.",
    "NATUREZA: Estude funções orgânicas com exemplos do cotidiano.",
    "NATUREZA: Revise soluções químicas e tipos de mistura.",
    "NATUREZA: Estude forças intermoleculares.",
    "NATUREZA: Revise gráficos de eletricidade e cinemática.",
    "NATUREZA: Estude som e características das ondas sonoras.",
    "NATUREZA: Revise luz, cor e fenômenos ópticos.",
    "NATUREZA: Estude sistemas respiratório e circulatório.",
    "NATUREZA: Revise fundamentos da ecologia aplicada.",
    "NATUREZA: Estude radiação e seus efeitos ambientais.",
    "NATUREZA: Revise energia e suas formas de transformação.",

    "HUMANAS: Revise Antiguidade Oriental e Ocidental.",
    "HUMANAS: Estude Grécia e Roma com foco em política e cultura.",
    "HUMANAS: Revise Idade Média com atenção ao feudalismo.",
    "HUMANAS: Estude Renascimento e mudanças culturais.",
    "HUMANAS: Revise Reforma e Contrarreforma.",
    "HUMANAS: Estude Iluminismo e seus principais pensadores.",
    "HUMANAS: Revise Revolução Francesa.",
    "HUMANAS: Estude Independência da América Latina.",
    "HUMANAS: Revise Brasil Colônia e ciclos econômicos.",
    "HUMANAS: Estude movimentos nativistas brasileiros.",
    "HUMANAS: Revise período Joanino e Independência.",
    "HUMANAS: Estude Primeiro e Segundo Reinado.",
    "HUMANAS: Revise República Velha.",
    "HUMANAS: Estude Era Vargas.",
    "HUMANAS: Revise Ditadura Militar brasileira.",
    "HUMANAS: Estude redemocratização.",
    "HUMANAS: Revise Primeira e Segunda Guerra Mundial.",
    "HUMANAS: Estude Guerra Fria.",
    "HUMANAS: Revise conflitos contemporâneos.",
    "HUMANAS: Estude geopolítica atual.",
    "HUMANAS: Revise urbanização e seus impactos.",
    "HUMANAS: Estude industrialização do Brasil.",
    "HUMANAS: Revise demografia e pirâmides etárias.",
    "HUMANAS: Estude agropecuária e produção no Brasil.",
    "HUMANAS: Revise globalização e fluxos econômicos.",
    "HUMANAS: Estude blocos econômicos.",
    "HUMANAS: Revise clima e tipos climáticos.",
    "HUMANAS: Estude vegetação e biomas.",
    "HUMANAS: Revise impactos ambientais humanos.",
    "HUMANAS: Estude economia sustentável.",
    "HUMANAS: Revise cartografia e leitura de mapas.",
    "HUMANAS: Estude migrações e dinâmicas populacionais.",
    "HUMANAS: Revise teoria dos sistemas produtivos.",
    "HUMANAS: Estude movimentos sociais brasileiros.",
    "HUMANAS: Revise cultura e identidade brasileira.",
    "HUMANAS: Estude patrimônio histórico.",
    "HUMANAS: Revise filosofia antiga.",
    "HUMANAS: Estude filosofia moderna.",
    "HUMANAS: Revise ética e moral.",
    "HUMANAS: Estude teorias do conhecimento.",
    "HUMANAS: Revise filosofia política.",
    "HUMANAS: Estude cidadania e direitos humanos.",
    "HUMANAS: Revise sociologia clássica: Durkheim, Weber, Marx.",
    "HUMANAS: Estude sociedade e trabalho.",
    "HUMANAS: Revise cultura e ideologia.",
    "HUMANAS: Estude estratificação social.",
    "HUMANAS: Revise mídia e comunicação.",
    "HUMANAS: Estude Estado e poder.",
    "HUMANAS: Revise movimentos urbanos.",
    "HUMANAS: Estude desigualdade social.",
    "HUMANAS: Revise relações de trabalho contemporâneas.",
    "HUMANAS: Estude tecnologia e transformação social.",
    "HUMANAS: Revise globalização cultural.",
    "HUMANAS: Estude conflitos étnicos e suas causas.",
    "HUMANAS: Revise geopolítica do Oriente Médio.",
    "HUMANAS: Estude ONU e organismos internacionais.",
    "HUMANAS: Revise guerras, tensões e acordos recentes."
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