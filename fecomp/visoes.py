import os
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, send_from_directory, current_app
from werkzeug.utils import secure_filename
from werkzeug.security import check_password_hash, generate_password_hash
from functools import wraps

# --- MODELS ATUALIZADOS ---
from .models import User, Subject, Folder, File, Task, Submission, Announcement, Course
from .extensions import db
from .forms import EmptyForm

views_bp = Blueprint('visoes', __name__)

# --- DECORATORS DE AUTENTICAÇÃO E FUNÇÃO (NÍVEL 1 & 2) ---

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Por favor, faça login para acessar esta página.', 'error')
            return redirect(url_for('autenticacao.pagina_login'))
        return f(*args, **kwargs)
    return decorated_function

# NOVO DECORATOR (NÍVEL 2.3) - JÁ CORRIGIDO
def role_required(roles_list):
    """ Exige que o usuário tenha uma das funções na lista (ex: ['admin', 'professor']) """
    def role_decorator(f): # Renomeado para evitar conflito
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                flash('Por favor, faça login para acessar esta página.', 'error')
                return redirect(url_for('autenticacao.pagina_login'))
            
            if session.get('user_role') not in roles_list:
                flash('Você não tem permissão para acessar esta página.', 'error')
                return redirect(url_for('visoes.pagina_inicio'))
            return f(*args, **kwargs)
        return decorated_function
    return role_decorator # Retorna a função renomeada


# --- ROTAS PRINCIPAIS (GET) ---

# NÍVEL 4.2: ROTA 'pagina_inicio' ATUALIZADA (HUB DINÂMICO + REDIRECIONAMENTO ADMIN)
@views_bp.route('/inicio')
@login_required
def pagina_inicio():
    user_id = session['user_id']
    user_role = session.get('user_role', 'aluno') 
    user = User.query.get(user_id)
    
    # --- ALTERAÇÃO AQUI (OPÇÃO 1) ---
    # Se for admin, redireciona DIRETAMENTE para o painel de admin
    if user_role == 'admin':
        return redirect(url_for('admin_bp.index')) # Redireciona para /admin/
    # --- FIM DA ALTERAÇÃO ---

    # Dashboard do Aluno
    if user_role == 'aluno':
        user_courses = user.courses.all()
        course_ids = [c.id for c in user_courses]
        
        announcements = Announcement.query.filter(Announcement.course_id.in_(course_ids)) \
                                        .order_by(Announcement.timestamp.desc()).limit(5).all()
        
        submitted_task_ids = [sub.task_id for sub in Submission.query.filter_by(student_id=user_id)]
        
        pending_tasks = Task.query.filter(
            Task.course_id.in_(course_ids),
            ~Task.id.in_(submitted_task_ids)
        ).order_by(Task.due_date.asc()).all()

        # Renderiza 'inicio.html' com dados do aluno
        return render_template('inicio.html', 
                             announcements=announcements, 
                             pending_tasks=pending_tasks)
    
    # Dashboard do Professor (Agora só 'professor' chega aqui)
    else: 
        courses = user.courses.all() 
        # Renderiza 'inicio.html' com dados do professor (template precisa ser adaptado ou criar um novo)
        return render_template('inicio.html', courses=courses)

# NÍVEL 2.2: ROTA 'pagina_materias' ATUALIZADA (HÍBRIDA)
@views_bp.route('/materias')
@login_required
def pagina_materias():
    form = EmptyForm()
    user_id = session['user_id']
    user = User.query.get(user_id)

    personal_subjects = Subject.query.filter_by(user_id=user.id).order_by(Subject.name).all()

    user_course_ids = [c.id for c in user.courses]
    course_subjects = Subject.query.filter(Subject.course_id.in_(user_course_ids)) \
                                .order_by(Subject.course_id, Subject.name).all()
    
    subjects_by_course = {}
    for subject in course_subjects:
        course_name = subject.course.name if subject.course else "Turma Desconhecida"
        if course_name not in subjects_by_course:
            subjects_by_course[course_name] = []
        subjects_by_course[course_name].append(subject)

    return render_template('home.html', 
                           subjects=personal_subjects, 
                           personal_subjects=personal_subjects, 
                           subjects_by_course=subjects_by_course, 
                           form=form, 
                           delete_form=form)

# Rota 'pastas_page' (com verificação de permissão Nível 2)
@views_bp.route('/pastas/<int:subject_id>')
@login_required
def pastas_page(subject_id):
    form = EmptyForm()
    subject = Subject.query.get_or_404(subject_id)
    user = User.query.get(session['user_id'])

    is_personal = (subject.user_id == user.id)
    is_member = False
    if subject.course_id:
        is_member = user.courses.filter_by(id=subject.course_id).first() is not None
    
    is_privileged = False
    if user.role in ['admin', 'professor'] and is_member:
        is_privileged = True
    if user.role == 'admin' and subject.course and subject.course.admin_id == user.id:
        is_privileged = True

    if not is_personal and not is_member and not is_privileged:
        flash('Você não tem permissão para ver esta matéria.', 'error')
        return redirect(url_for('visoes.pagina_materias'))

    folders = Folder.query.filter_by(subject_id=subject.id).order_by(Folder.name).all()
    can_edit = is_personal or is_privileged

    return render_template('pastas.html', 
                           subject=subject, 
                           folders=folders, 
                           form=form,
                           can_edit=can_edit) 

# Rota 'folders' (com verificação de permissão Nível 2)
@views_bp.route('/pasta/<int:folder_id>')
@login_required
def folders(folder_id):
    form = EmptyForm()
    folder = Folder.query.get_or_404(folder_id)
    subject = folder.subject
    user = User.query.get(session['user_id'])

    is_personal = (subject.user_id == user.id)
    is_member = False
    if subject.course_id:
        is_member = user.courses.filter_by(id=subject.course_id).first() is not None
    
    is_privileged = False
    if user.role in ['admin', 'professor'] and is_member:
        is_privileged = True
    if user.role == 'admin' and subject.course and subject.course.admin_id == user.id:
        is_privileged = True

    if not is_personal and not is_member and not is_privileged:
        flash('Você não tem permissão para ver esta pasta.', 'error')
        return redirect(url_for('visoes.pagina_materias'))

    files = File.query.filter_by(folder_id=folder.id).order_by(File.original_filename).all()
    can_edit = is_personal or is_privileged
    
    return render_template('folders.html', 
                           folder=folder, 
                           files=files, 
                           form=form,
                           can_edit=can_edit) 

@views_bp.route('/chat')
@login_required
def pagina_chat():
    return render_template('chat.html')

@views_bp.route('/perfil')
@login_required
def pagina_perfil():
    form = EmptyForm()
    user = User.query.get(session['user_id'])
    return render_template('perfil.html', user=user, form=form)

# --- NÍVEL 3: NOVAS ROTAS DE TAREFAS (ALUNO) ---

@views_bp.route('/tasks') # URL para acessar a página de tarefas
@login_required
@role_required(['aluno']) # Apenas alunos
def tasks(): # Nome da função
    user = User.query.get(session['user_id'])
    user_course_ids = [c.id for c in user.courses]
    
    all_tasks = Task.query.filter(Task.course_id.in_(user_course_ids)) \
                        .order_by(Task.due_date.asc()).all()

    submitted_task_ids = [sub.task_id for sub in Submission.query.filter_by(student_id=user.id)]

    pending_tasks = [task for task in all_tasks if task.id not in submitted_task_ids]
    completed_tasks = [task for task in all_tasks if task.id in submitted_task_ids]
    
    form = EmptyForm() 

    return render_template('tasks.html', # Nome do template
                         pending_tasks=pending_tasks, 
                         completed_tasks=completed_tasks,
                         form=form)

@views_bp.route('/task/<int:task_id>/submit', methods=['POST'])
@login_required
@role_required(['aluno'])
def submit_task(task_id):
    form = EmptyForm()
    task = Task.query.get_or_404(task_id)
    user = User.query.get(session['user_id'])
    
    if task.course not in user.courses:
         flash('Você não pertence à turma desta tarefa.', 'error')
         return redirect(url_for('visoes.tasks')) # Redireciona de volta para /tasks

    existing_submission = Submission.query.filter_by(task_id=task.id, student_id=user.id).first()
    if existing_submission:
        flash('Você já enviou esta tarefa.', 'error')
        return redirect(url_for('visoes.tasks')) # Redireciona de volta para /tasks

    if 'file' not in request.files or request.files['file'].filename == '':
        flash('Nenhum arquivo selecionado.', 'error')
        return redirect(url_for('visoes.tasks')) # Redireciona de volta para /tasks
        
    file = request.files['file']
    if file:
        subject_id = task.subject_id
        if not subject_id: 
            generic_subject = Subject.query.filter_by(course_id=task.course_id, name="Entregas Gerais").first()
            if not generic_subject:
                generic_subject = Subject(name="Entregas Gerais", course_id=task.course_id)
                db.session.add(generic_subject)
                db.session.commit()
            subject_id = generic_subject.id

        folder_name = f"Entrega - {user.name}"
        submission_folder = Folder.query.filter_by(subject_id=subject_id, name=folder_name).first()
        if not submission_folder:
            submission_folder = Folder(name=folder_name, subject_id=subject_id)
            db.session.add(submission_folder)
            db.session.commit()
        
        original_filename = secure_filename(file.filename)
        filename = f"user_{user.id}_task_{task.id}_{original_filename}"
        upload_folder_path = current_app.config['UPLOAD_FOLDER']
        os.makedirs(upload_folder_path, exist_ok=True)
        
        file.save(os.path.join(upload_folder_path, filename))
        
        new_file = File(filename=filename, 
                        original_filename=original_filename, 
                        folder_id=submission_folder.id)
        db.session.add(new_file)
        db.session.commit()
        
        new_submission = Submission(task_id=task.id, 
                                    student_id=user.id, 
                                    file_id=new_file.id)
        db.session.add(new_submission)
        db.session.commit()
        
        flash('Tarefa enviada com sucesso!', 'success')

    return redirect(url_for('visoes.tasks')) # Redireciona de volta para /tasks

# --- ROTAS POST (PROCESSAR FORMULÁRIOS) ---

@views_bp.route('/add_folder/<int:subject_id>', methods=['POST'])
@login_required
def add_folder(subject_id):
    form = EmptyForm()
    subject = Subject.query.get_or_404(subject_id)
    user = User.query.get(session['user_id'])
    
    is_personal = (subject.user_id == user.id)
    is_privileged = False
    if subject.course_id and user.role in ['admin', 'professor']:
         if (user.courses.filter_by(id=subject.course_id).first() or 
            (user.role == 'admin' and subject.course.admin_id == user.id)):
            is_privileged = True
    
    if not is_personal and not is_privileged:
        flash('Você não tem permissão para adicionar pastas aqui.', 'error')
        return redirect(url_for('visoes.pastas_page', subject_id=subject_id))
    
    if form.validate_on_submit():
        folder_name = request.form.get('folder_name')
        if folder_name:
            new_folder = Folder(name=folder_name, subject_id=subject.id)
            db.session.add(new_folder)
            db.session.commit()
            flash('Pasta criada com sucesso!', 'success')
        else:
            flash('O nome da pasta não pode estar vazio.', 'error')
    return redirect(url_for('visoes.pastas_page', subject_id=subject_id))

@views_bp.route('/upload_file/<int:folder_id>', methods=['POST'])
@login_required
def upload_file(folder_id):
    form = EmptyForm()
    folder = Folder.query.get_or_404(folder_id)
    subject = folder.subject
    user = User.query.get(session['user_id'])

    is_personal = (subject.user_id == user.id)
    is_privileged = False
    if subject.course_id and user.role in ['admin', 'professor']:
         if (user.courses.filter_by(id=subject.course_id).first() or 
            (user.role == 'admin' and subject.course.admin_id == user.id)):
            is_privileged = True
    
    if not is_personal and not is_privileged:
        flash('Você não tem permissão para enviar arquivos para esta pasta.', 'error')
        return redirect(url_for('visoes.folders', folder_id=folder_id))

    if form.validate_on_submit():
        if 'file' not in request.files or request.files['file'].filename == '':
            flash('Nenhum arquivo selecionado.', 'error')
            return redirect(url_for('visoes.folders', folder_id=folder_id))
        
        file = request.files['file']
        if file:
            original_filename = secure_filename(file.filename)
            filename = f"user_{session['user_id']}_folder_{folder_id}_{original_filename}"
            upload_folder = current_app.config['UPLOAD_FOLDER']
            os.makedirs(upload_folder, exist_ok=True)
            file.save(os.path.join(upload_folder, filename))
            
            new_file = File(filename=filename, original_filename=original_filename, folder_id=folder_id)
            db.session.add(new_file)
            db.session.commit()
            flash('Arquivo enviado com sucesso!', 'success')
    return redirect(url_for('visoes.folders', folder_id=folder_id))

@views_bp.route('/update_subject_color/<int:subject_id>', methods=['POST'])
@login_required
def update_subject_color(subject_id):
    form = EmptyForm()
    if form.validate_on_submit():
        subject = Subject.query.filter_by(id=subject_id, user_id=session['user_id']).first()
        if not subject:
             flash('Ação não permitida.', 'error')
             return redirect(url_for('visoes.pagina_materias'))
             
        new_color = request.form.get('new_color')
        if new_color and len(new_color) == 7 and new_color.startswith('#'):
            subject.color = new_color
            db.session.commit()
            flash('Cor da matéria atualizada!', 'success')
        else:
            flash('Formato de cor inválido.', 'error')
    return redirect(url_for('visoes.pagina_materias'))

@views_bp.route('/delete_subject/<int:subject_id>', methods=['POST'])
@login_required
def delete_subject(subject_id):
    form = EmptyForm()
    if form.validate_on_submit():
        subject = Subject.query.filter_by(id=subject_id, user_id=session['user_id']).first()
        if not subject:
             flash('Ação não permitida.', 'error')
             return redirect(url_for('visoes.pagina_materias'))
             
        db.session.delete(subject)
        db.session.commit()
        flash('Matéria, pastas e arquivos foram excluídos.', 'success')
    return redirect(url_for('visoes.pagina_materias'))

# --- ROTAS DO PERFIL ---

@views_bp.route('/update_profile', methods=['POST'])
@login_required
def update_profile():
    form = EmptyForm()
    if form.validate_on_submit():
        user = User.query.get(session['user_id'])
        new_name = request.form.get('new_name')
        if new_name:
            user.name = new_name
            session['user_name'] = new_name
            db.session.commit()
            flash('Nome atualizado com sucesso!', 'success')
        else:
            flash('O nome não pode ficar em branco.', 'error')
    return redirect(url_for('visoes.pagina_perfil'))

@views_bp.route('/change_password', methods=['POST'])
@login_required
def change_password():
    form = EmptyForm()
    if form.validate_on_submit():
        user = User.query.get(session['user_id'])
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        if not user or not check_password_hash(user.password_hash, current_password):
            flash('A senha atual está incorreta.', 'error')
        elif not new_password:
            flash('A nova senha não pode estar em branco.', 'error')
        else:
            user.password_hash = generate_password_hash(new_password)
            db.session.commit()
            flash('Senha alterada com sucesso!', 'success')
    return redirect(url_for('visoes.pagina_perfil'))

@views_bp.route('/delete_account', methods=['POST'])
@login_required
def delete_account():
    form = EmptyForm()
    if form.validate_on_submit():
        try:
            user = User.query.get(session['user_id'])
            if user.role == 'admin':
                flash('Contas de administrador não podem ser excluídas por esta rota.', 'error')
                return redirect(url_for('visoes.pagina_perfil'))
                
            db.session.delete(user)
            db.session.commit()
            session.clear()
            flash('Sua conta foi excluída com sucesso.', 'success')
            return redirect(url_for('autenticacao.pagina_login'))
        except Exception as e:
            db.session.rollback()
            flash('Não foi possível excluir a conta.', 'error')
    return redirect(url_for('visoes.pagina_perfil'))

# --- ROTA PARA SERVIR ARQUIVOS ---
@views_bp.route('/uploads/<path:filename>')
@login_required
def uploaded_file(filename):
    
    file_db = File.query.filter_by(filename=filename).first()
    user = User.query.get(session['user_id'])
    
    if not file_db:
        flash('Arquivo não encontrado.', 'error')
        return redirect(request.referrer or url_for('visoes.pagina_inicio'))

    subject = file_db.folder.subject

    is_personal = (subject.user_id == user.id)
    is_member = False
    if subject.course_id:
        is_member = user.courses.filter_by(id=subject.course_id).first() is not None
    
    is_privileged = False
    if user.role in ['admin', 'professor'] and is_member:
        is_privileged = True
    if user.role == 'admin' and subject.course and subject.course.admin_id == user.id:
        is_privileged = True

    is_submission_relation = hasattr(file_db, 'submission') and file_db.submission
    can_view_submission = False
    if is_submission_relation:
        # Acessa a submission associada ao file
        submission_instance = file_db.submission 
        if submission_instance and submission_instance.student_id == user.id: # É o próprio aluno
             can_view_submission = True
        if is_privileged: # É o professor/admin da turma
             can_view_submission = True


    if not is_personal and not is_member and not is_privileged and not can_view_submission:
        flash('Você não tem permissão para ver este arquivo.', 'error')
        return redirect(request.referrer or url_for('visoes.pagina_inicio'))
    
    # Constrói o caminho absoluto para a pasta de uploads
    # Assume que a pasta 'uploads' está dentro da pasta 'fecomp'
    upload_folder_abs = os.path.join(current_app.root_path, current_app.config['UPLOAD_FOLDER'].split('/')[-1])
    
    # Verifica se o caminho está correto (para debug)
    # print(f"Tentando servir de: {upload_folder_abs}")
    # print(f"Arquivo: {filename}")
    
    try:
        return send_from_directory(upload_folder_abs, filename)
    except FileNotFoundError:
         flash('Erro interno: Arquivo não encontrado no servidor.', 'error')
         # Tenta reconstruir o caminho relativo se falhar (menos ideal)
         upload_folder_rel = os.path.join('..', current_app.config['UPLOAD_FOLDER'])
         try:
             # print(f"Tentando servir de (relativo): {upload_folder_rel}")
             return send_from_directory(upload_folder_rel, filename, as_attachment=False) # Tenta forçar a visualização
         except Exception as e:
            # print(f"Erro final ao servir arquivo: {e}")
            return redirect(request.referrer or url_for('visoes.pagina_inicio'))