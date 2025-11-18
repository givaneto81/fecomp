import os
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, send_from_directory, current_app
from werkzeug.utils import secure_filename
from werkzeug.security import check_password_hash, generate_password_hash
from functools import wraps

# --- models atualizados ---
from .models import User, Subject, Folder, File, Task, Submission, Announcement, Course
# --- csrf ACRESCENTADO AQUI ---
from .extensions import db, csrf
from .forms import EmptyForm

views_bp = Blueprint('visoes', __name__)

# --- CONSTANTES PARA UPLOAD DE AVATAR (NOVO) ---
# A gente salva em /static/avatars/
AVATAR_UPLOAD_FOLDER = 'static/avatars'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
# --- FIM DAS CONSTANTES ---


# --- decorators de autenticação e função (nível 1 & 2) ---

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Por favor, faça login para acessar esta página.', 'error')
            return redirect(url_for('autenticacao.pagina_login'))
        return f(*args, **kwargs)
    return decorated_function

# novo decorator (nível 2.3) - já corrigido
def role_required(roles_list):
    """ exige que o usuário tenha uma das funções na lista (ex: ['admin', 'professor']) """
    def role_decorator(f): # renomeado para evitar conflito
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
    return role_decorator # retorna a função renomeada


# --- NOVA FUNÇÃO DE VERIFICAÇÃO DE PERMISSÃO ---
def check_permission(subject):
    """Verifica se o usuário atual tem permissão de edição (pessoal ou privilegiada) para uma matéria."""
    user = User.query.get(session['user_id'])
    
    is_personal = (subject.user_id == user.id)
    is_privileged = False
    
    if subject.course_id:
        is_member = user.courses.filter_by(id=subject.course_id).first() is not None
        if user.role in ['admin', 'professor'] and is_member:
            is_privileged = True
        if user.role == 'admin' and subject.course and subject.course.admin_id == user.id:
            is_privileged = True
            
    return is_personal or is_privileged

# --- rotas principais (get) ---

# nível 4.2: rota 'pagina_inicio' atualizada (hub dinâmico + redirecionamento admin)
@views_bp.route('/inicio')
@login_required
def pagina_inicio():
    user_id = session['user_id']
    user_role = session.get('user_role', 'aluno')
    user = User.query.get(user_id)
    
    if user_role == 'admin':
        return redirect(url_for('admin_bp.index')) 

    user_courses = user.courses.all() # type: ignore
    course_ids = [c.id for c in user_courses]
    
    announcements = Announcement.query.filter(Announcement.course_id.in_(course_ids)) \
                                    .order_by(Announcement.timestamp.desc()).limit(5).all()
    
    has_courses_check = bool(user_courses)
    
    # --- MODIFICAÇÃO (PROPOSTA 3) ---
    # Busca matérias destacadas (apenas de cursos, já que pessoais não são para todos)
    featured_subjects = Subject.query.filter(
        Subject.is_featured == True,
        Subject.course_id.isnot(None)
    ).all()
    # --- FIM DA MODIFICAÇÃO ---

    if user_role == 'aluno':
        submitted_task_ids = [sub.task_id for sub in Submission.query.filter_by(student_id=user_id).all()]
        
        pending_tasks = Task.query.filter(
            Task.course_id.in_(course_ids),
            ~Task.id.in_(submitted_task_ids)
        ).order_by(Task.due_date.asc()).all()

        return render_template('inicio.html', 
                             announcements=announcements, 
                             pending_tasks=pending_tasks,
                             has_courses=has_courses_check,
                             featured_subjects=featured_subjects) # Passa para o template
    
    else: 
        return render_template('inicio.html', 
                             announcements=announcements,
                             pending_tasks=None,
                             has_courses=has_courses_check,
                             featured_subjects=featured_subjects) # Passa para o template

# nível 2.2: rota 'pagina_materias'
@views_bp.route('/materias') # type: ignore
@login_required
def pagina_materias():
    form = EmptyForm()
    user_id = session['user_id']
    user = User.query.get(user_id)

    personal_subjects = Subject.query.filter_by(user_id=user.id).order_by(Subject.name).all()
 # type: ignore
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
                           subjects=personal_subjects, # type: ignore
                           personal_subjects=personal_subjects, 
                           subjects_by_course=subjects_by_course, 
                           form=form, 
                           delete_form=form)

# rota 'pastas_page' (com verificação de permissão nível 2)
@views_bp.route('/pastas/<int:subject_id>')
@login_required
def pastas_page(subject_id):
    form = EmptyForm()
    subject = Subject.query.get_or_404(subject_id)
    
    can_edit = check_permission(subject)

    if not can_edit:
        user = User.query.get(session['user_id'])
        is_member = False
        if subject.course_id: # type: ignore
            is_member = user.courses.filter_by(id=subject.course_id).first() is not None
        if not is_member:
            flash('Você não tem permissão para ver esta matéria.', 'error')
            return redirect(url_for('visoes.pagina_materias'))

    folders = Folder.query.filter_by(subject_id=subject.id).order_by(Folder.name).all()

    return render_template('pastas.html', 
                           subject=subject, 
                           folders=folders, 
                           form=form,
                           can_edit=can_edit) 

# rota 'folders' (com verificação de permissão nível 2)
@views_bp.route('/pasta/<int:folder_id>')
@login_required
def folders(folder_id):
    form = EmptyForm()
    folder = Folder.query.get_or_404(folder_id)
    subject = folder.subject
    
    can_edit = check_permission(subject)
    
    if not can_edit:
        user = User.query.get(session['user_id'])
        is_member = False
        if subject.course_id: # type: ignore
            is_member = user.courses.filter_by(id=subject.course_id).first() is not None
        if not is_member:
            flash('Você não tem permissão para ver esta pasta.', 'error')
            return redirect(url_for('visoes.pagina_materias'))

    # --- INÍCIO DA MODIFICAÇÃO (VISUALIZAÇÃO DE ARQUIVO) ---
    files_data = []
    files_from_db = File.query.filter_by(folder_id=folder.id).order_by(File.original_filename).all()
    
    for file in files_from_db:
        ext = file.original_filename.split('.')[-1].lower()
        icon = 'file' # Padrão
        file_type = 'other'
        
        if ext in ['png', 'jpg', 'jpeg', 'gif', 'bmp', 'svg']:
            icon = 'image'
            file_type = 'image'
        elif ext == 'pdf':
            icon = 'file-text'
            file_type = 'pdf'
        elif ext in ['doc', 'docx']:
            icon = 'file-text'
            file_type = 'word'
        elif ext in ['txt', 'md']:
            icon = 'file-text'
            file_type = 'text'
        
        files_data.append({
            'id': file.id,
            'filename': file.filename,
            'original_filename': file.original_filename,
            'icon': icon,
            'file_type': file_type,
            'url': url_for('visoes.uploaded_file', filename=file.filename)
        })
   
    return render_template('folders.html', 
                           folder=folder, 
                           files=files_data, # Passa a nova lista
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

# --- nível 3: novas rotas de tarefas (aluno) ---

@views_bp.route('/tasks') # url para acessar a página de tarefas
@login_required
@role_required(['aluno']) # apenas alunos
def tasks(): # nome da função
    user = User.query.get(session['user_id'])
    user_course_ids = [c.id for c in user.courses]
    
    # Busca todas as tarefas dos cursos do aluno
    all_tasks = Task.query.filter(Task.course_id.in_(user_course_ids)) \
                        .order_by(Task.due_date.asc()).all()
    
    # Busca todas as submissões deste aluno
    submissions = Submission.query.filter_by(student_id=user.id).all()
    
    # Cria um mapa de submissões para consulta rápida
    submission_map = {sub.task_id: sub for sub in submissions}

    # Separa as listas
    pending_tasks = [task for task in all_tasks if task.id not in submission_map]
    
    # Passa as submissões (que contêm as tarefas e as notas)
    completed_submissions = [submission_map[task.id] for task in all_tasks if task.id in submission_map]
    
    form = EmptyForm() 

    return render_template('tasks.html', # nome do template
                         pending_tasks=pending_tasks, 
                         completed_submissions=completed_submissions,
                         form=form)

@views_bp.route('/task/<int:task_id>/submit', methods=['POST'])
@login_required
@role_required(['aluno'])
def submit_task(task_id):
    form = EmptyForm()
    task = Task.query.get_or_404(task_id)
    user = User.query.get(session['user_id'])
    
    if task.course not in user.courses: # type: ignore
         flash('Você não pertence à turma desta tarefa.', 'error')
         return redirect(url_for('visoes.tasks')) # redireciona de volta para /tasks

    existing_submission = Submission.query.filter_by(task_id=task.id, student_id=user.id).first()
    if existing_submission:
        flash('Você já enviou esta tarefa.', 'error')
        return redirect(url_for('visoes.tasks')) # redireciona de volta para /tasks

    if 'file' not in request.files or request.files['file'].filename == '':
        flash('Nenhum arquivo selecionado.', 'error')
        return redirect(url_for('visoes.tasks')) # redireciona de volta para /tasks
        
    file = request.files['file']
    if file:
        subject_id = task.subject_id
        if not subject_id: # type: ignore
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

    return redirect(url_for('visoes.tasks')) # redireciona de volta para /tasks

# --- rotas post (processar formulários) ---

@views_bp.route('/add_folder/<int:subject_id>', methods=['POST'])
@login_required
def add_folder(subject_id):
    form = EmptyForm()
    subject = Subject.query.get_or_404(subject_id)
    
    if not check_permission(subject):
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

    if not check_permission(subject):
        flash('Você não tem permissão para enviar arquivos para esta pasta.', 'error')
        return redirect(url_for('visoes.folders', folder_id=folder_id))

    if form.validate_on_submit():
        # --- MUDANÇA (SUPORTE A MÚLTIPLOS ARQUIVOS) ---
        files = request.files.getlist('file') # Pega a lista de arquivos
        
        if not files or files[0].filename == '':
            flash('Nenhum arquivo selecionado.', 'error')
            return redirect(url_for('visoes.folders', folder_id=folder_id))
        
        files_uploaded_count = 0
        for file in files:
            if file:
                original_filename = secure_filename(file.filename)
                # Garante um nome único
                filename = f"user_{session['user_id']}_folder_{folder_id}_{original_filename}"
                upload_folder = current_app.config['UPLOAD_FOLDER']
                os.makedirs(upload_folder, exist_ok=True)
                file.save(os.path.join(upload_folder, filename))
                
                new_file = File(filename=filename, original_filename=original_filename, folder_id=folder_id)
                db.session.add(new_file)
                files_uploaded_count += 1
        
        # Salva tudo no banco de uma vez
        db.session.commit()
        
        # --- MODIFICAÇÃO (PROPOSTA 2) - Anúncio automático ---
        if files_uploaded_count > 0:
            try:
                user_role = session.get('user_role')
                if subject.course_id and user_role in ['admin', 'professor']:
                    user = User.query.get(session['user_id'])
                    
                    if files_uploaded_count == 1:
                        anuncio_content = f"O professor {user.name} adicionou o ficheiro '{files[0].filename}' à matéria '{subject.name}'."
                    else:
                        anuncio_content = f"O professor {user.name} adicionou {files_uploaded_count} novos ficheiros à matéria '{subject.name}'."

                    new_announcement = Announcement(
                        content=anuncio_content,
                        course_id=subject.course_id,
                        professor_id=session['user_id']
                    )
                    db.session.add(new_announcement)
                    db.session.commit()
            except Exception as e:
                print(f"Erro ao criar anúncio automático: {e}")
                db.session.rollback()

            flash(f'{files_uploaded_count} arquivo(s) enviado(s) com sucesso!', 'success')
            
    return redirect(url_for('visoes.folders', folder_id=folder_id))

@views_bp.route('/update_subject_color/<int:subject_id>', methods=['POST'])
@login_required
def update_subject_color(subject_id):
    form = EmptyForm()
    if form.validate_on_submit():
        subject = Subject.query.filter_by(id=subject_id, user_id=session['user_id']).first() # type: ignore
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
        subject = Subject.query.filter_by(id=subject_id, user_id=session['user_id']).first() # type: ignore
        if not subject:
             flash('Ação não permitida.', 'error')
             return redirect(url_for('visoes.pagina_materias'))
             
        db.session.delete(subject)
        db.session.commit()
        flash('Matéria, pastas e arquivos foram excluídos.', 'success')
    return redirect(url_for('visoes.pagina_materias'))

# --- rotas do perfil ---

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

# --- rota para servir arquivos ---
@views_bp.route('/uploads/<path:filename>')
@login_required
def uploaded_file(filename):
    
    file_db = File.query.filter_by(filename=filename).first()
    user = User.query.get(session['user_id'])
 # type: ignore
    if not file_db:
        flash('Arquivo não encontrado.', 'error')
        return redirect(request.referrer or url_for('visoes.pagina_inicio'))

    subject = file_db.folder.subject

    can_view = check_permission(subject)
    
    is_submission_relation = hasattr(file_db, 'submission') and file_db.submission
    can_view_submission = False
    if is_submission_relation:
        submission_instance = file_db.submission 
        if submission_instance and submission_instance.student_id == user.id: 
             can_view_submission = True
        if can_view: # Se for admin/professor da turma
             can_view_submission = True

    if not can_view and not can_view_submission:
        user = User.query.get(session['user_id'])
        is_member = False
        if subject.course_id:
            is_member = user.courses.filter_by(id=subject.course_id).first() is not None
        if not is_member:
            flash('Você não tem permissão para ver este arquivo.', 'error')
            return redirect(request.referrer or url_for('visoes.pagina_inicio'))
    
    upload_folder_abs = os.path.join(current_app.root_path, current_app.config['UPLOAD_FOLDER'].split('/')[-1])
    
    try:
        return send_from_directory(upload_folder_abs, filename)
    except FileNotFoundError:
         flash('Erro interno: Arquivo não encontrado no servidor.', 'error')
         upload_folder_rel = os.path.join('..', current_app.config['UPLOAD_FOLDER'])
         try:
             return send_from_directory(upload_folder_rel, filename, as_attachment=False) 
         except Exception as e:
            return redirect(request.referrer or url_for('visoes.pagina_inicio'))        

# --- NOVAS ROTAS PARA GERIR PASTAS E FICHEIROS ---

@views_bp.route('/rename_folder/<int:folder_id>', methods=['POST'])
@login_required
def rename_folder(folder_id):
    form = EmptyForm()
    folder = Folder.query.get_or_404(folder_id)
    subject = folder.subject
    
    if not check_permission(subject):
        flash('Você não tem permissão para editar esta pasta.', 'error')
        return redirect(url_for('visoes.pastas_page', subject_id=subject.id))
        
    if form.validate_on_submit():
        new_name = request.form.get('new_folder_name')
        if new_name:
            folder.name = new_name
            db.session.commit()
            flash('Pasta renomeada com sucesso!', 'success')
        else:
            flash('O nome da pasta não pode estar vazio.', 'error')
    return redirect(url_for('visoes.pastas_page', subject_id=subject.id))

@views_bp.route('/update_folder_color/<int:folder_id>', methods=['POST'])
@login_required
def update_folder_color(folder_id):
    form = EmptyForm()
    folder = Folder.query.get_or_404(folder_id)
    subject = folder.subject

    if not check_permission(subject):
        flash('Você não tem permissão para editar esta pasta.', 'error')
        return redirect(url_for('visoes.pastas_page', subject_id=subject.id))
        
    if form.validate_on_submit():
        new_color = request.form.get('new_color')
        if new_color and len(new_color) == 7 and new_color.startswith('#'):
            folder.color = new_color
            db.session.commit()
            flash('Cor da pasta atualizada!', 'success')
        else:
            flash('Formato de cor inválido.', 'error')
    return redirect(url_for('visoes.pastas_page', subject_id=subject.id))

@views_bp.route('/delete_folder/<int:folder_id>', methods=['POST'])
@login_required
def delete_folder(folder_id):
    form = EmptyForm()
    folder = Folder.query.get_or_404(folder_id)
    subject = folder.subject
    subject_id = subject.id # Guarda o ID antes de apagar

    if not check_permission(subject):
        flash('Você não tem permissão para excluir esta pasta.', 'error')
        return redirect(url_for('visoes.pastas_page', subject_id=subject_id))
        
    if form.validate_on_submit():
        try:
            upload_folder_abs = os.path.join(current_app.root_path, current_app.config['UPLOAD_FOLDER'].split('/')[-1])
            for file in folder.files:
                file_path = os.path.join(upload_folder_abs, file.filename)
                if os.path.exists(file_path):
                    os.remove(file_path)
            
            db.session.delete(folder)
            db.session.commit()
            flash('Pasta e todos os seus ficheiros foram excluídos.', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao excluir a pasta: {e}', 'error')
            
    return redirect(url_for('visoes.pastas_page', subject_id=subject_id))

@views_bp.route('/delete_file/<int:file_id>', methods=['POST'])
@login_required
def delete_file(file_id):
    form = EmptyForm()
    file_db = File.query.get_or_404(file_id)
    folder_id = file_db.folder_id
    subject = file_db.folder.subject

    if not check_permission(subject):
        flash('Você não tem permissão para excluir este ficheiro.', 'error')
        return redirect(url_for('visoes.folders', folder_id=folder_id))
        
    if form.validate_on_submit():
        try:
            upload_folder_abs = os.path.join(current_app.root_path, current_app.config['UPLOAD_FOLDER'].split('/')[-1])
            file_path = os.path.join(upload_folder_abs, file_db.filename)
            
            if os.path.exists(file_path):
                os.remove(file_path)
            
            db.session.delete(file_db)
            db.session.commit()
            flash('Ficheiro excluído com sucesso.', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao excluir o ficheiro: {e}', 'error')
            
    return redirect(url_for('visoes.folders', folder_id=folder_id))


# --- NOVA ROTA PARA UPLOAD DE AVATAR ---
@views_bp.route('/upload_avatar', methods=['POST'])
@csrf.exempt # Isenção de CSRF (mais fácil pro tutorial)
@login_required
def upload_avatar():
    if 'avatar' not in request.files:
        flash('Nenhum arquivo selecionado.', 'error')
        return redirect(request.referrer or url_for('visoes.pagina_inicio'))
    
    file = request.files['avatar']
    
    if file.filename == '':
        flash('Nenhum arquivo selecionado.', 'error')
        return redirect(request.referrer or url_for('visoes.pagina_inicio'))
        
    if file and allowed_file(file.filename):
        user = User.query.get(session['user_id'])
        original_filename = secure_filename(file.filename)
        extension = original_filename.rsplit('.', 1)[1].lower()
        
        # Cria nome de arquivo único: user_1.png, user_2.jpg
        filename = f"user_{user.id}.{extension}"
        
        # Pega o caminho absoluto para salvar
        avatar_dir = os.path.join(current_app.root_path, AVATAR_UPLOAD_FOLDER)
        avatar_save_path = os.path.join(avatar_dir, filename)
        
        # Garante que a pasta /static/avatars/ existe
        os.makedirs(avatar_dir, exist_ok=True)
        
        try:
            # Apaga o avatar antigo (se existir e não for o default)
            if user.profile_pic != 'default_avatar.png':
                old_file_path = os.path.join(avatar_dir, user.profile_pic)
                if os.path.exists(old_file_path):
                    os.remove(old_file_path)
            
            # Salva o arquivo novo
            file.save(avatar_save_path)
            
            # Atualiza o nome no banco
            user.profile_pic = filename
            db.session.commit()
            flash('Foto de perfil atualizada!', 'success')
            
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao salvar a foto: {e}', 'error')
        
    else:
        flash('Tipo de arquivo não permitido. Use .png, .jpg, .jpeg ou .gif.', 'error')

    # Redireciona de volta para a página que o usuário estava (tutorial ou perfil)
    return redirect(request.referrer or url_for('visoes.pagina_inicio'))