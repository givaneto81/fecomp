import os
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, send_from_directory, current_app
from werkzeug.utils import secure_filename
from werkzeug.security import check_password_hash, generate_password_hash
from functools import wraps
from .models import User, Subject, Folder, File
from .extensions import db
from .forms import EmptyForm

views_bp = Blueprint('visoes', __name__)

# --- DECORATOR PARA EXIGIR LOGIN ---
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Por favor, faça login para acessar esta página.', 'error')
            return redirect(url_for('autenticacao.pagina_login'))
        return f(*args, **kwargs)
    return decorated_function

# --- ROTAS GET (PARA RENDERIZAR PÁGINAS) ---
@views_bp.route('/inicio')
@login_required
def pagina_inicio():
    return render_template('inicio.html')

@views_bp.route('/materias')
@login_required
def pagina_materias():
    form = EmptyForm()
    user_subjects = Subject.query.filter_by(user_id=session['user_id']).order_by(Subject.name).all()
    # Passa o mesmo form para todos os modais da página
    return render_template('home.html', subjects=user_subjects, form=form, delete_form=form)

@views_bp.route('/pastas/<int:subject_id>')
@login_required
def pastas_page(subject_id):
    form = EmptyForm()
    subject = Subject.query.filter_by(id=subject_id, user_id=session['user_id']).first_or_404()
    folders = Folder.query.filter_by(subject_id=subject.id).order_by(Folder.name).all()
    return render_template('pastas.html', subject=subject, folders=folders, form=form)

@views_bp.route('/pasta/<int:folder_id>')
@login_required
def folders(folder_id):
    form = EmptyForm()
    folder = Folder.query.join(Subject).filter(Subject.user_id == session['user_id'], Folder.id == folder_id).first_or_404()
    files = File.query.filter_by(folder_id=folder.id).order_by(File.original_filename).all()
    return render_template('folders.html', folder=folder, files=files, form=form)

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

# --- ROTAS POST (PARA PROCESSAR FORMULÁRIOS) ---

@views_bp.route('/add_folder/<int:subject_id>', methods=['POST'])
@login_required
def add_folder(subject_id):
    form = EmptyForm()
    if form.validate_on_submit():
        subject = Subject.query.filter_by(id=subject_id, user_id=session['user_id']).first_or_404()
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
    if form.validate_on_submit():
        folder = Folder.query.join(Subject).filter(Subject.user_id == session['user_id'], Folder.id == folder_id).first_or_404()
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
        subject = Subject.query.filter_by(id=subject_id, user_id=session['user_id']).first_or_404()
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
        subject = Subject.query.filter_by(id=subject_id, user_id=session['user_id']).first_or_404()
        db.session.delete(subject)
        db.session.commit()
        flash('Matéria, pastas e arquivos foram excluídos.', 'success')
    return redirect(url_for('visoes.pagina_materias'))

# --- ROTAS DO PERFIL (ADICIONADAS E CORRIGIDAS) ---

@views_bp.route('/update_profile', methods=['POST'])
@login_required
def update_profile():
    form = EmptyForm()
    if form.validate_on_submit():
        user = User.query.get(session['user_id'])
        new_name = request.form.get('new_name')
        if new_name:
            user.name = new_name
            session['user_name'] = new_name # Atualiza o nome na sessão
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
    # Garante que o diretório de uploads existe
    upload_folder = os.path.join(current_app.root_path, '..', current_app.config['UPLOAD_FOLDER'])
    return send_from_directory(upload_folder, filename)