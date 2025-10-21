from flask import Blueprint, render_template, request, redirect, url_for, flash, session
import datetime
from .models import User, Course, Subject, Task, Announcement, Submission
from .extensions import db
from .forms import EmptyForm
# Reutiliza os decorators
from .visoes import login_required, role_required 

admin_bp = Blueprint('admin_bp', __name__, url_prefix='/admin')

# --- PAINEL DE CONTROLO (NÍVEL 4.3) ---

@admin_bp.route('/')
@login_required
@role_required(['admin']) # Apenas o dono do cursinho
def index():
    """ Página principal do admin, mostra as turmas que ele gerencia. """
    courses = Course.query.filter_by(admin_id=session['user_id']).all()
    form = EmptyForm()
    # (Você precisará criar 'admin/admin_index.html')
    return render_template('admin/admin_index.html', courses=courses, form=form)

@admin_bp.route('/course', methods=['POST'])
@login_required
@role_required(['admin'])
def create_course():
    """ (4.3.A) CRUD de Course (Criar Turma) """
    form = EmptyForm()
    if form.validate_on_submit():
        name = request.form.get('course_name')
        if name:
            new_course = Course(name=name, admin_id=session['user_id'])
            db.session.add(new_course)
            db.session.commit()
            flash('Turma criada com sucesso.', 'success')
        else:
            flash('O nome da turma não pode estar vazio.', 'error')
    return redirect(url_for('admin_bp.index'))

@admin_bp.route('/course/<int:course_id>')
@login_required
@role_required(['admin', 'professor']) # Admin ou professor podem gerir a turma
def manage_course(course_id):
    """ Página para gerir uma turma específica (Matérias, Alunos, Professores) """
    course = Course.query.get_or_404(course_id)
    user = User.query.get(session['user_id'])
    
    # Verifica permissão
    if user.role == 'professor' and course not in user.courses:
        flash('Você não tem permissão para gerir esta turma.', 'error')
        return redirect(url_for('visoes.pagina_inicio'))
    if user.role == 'admin' and course.admin_id != user.id:
        flash('Você não é o admin desta turma.', 'error')
        return redirect(url_for('admin_bp.index'))
        
    form = EmptyForm()
    
    # Usuários que não estão na turma, para adicionar
    non_members = User.query.filter(User.role != 'admin', ~User.courses.any(id=course_id)).all()

    # (Você precisará criar 'admin/admin_manage_course.html')
    return render_template('admin/admin_manage_course.html', 
                         course=course, 
                         non_members=non_members,
                         form=form)

# --- Gestão de Matérias da Turma (NÍVEL 2.3) ---

@admin_bp.route('/course/<int:course_id>/add_subject', methods=['POST'])
@login_required
@role_required(['admin', 'professor'])
def add_course_subject(course_id):
    """ (2.3) Rota do Professor/Admin para criar Matéria da Turma """
    form = EmptyForm()
    course = Course.query.get_or_404(course_id)
    # ... (Verificar permissão) ...
    
    if form.validate_on_submit():
        subject_name = request.form.get('subject_name')
        if subject_name:
            # Cria a matéria LIGADA AO CURSO (course_id), não ao usuário
            new_subject = Subject(name=subject_name, course_id=course.id)
            db.session.add(new_subject)
            db.session.commit()
            flash('Matéria da turma criada!', 'success')
    return redirect(url_for('admin_bp.manage_course', course_id=course_id))

# --- Gestão de Membros (NÍVEL 4.3.B) ---

@admin_bp.route('/course/<int:course_id>/add_member', methods=['POST'])
@login_required
@role_required(['admin']) # Apenas admin pode adicionar/remover
def add_member(course_id):
    form = EmptyForm()
    course = Course.query.get_or_404(course_id)
    if course.admin_id != session['user_id']:
         flash('Sem permissão.', 'error')
         return redirect(url_for('admin_bp.index'))
         
    if form.validate_on_submit():
        user_id = request.form.get('user_id')
        user = User.query.get(user_id)
        if user:
            course.members.append(user)
            db.session.commit()
            flash(f'{user.name} adicionado à turma.', 'success')
    return redirect(url_for('admin_bp.manage_course', course_id=course_id))

@admin_bp.route('/course/<int:course_id>/remove_member/<int:user_id>', methods=['POST'])
@login_required
@role_required(['admin'])
def remove_member(course_id, user_id):
    form = EmptyForm()
    course = Course.query.get_or_404(course_id)
    if course.admin_id != session['user_id']:
         flash('Sem permissão.', 'error')
         return redirect(url_for('admin_bp.index'))
    
    if form.validate_on_submit():
        user = User.query.get(user_id)
        if user and user in course.members:
            course.members.remove(user)
            db.session.commit()
            flash(f'{user.name} removido da turma.', 'success')
    return redirect(url_for('admin_bp.manage_course', course_id=course_id))

# --- Gestão de Funções (NÍVEL 4.3.C) ---

@admin_bp.route('/users')
@login_required
@role_required(['admin'])
def manage_users():
    """ Página para o admin ver todos os usuários e mudar funções """
    users = User.query.filter(User.id != session['user_id']).all()
    form = EmptyForm()
    # (Você precisará criar 'admin/admin_manage_users.html')
    return render_template('admin/admin_manage_users.html', users=users, form=form)

@admin_bp.route('/user/<int:user_id>/set_role', methods=['POST'])
@login_required
@role_required(['admin'])
def set_user_role(user_id):
    form = EmptyForm()
    if form.validate_on_submit():
        user = User.query.get(user_id)
        new_role = request.form.get('role')
        if user and new_role in ['aluno', 'professor']:
            user.role = new_role
            db.session.commit()
            flash(f'Função de {user.name} atualizada para {new_role}.', 'success')
    return redirect(url_for('admin_bp.manage_users'))

# --- Gestão de Tarefas (NÍVEL 3.2) ---

@admin_bp.route('/course/<int:course_id>/create_task', methods=['POST'])
@login_required
@role_required(['admin', 'professor'])
def create_task(course_id):
    form = EmptyForm()
    course = Course.query.get_or_404(course_id)
    # ... (Verificar permissão) ...
    
    if form.validate_on_submit():
        title = request.form.get('title')
        desc = request.form.get('description')
        due_date_str = request.form.get('due_date')
        subject_id = request.form.get('subject_id') # ID da matéria da turma
        
        due_date = datetime.datetime.fromisoformat(due_date_str) if due_date_str else None
        
        if title:
            new_task = Task(title=title, 
                            description=desc, 
                            due_date=due_date, 
                            course_id=course_id, 
                            subject_id=subject_id if (subject_id and subject_id != "None") else None)
            db.session.add(new_task)
            db.session.commit()
            flash('Tarefa criada com sucesso.', 'success')
    return redirect(url_for('admin_bp.manage_course', course_id=course_id))

# --- Gestão de Avisos (NÍVEL 4.1) ---

@admin_bp.route('/course/<int:course_id>/post_announcement', methods=['POST'])
@login_required
@role_required(['admin', 'professor'])
def post_announcement(course_id):
    form = EmptyForm()
    course = Course.query.get_or_404(course_id)
    # ... (Verificar permissão) ...
    
    if form.validate_on_submit():
        content = request.form.get('content')
        if content:
            new_announcement = Announcement(content=content,
                                            course_id=course_id,
                                            professor_id=session['user_id'])
            db.session.add(new_announcement)
            db.session.commit()
            flash('Aviso publicado no mural.', 'success')
    return redirect(url_for('admin_bp.manage_course', course_id=course_id))

# --- (NÍVEL 3.2) Rota para Professores verem entregas ---
@admin_bp.route('/task/<int:task_id>/submissions')
@login_required
@role_required(['professor', 'admin'])
def view_submissions(task_id):
    task = Task.query.get_or_404(task_id)
    course = task.course
    user = User.query.get(session['user_id'])
    
    # ... (Verificar permissão) ...
    if user.role == 'professor' and course not in user.courses:
         flash('Sem permissão.', 'error')
         return redirect(url_for('visoes.pagina_inicio'))
    if user.role == 'admin' and course.admin_id != user.id:
         flash('Sem permissão.', 'error')
         return redirect(url_for('admin_bp.index'))

    submissions = Submission.query.filter_by(task_id=task.id).all()
    # (Você precisará criar 'admin/admin_view_submissions.html')
    return render_template('admin/admin_view_submissions.html', task=task, submissions=submissions)