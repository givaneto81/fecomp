import os
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, send_from_directory, current_app
from werkzeug.utils import secure_filename
from werkzeug.security import check_password_hash, generate_password_hash
from . import db
from .models import User, Subject, Folder, File
from . import login_required

views_bp = Blueprint('views', __name__)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']

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
    subject_name = request.form.get('subject_name', '').strip()
    if subject_name:
        # Verifica se já existe uma matéria com o mesmo nome para este usuário
        exists = Subject.query.filter_by(user_id=session['user_id'], name=subject_name).first()
        if not exists:
            new_subject = Subject(name=subject_name, user_id=session['user_id'])
            db.session.add(new_subject)
            db.session.commit()
            flash('Matéria adicionada com sucesso!', 'success')
        else:
            flash('Você já possui uma matéria com este nome.', 'warning')
    else:
        flash('O nome da matéria não pode estar vazio.', 'error')
    return redirect(url_for('views.home_page'))

@views_bp.route('/add_folder/<int:subject_id>', methods=['POST'])
@login_required
def add_folder(subject_id):
    subject = Subject.query.filter_by(id=subject_id, user_id=session['user_id']).first_or_404()
    folder_name = request.form.get('folder_name', '').strip()
    if folder_name:
        # Verifica se já existe uma pasta com o mesmo nome dentro desta matéria
        exists = Folder.query.filter_by(subject_id=subject.id, name=folder_name).first()
        if not exists:
            new_folder = Folder(name=folder_name, subject_id=subject.id)
            db.session.add(new_folder)
            db.session.commit()
            flash('Pasta criada com sucesso!', 'success')
        else:
            flash('Você já possui uma pasta com este nome nesta matéria.', 'warning')
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
    if file and allowed_file(file.filename):
        original_filename = secure_filename(file.filename)
        # Cria um nome de arquivo único para evitar conflitos
        filename = f"user_{session['user_id']}_folder_{folder_id}_{original_filename}"
        upload_folder = current_app.config['UPLOAD_FOLDER']

        os.makedirs(upload_folder, exist_ok=True)

        try:
            file.save(os.path.join(upload_folder, filename))
            new_file = File(filename=filename, original_filename=original_filename, folder_id=folder_id)
            db.session.add(new_file)
            db.session.commit()
            flash('Arquivo enviado com sucesso!', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Ocorreu um erro ao salvar o arquivo: {e}', 'error')

    else:
        flash('Tipo de arquivo não permitido.', 'error')

    return redirect(url_for('views.folders', folder_id=folder_id))

# --- ROTA PARA SERVIR ARQUIVOS ---
@views_bp.route('/uploads/<path:filename>')
@login_required
def uploaded_file(filename):
    # Adiciona uma verificação de segurança para garantir que o usuário tenha acesso ao arquivo
    file_record = File.query.filter_by(filename=filename).join(Folder).join(Subject).filter(Subject.user_id == session['user_id']).first_or_404()
    return send_from_directory(current_app.config['UPLOAD_FOLDER'], filename, as_attachment=False)


# --- ROTAS DE EDIÇÃO E EXCLUSÃO ---
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

    # Guarda os nomes dos arquivos para deletar do sistema de arquivos
    files_to_delete = [file.filename for folder in subject.folders for file in folder.files]

    try:
        # Primeiro, deleta o registro do banco de dados (com cascade)
        db.session.delete(subject)
        db.session.commit()

        # Se a deleção no DB for bem-sucedida, deleta os arquivos físicos
        for filename in files_to_delete:
            try:
                os.remove(os.path.join(current_app.config['UPLOAD_FOLDER'], filename))
            except OSError as e:
                # Log do erro, mas a operação principal já foi concluída
                print(f"Erro ao deletar o arquivo físico {filename}: {e}")
                flash(f"A matéria foi deletada, mas ocorreu um erro ao limpar o arquivo {filename}.", "warning")

        flash('Matéria e seus conteúdos foram excluídos com sucesso.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f"Ocorreu um erro ao deletar a matéria: {e}", "error")

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
    subject_id = folder.subject_id

    files_to_delete = [file.filename for file in folder.files]

    try:
        db.session.delete(folder)
        db.session.commit()

        for filename in files_to_delete:
            try:
                os.remove(os.path.join(current_app.config['UPLOAD_FOLDER'], filename))
            except OSError as e:
                print(f"Erro ao deletar o arquivo físico {filename}: {e}")
                flash(f"A pasta foi deletada, mas ocorreu um erro ao limpar o arquivo {filename}.", "warning")

        flash('Pasta e seus arquivos foram excluídos.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Ocorreu um erro ao deletar a pasta: {e}', 'error')

    return redirect(url_for('views.pastas_page', subject_id=subject_id))


# --- ROTAS DE PERFIL ---
@views_bp.route('/update_profile', methods=['POST'])
@login_required
def update_profile():
    new_name = request.form.get('new_name', '').strip()
    if new_name:
        user = User.query.get(session['user_id'])
        user.name = new_name
        db.session.commit()
        session['user_name'] = new_name # Atualiza o nome na sessão
        flash('Nome atualizado com sucesso!', 'success')
    else:
        flash('O nome não pode ficar em branco.', 'error')
    return redirect(url_for('views.perfil_page'))

@views_bp.route('/change_password', methods=['POST'])
@login_required
def change_password():
    user = User.query.get(session['user_id'])

    # Caso de borda: não permitir mudança de senha para contas OAuth
    if not user.password_hash:
        flash('Você não pode alterar a senha de uma conta criada com o Google.', 'warning')
        return redirect(url_for('views.perfil_page'))

    current_password = request.form.get('current_password')
    new_password = request.form.get('new_password')

    if not current_password or not new_password:
        flash('Todos os campos de senha são obrigatórios.', 'error')
        return redirect(url_for('views.perfil_page'))

    if check_password_hash(user.password_hash, current_password):
        if len(new_password) < 6: # Exemplo de validação de força da senha
            flash('A nova senha deve ter pelo menos 6 caracteres.', 'error')
        else:
            user.password_hash = generate_password_hash(new_password)
            db.session.commit()
            flash('Senha alterada com sucesso!', 'success')
    else:
        flash('A senha atual está incorreta.', 'error')

    return redirect(url_for('views.perfil_page'))

@views_bp.route('/delete_account', methods=['POST'])
@login_required
def delete_account():
    user = User.query.get(session['user_id'])
    if not user:
        flash('Usuário não encontrado. A exclusão não pode ser concluída.', 'error')
        return redirect(url_for('views.perfil_page'))

    # Coleta os nomes dos arquivos antes de iniciar a transação
    files_to_delete = [f.filename for f in File.query.join(Folder).join(Subject).filter(Subject.user_id == user.id).all()]

    try:
        # 1. Deleta os arquivos físicos primeiro
        for filename in files_to_delete:
            try:
                file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
                if os.path.exists(file_path):
                    os.remove(file_path)
            except OSError as e:
                # Se não for possível deletar um arquivo, interrompe e faz rollback
                raise Exception(f"Erro ao deletar o arquivo físico {filename}: {e}")

        # 2. Se a exclusão dos arquivos for bem-sucedida, deleta do banco de dados
        db.session.delete(user)
        db.session.commit()

        session.clear()
        flash('Sua conta e todos os seus dados foram excluídos com sucesso.', 'success')
        return redirect(url_for('auth.login_page'))

    except Exception as e:
        # Faz o rollback em caso de qualquer erro
        db.session.rollback()
        print(f"Ocorreu um erro ao excluir a conta: {e}")
        flash("Ocorreu um erro crítico ao tentar excluir sua conta. A operação foi cancelada para proteger seus dados. Por favor, contate o suporte.", "error")
        return redirect(url_for('views.perfil_page'))