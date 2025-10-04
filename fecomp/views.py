import os
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, send_from_directory, current_app
from werkzeug.utils import secure_filename
from werkzeug.security import check_password_hash, generate_password_hash
from functools import wraps
from .models import User, Subject, Folder, File
from .extensions import db

# Cria o Blueprint de views
views_bp = Blueprint('views', __name__)

# --- DECORATOR PARA EXIGIR LOGIN ---
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Por favor, faça login para acessar esta página.', 'error')
            return redirect(url_for('auth.login_page')) # Aponta para a rota de login no blueprint 'auth'
        return f(*args, **kwargs)
    return decorated_function

# --- ROTAS PRINCIPAIS DO APP ---
@views_bp.route('/home')
@login_required
def home_page():
    user_subjects = Subject.query.filter_by(user_id=session['user_id']).order_by(Subject.name).all()
    return render_template('home.html', subjects=user_subjects)

@views_bp.route('/pastas/<int:subject_id>')
@login_required
def pastas_page(subject_id):
    subject = Subject.query.filter_by(id=subject_id, user_id=session['user_id']).first_or_404()
    folders = Folder.query.filter_by(subject_id=subject.id).order_by(Folder.name).all()
    return render_template('pastas.html', subject=subject, folders=folders)

@views_bp.route('/folder/<int:folder_id>')
@login_required
def folders(folder_id):
    folder = Folder.query.join(Subject).filter(Subject.user_id == session['user_id'], Folder.id == folder_id).first_or_404()
    files = File.query.filter_by(folder_id=folder.id).order_by(File.original_filename).all()
    return render_template('folders.html', folder=folder, files=files)

@views_bp.route('/chat')
@login_required
def chat_page():
    return render_template('chat.html')

@views_bp.route('/perfil')
@login_required
def perfil_page():
    user = User.query.get(session['user_id'])
    return render_template('perfil.html', user=user)


# --- ROTAS DE CRIAÇÃO E UPLOAD ---
@views_bp.route('/add_subject', methods=['POST'])
@login_required
def add_subject():
    subject_name = request.form.get('subject_name')
    if subject_name:
        new_subject = Subject(name=subject_name, user_id=session['user_id'])
        db.session.add(new_subject)
        db.session.commit()
        flash('Matéria adicionada com sucesso!', 'success')
    else:
        flash('O nome da matéria não pode estar vazio.', 'error')
    return redirect(url_for('views.home_page'))

@views_bp.route('/add_folder/<int:subject_id>', methods=['POST'])
@login_required
def add_folder(subject_id):
    subject = Subject.query.filter_by(id=subject_id, user_id=session['user_id']).first_or_404()
    folder_name = request.form.get('folder_name')
    if folder_name:
        new_folder = Folder(name=folder_name, subject_id=subject.id)
        db.session.add(new_folder)
        db.session.commit()
        flash('Pasta criada com sucesso!', 'success')
    else:
        flash('O nome da pasta não pode estar vazio.', 'error')
    return redirect(url_for('views.pastas_page', subject_id=subject_id))

@views_bp.route('/upload_file/<int:folder_id>', methods=['POST'])
@login_required
def upload_file(folder_id):
    folder = Folder.query.join(Subject).filter(Subject.user_id == session['user_id'], Folder.id == folder_id).first_or_404()
    if 'file' not in request.files or request.files['file'].filename == '':
        flash('Nenhum arquivo selecionado.', 'error')
        return redirect(url_for('views.folders', folder_id=folder_id))
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
    return redirect(url_for('views.folders', folder_id=folder_id))

# --- ROTA PARA SERVIR ARQUIVOS ---
@views_bp.route('/uploads/<path:filename>')
@login_required
def uploaded_file(filename):
    return send_from_directory(current_app.config['UPLOAD_FOLDER'], filename, as_attachment=False)


# --- ROTAS DE EDIÇÃO ---
@views_bp.route('/update_subject_color/<int:subject_id>', methods=['POST'])
@login_required
def update_subject_color(subject_id):
    subject = Subject.query.filter_by(id=subject_id, user_id=session['user_id']).first_or_404()
    new_color = request.form.get('new_color')
    if new_color and len(new_color) == 7 and new_color.startswith('#'):
        subject.color = new_color
        db.session.commit()
        flash('Cor da matéria atualizada!', 'success')
    else:
        flash('Formato de cor inválido.', 'error')
    return redirect(url_for('views.home_page'))

@views_bp.route('/delete_subject/<int:subject_id>', methods=['POST'])
@login_required
def delete_subject(subject_id):
    subject = Subject.query.filter_by(id=subject_id, user_id=session['user_id']).first_or_404()
    for folder in subject.folders:
        for file in folder.files:
            try:
                os.remove(os.path.join(current_app.config['UPLOAD_FOLDER'], file.filename))
            except OSError as e:
                print(f"Erro ao deletar o arquivo físico {file.filename}: {e}")
    db.session.delete(subject)
    db.session.commit()
    flash('Matéria, pastas e arquivos foram excluídos.', 'success')
    return redirect(url_for('views.home_page'))

@views_bp.route('/rename_folder/<int:folder_id>', methods=['POST'])
@login_required
def rename_folder(folder_id):
    folder = Folder.query.join(Subject).filter(Subject.user_id == session['user_id'], Folder.id == folder_id).first_or_404()
    new_name = request.form.get('new_folder_name')
    if new_name:
        folder.name = new_name
        db.session.commit()
        flash('Pasta renomeada com sucesso!', 'success')
    else:
        flash('O novo nome não pode ser vazio.', 'error')
    return redirect(url_for('views.pastas_page', subject_id=folder.subject_id))

@views_bp.route('/update_folder_color/<int:folder_id>', methods=['POST'])
@login_required
def update_folder_color(folder_id):
    folder = Folder.query.join(Subject).filter(Subject.user_id == session['user_id'], Folder.id == folder_id).first_or_404()
    new_color = request.form.get('new_color')
    if new_color and len(new_color) == 7 and new_color.startswith('#'):
        folder.color = new_color
        db.session.commit()
        flash('Cor da pasta atualizada!', 'success')
    else:
        flash('Formato de cor inválido.', 'error')
    return redirect(url_for('views.pastas_page', subject_id=folder.subject_id))

@views_bp.route('/delete_folder/<int:folder_id>', methods=['POST'])
@login_required
def delete_folder(folder_id):
    folder = Folder.query.join(Subject).filter(Subject.user_id == session['user_id'], Folder.id == folder_id).first_or_404()
    for file in folder.files:
        try:
            os.remove(os.path.join(current_app.config['UPLOAD_FOLDER'], file.filename))
        except OSError as e:
            print(f"Erro ao deletar o arquivo {file.filename}: {e}")
    subject_id = folder.subject_id
    db.session.delete(folder)
    db.session.commit()
    flash('Pasta e seus arquivos foram excluídos.', 'success')
    return redirect(url_for('views.pastas_page', subject_id=subject_id))

@views_bp.route('/delete_file/<int:file_id>', methods=['POST'])
@login_required
def delete_file(file_id):
    file_to_delete = File.query.get_or_404(file_id)
    folder = file_to_delete.folder
    subject = folder.subject

    # Verifica se o ficheiro pertence ao utilizador logado
    if subject.user_id != session['user_id']:
        flash('Você não tem permissão para apagar este ficheiro.', 'error')
        return redirect(url_for('views.home_page'))

    try:
        # Apaga o ficheiro físico
        os.remove(os.path.join(current_app.config['UPLOAD_FOLDER'], file_to_delete.filename))
        
        # Apaga o registo do banco de dados
        db.session.delete(file_to_delete)
        db.session.commit()
        flash('Ficheiro apagado com sucesso!', 'success')
    except OSError as e:
        db.session.rollback()
        print(f"Erro ao apagar o ficheiro físico: {e}")
        flash('Erro ao apagar o ficheiro do servidor.', 'error')
    
    return redirect(url_for('views.folders', folder_id=folder.id))


# --- ROTAS DE PERFIL ---
@views_bp.route('/update_profile', methods=['POST'])
@login_required
def update_profile():
    new_name = request.form.get('new_name')
    if new_name:
        user = User.query.get(session['user_id'])
        user.name = new_name
        db.session.commit()
        session['user_name'] = new_name
        flash('Nome atualizado com sucesso!', 'success')
    else:
        flash('O nome não pode ficar em branco.', 'error')
    return redirect(url_for('views.perfil_page'))

@views_bp.route('/change_password', methods=['POST'])
@login_required
def change_password():
    current_password = request.form.get('current_password')
    new_password = request.form.get('new_password')
    user = User.query.get(session['user_id'])
    if user and check_password_hash(user.password_hash, current_password):
        if new_password:
            user.password_hash = generate_password_hash(new_password)
            db.session.commit()
            flash('Senha alterada com sucesso!', 'success')
        else:
            flash('A nova senha não pode estar em branco.', 'error')
    else:
        flash('A senha atual está incorreta.', 'error')
    return redirect(url_for('views.perfil_page'))

@views_bp.route('/delete_account', methods=['POST'])
@login_required
def delete_account():
    user = User.query.get(session['user_id'])
    if user:
        db.session.delete(user)
        db.session.commit()
        session.clear()
        flash('Sua conta foi excluída com sucesso.', 'success')
        return redirect(url_for('auth.login_page'))
    flash('Não foi possível excluir a conta.', 'error')
    return redirect(url_for('views.perfil_page'))

# nota: garanta que todas as refs url_for apontem para o blueprint correto, por exemplo, 'views.home_page', 'auth.login_page', etc.