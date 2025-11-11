from flask import Blueprint, render_template, request, redirect, url_for, flash, session
import datetime
from .models import User, Course, Subject, Task, Announcement, Submission
from .extensions import db
from .forms import EmptyForm
# Reutiliza os decorators
from .visoes import login_required, role_required 

admin_bp = Blueprint('admin_bp', __name__, url_prefix='/admin')

# --- FUNÇÕES DE VERIFICAÇÃO DE PERMISSÃO (HELPERS) ---
def get_task_or_404_with_permission(task_id):
    """ Busca uma tarefa e verifica se o usuário (admin/professor) tem permissão. """
    task = Task.query.get_or_404(task_id)
    course = task.course
    user = User.query.get(session['user_id'])

    if user.role == 'professor' and course not in user.courses:
        flash('Sem permissão para acessar esta tarefa.', 'error')
        return None, redirect(url_for('visoes.pagina_inicio'))
    
    if user.role == 'admin' and course.admin_id != user.id:
        flash('Sem permissão para acessar esta tarefa.', 'error')
        return None, redirect(url_for('admin_bp.index'))
        
    return task, course

def get_announcement_or_404_with_permission(announcement_id):
    """ Busca um aviso e verifica se o usuário (admin/autor) tem permissão. """
    announcement = Announcement.query.get_or_404(announcement_id)
    course = announcement.course
    user = User.query.get(session['user_id'])

    is_admin = (user.role == 'admin' and course.admin_id == user.id)
    is_author = (user.role == 'professor' and announcement.professor_id == user.id)

    if not is_admin and not is_author:
        flash('Sem permissão para gerir este aviso.', 'error')
        return None, redirect(url_for('admin_bp.manage_course', course_id=course.id))
        
    return announcement, course

def get_subject_or_404_with_permission(subject_id):
    """ Busca uma matéria de turma e verifica se o usuário (admin/professor) tem permissão. """
    subject = Subject.query.get_or_404(subject_id)
    if not subject.course: # Garante que é uma matéria de turma
        flash('Ação não permitida.', 'error')
        return None, redirect(url_for('visoes.pagina_materias'))
        
    course = subject.course
    user = User.query.get(session['user_id'])

    is_admin = (user.role == 'admin' and course.admin_id == user.id)
    is_professor_member = (user.role == 'professor' and course in user.courses)

    if not is_admin and not is_professor_member:
        flash('Sem permissão para gerir esta matéria.', 'error')
        return None, redirect(url_for('admin_bp.manage_course', course_id=course.id))
        
    return subject, course


# --- PAINEL DE CONTROLO (NÍVEL 4.3) ---

@admin_bp.route('/')
@login_required
@role_required(['admin', 'professor']) 
def index():
    user = User.query.get(session['user_id'])
    form = EmptyForm()
    
    if user.role == 'admin':
        courses = Course.query.filter_by(admin_id=session['user_id']).all()
    else: # Professor
        courses = user.courses.all()

    course_data = []
    for course in courses:
        pending_count = db.session.query(Submission.id)\
            .join(Task, Task.id == Submission.task_id)\
            .filter(Task.course_id == course.id)\
            .filter(Submission.grade == None)\
            .count()
            
        course_data.append({
            'course': course,
            'members_count': len(course.members), # Pega o N. de membros
            'pending_submissions': pending_count # N. de envios sem nota
        })
        
    return render_template('admin/admin_painel.html', course_data=course_data, form=form, user_role=user.role)

 
@admin_bp.route('/course', methods=['POST'])
@login_required
@role_required(['admin'])
def create_course():
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
@role_required(['admin', 'professor']) 
def manage_course(course_id):
    course = Course.query.get_or_404(course_id)
    user = User.query.get(session['user_id'])
    
    if user.role == 'professor' and course not in user.courses:
        flash('Você não tem permissão para gerir esta turma.', 'error')
        return redirect(url_for('visoes.pagina_inicio'))
    if user.role == 'admin' and course.admin_id != user.id:
        flash('Você não é o admin desta turma.', 'error')
        return redirect(url_for('admin_bp.index'))
        
    form = EmptyForm()
    
    non_members = User.query.filter(User.role != 'admin', ~User.courses.any(id=course_id)).all()

    return render_template('admin/admin_cursos.html', 
                         course=course, 
                         non_members=non_members,
                         form=form)

# --- Gestão de Matérias da Turma (NÍVEL 2.3) ---

@admin_bp.route('/course/<int:course_id>/add_subject', methods=['POST'])
@login_required
@role_required(['admin', 'professor'])
def add_course_subject(course_id):
    form = EmptyForm()
    course = Course.query.get_or_404(course_id)
    # (Verificar permissão)
    
    if form.validate_on_submit():
        subject_name = request.form.get('subject_name')
        if subject_name:
            new_subject = Subject(name=subject_name, course_id=course.id)
            db.session.add(new_subject)
            db.session.commit()
            flash('Matéria da turma criada!', 'success')
    return redirect(url_for('admin_bp.manage_course', course_id=course_id))

@admin_bp.route('/course_subject/<int:subject_id>/edit', methods=['GET', 'POST'])
@login_required
@role_required(['admin', 'professor'])
def edit_course_subject(subject_id):
    form = EmptyForm()
    subject, course = get_subject_or_404_with_permission(subject_id)
    if not subject:
        return course # Retorna o redirect

    if form.validate_on_submit(): # Rota POST
        new_name = request.form.get('subject_name')
        if new_name:
            subject.name = new_name
            db.session.commit()
            flash('Matéria atualizada com sucesso.', 'success')
            return redirect(url_for('admin_bp.manage_course', course_id=course.id))
        else:
            flash('O nome da matéria não pode estar vazio.', 'error')
            
    # Rota GET
    return render_template('admin/admin_editar_materia.html', subject=subject, form=form)

@admin_bp.route('/course_subject/<int:subject_id>/delete', methods=['POST'])
@login_required
@role_required(['admin', 'professor'])
def delete_course_subject(subject_id):
    form = EmptyForm()
    subject, course = get_subject_or_404_with_permission(subject_id)
    if not subject:
        return course # Retorna o redirect
    
    if form.validate_on_submit():
        try:
            db.session.delete(subject)
            db.session.commit()
            flash('Matéria da turma excluída com sucesso.', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao excluir a matéria: {e}', 'error')
            
    return redirect(url_for('admin_bp.manage_course', course_id=course.id))


# --- Gestão de Membros (NÍVEL 4.3.B) ---

@admin_bp.route('/course/<int:course_id>/add_member', methods=['POST'])
@login_required
@role_required(['admin']) 
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
    users = User.query.filter(User.id != session['user_id']).all()
    form = EmptyForm()
    return render_template('admin/admin_permissao.html', users=users, form=form)

@admin_bp.route('/user/<int:user_id>/set_role', methods=['POST'])
@login_required
@role_required(['admin'])
def set_user_role(user_id):
    form = EmptyForm()
    if form.validate_on_submit():
        user = User.query.get(user_id)
        new_role = request.form.get('role')

        if user.id == session['user_id']:
            flash('Você não pode alterar sua própria função.', 'error')
            return redirect(url_for('admin_bp.manage_users'))

        if user.id == 1 and new_role != 'admin':
            flash('A função do administrador principal não pode ser alterada.', 'error')
            return redirect(url_for('admin_bp.manage_users'))

        if user and new_role in ['aluno', 'professor', 'admin']:
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
    # (Verificar permissão)
    
    if form.validate_on_submit():
        title = request.form.get('title')
        desc = request.form.get('description')
        due_date_str = request.form.get('due_date')
        subject_id = request.form.get('subject_id') 
        
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

@admin_bp.route('/task/<int:task_id>/delete', methods=['POST'])
@login_required
@role_required(['admin', 'professor'])
def delete_task(task_id):
    form = EmptyForm()
    task, course = get_task_or_404_with_permission(task_id)
    if not task:
        return course 
    
    if form.validate_on_submit():
        try:
            db.session.delete(task)
            db.session.commit()
            flash('Tarefa excluída com sucesso.', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao excluir a tarefa: {e}', 'error')
            
    return redirect(url_for('admin_bp.manage_course', course_id=course.id))

@admin_bp.route('/task/<int:task_id>/edit', methods=['GET', 'POST'])
@login_required
@role_required(['admin', 'professor'])
def edit_task(task_id):
    form = EmptyForm()
    task, course = get_task_or_404_with_permission(task_id)
    if not task:
        return course 

    if form.validate_on_submit(): # Rota POST
        try:
            task.title = request.form.get('title')
            task.description = request.form.get('description')
            due_date_str = request.form.get('due_date')
            task.due_date = datetime.datetime.fromisoformat(due_date_str) if due_date_str else None
            
            subject_id_str = request.form.get('subject_id')
            task.subject_id = int(subject_id_str) if (subject_id_str and subject_id_str != "None") else None
            
            db.session.commit()
            flash('Tarefa atualizada com sucesso.', 'success')
            return redirect(url_for('admin_bp.manage_course', course_id=course.id))
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao atualizar a tarefa: {e}', 'error')
            
    # Rota GET
    return render_template('admin/admin_editar_tarefas.html', task=task, form=form)


# --- Gestão de Avisos (NÍVEL 4.1) ---

@admin_bp.route('/course/<int:course_id>/post_announcement', methods=['POST'])
@login_required
@role_required(['admin', 'professor'])
def post_announcement(course_id):
    form = EmptyForm()
    course = Course.query.get_or_404(course_id)
    # (Verificar permissão)
    
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

@admin_bp.route('/announcement/<int:announcement_id>/edit', methods=['GET', 'POST'])
@login_required
@role_required(['admin', 'professor'])
def edit_announcement(announcement_id):
    form = EmptyForm()
    announcement, course = get_announcement_or_404_with_permission(announcement_id)
    if not announcement:
        return course 
    
    if form.validate_on_submit(): # Rota POST
        new_content = request.form.get('content')
        if new_content:
            announcement.content = new_content
            db.session.commit()
            flash('Aviso atualizado com sucesso.', 'success')
            return redirect(url_for('admin_bp.manage_course', course_id=course.id))
        else:
            flash('O aviso não pode ficar em branco.', 'error')
            
    # Rota GET
    return render_template('admin/admin_editar_avisos.html', announcement=announcement, form=form)

@admin_bp.route('/announcement/<int:announcement_id>/delete', methods=['POST'])
@login_required
@role_required(['admin', 'professor'])
def delete_announcement(announcement_id):
    form = EmptyForm()
    announcement, course = get_announcement_or_404_with_permission(announcement_id)
    if not announcement:
        return course 
    
    if form.validate_on_submit():
        db.session.delete(announcement)
        db.session.commit()
        flash('Aviso excluído com sucesso.', 'success')
        
    return redirect(url_for('admin_bp.manage_course', course_id=course.id))


# --- (NÍVEL 3.2) Rota para Professores verem entregas ---
@admin_bp.route('/task/<int:task_id>/submissions')
@login_required
@role_required(['professor', 'admin'])
def view_submissions(task_id):
    task, course = get_task_or_404_with_permission(task_id)
    if not task:
        return course 

    submissions = Submission.query.filter_by(task_id=task.id).all()
    form = EmptyForm()
    
    return render_template('admin/admin_entregas.html', task=task, submissions=submissions, form=form)

@admin_bp.route('/submission/<int:submission_id>/grade', methods=['POST'])
@login_required
@role_required(['professor', 'admin'])
def grade_submission(submission_id):
    form = EmptyForm()
    submission = Submission.query.get_or_404(submission_id)
    task, course = get_task_or_404_with_permission(submission.task_id)
    if not task:
        return course
        
    if form.validate_on_submit():
        grade = request.form.get('grade')
        feedback = request.form.get('feedback')
        
        submission.grade = grade
        submission.feedback = feedback
        db.session.commit()
        flash(f'Nota/feedback para {submission.student.name} atualizado.', 'success')
        
    return redirect(url_for('admin_bp.view_submissions', task_id=submission.task_id))

# --- (PROPOSTA 3) Rota para destacar matérias ---
@admin_bp.route('/subject/<int:subject_id>/toggle_feature', methods=['POST'])
@login_required
@role_required(['admin', 'professor'])
def toggle_feature_subject(subject_id):
    form = EmptyForm()
    subject, course = get_subject_or_404_with_permission(subject_id)
    if not subject:
        return course # Retorna o redirect
    
    if form.validate_on_submit():
        try:
            subject.is_featured = not subject.is_featured
            db.session.commit()
            status = "destacada" if subject.is_featured else "não destacada"
            flash(f'Matéria "{subject.name}" agora está {status}.', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao alterar destaque: {e}', 'error')
    
    return redirect(url_for('admin_bp.manage_course', course_id=course.id))