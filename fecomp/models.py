from .extensions import db
from datetime import datetime

# NÍVEL 1: TABELA DE VÍNCULO (MEMBERSHIP)
# Tabela de associação Muitos-para-Muitos entre User (Aluno/Professor) e Course (Turma)
membership = db.Table('membership',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('course_id', db.Integer, db.ForeignKey('course.id'), primary_key=True)
)

# NÍVEL 1: MODELO USER (COM ROLES)
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    
    # NÍVEL 1.2: Adiciona a coluna 'role'
    # Funções possíveis: 'aluno', 'professor', 'admin' (dono do cursinho)
    role = db.Column(db.String(20), nullable=False, default='aluno')
    
    tutorial_concluido = db.Column(db.Boolean, default=False, nullable=False)

    # NÍVEL 2: Matérias Pessoais (user_id preenchido)
    # Relação original, agora representa o repositório pessoal
    subjects = db.relationship('Subject', backref='user', lazy=True, cascade="all, delete-orphan",
                               foreign_keys='Subject.user_id')

    # NÍVEL 1: Cursos que este usuário administra (se for 'admin')
    administered_courses = db.relationship('Course', backref='admin', lazy=True, 
                                           foreign_keys='Course.admin_id')

    # NÍVEL 3: Entregas deste usuário (se for 'aluno')
    submissions = db.relationship('Submission', backref='student', lazy=True, 
                                  foreign_keys='Submission.student_id')

    # NÍVEL 4: Avisos criados por este usuário (se for 'professor')
    announcements = db.relationship('Announcement', backref='professor', lazy=True, 
                                    foreign_keys='Announcement.professor_id')
    
    # NÍVEL 1.3: Relação Muitos-para-Muitos (cursos que o usuário pertence)
    # A tabela 'membership' é usada aqui
    courses = db.relationship('Course', secondary=membership, lazy='dynamic',
                              backref=db.backref('members', lazy=True))


# NÍVEL 1: MODELO COURSE (TURMA)
class Course(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    
    # NÍVEL 1.1: O 'admin' (User) que é o dono desta turma
    admin_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # Relações (o que uma turma "tem")
    subjects = db.relationship('Subject', backref='course', lazy=True, 
                               foreign_keys='Subject.course_id', cascade="all, delete-orphan")
    tasks = db.relationship('Task', backref='course', lazy=True, cascade="all, delete-orphan")
    announcements = db.relationship('Announcement', backref='course', lazy=True, cascade="all, delete-orphan")


# NÍVEL 2: MODELO SUBJECT (HÍBRIDO)
class Subject(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    color = db.Column(db.String(7), nullable=False, default='#007bff')
    
    # NÍVEL 2.1: A CHAVE DA LÓGICA HÍBRIDA
    # Se user_id != NULL -> Matéria Pessoal
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    # Se course_id != NULL -> Matéria da Turma
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=True)
    
    folders = db.relationship('Folder', backref='subject', lazy=True, cascade="all, delete-orphan")

    # Garante que a matéria é OU pessoal OU da turma, nunca ambos.
    __table_args__ = (
        db.CheckConstraint(
            '(user_id IS NOT NULL AND course_id IS NULL) OR (user_id IS NULL AND course_id IS NOT NULL)',
            name='ck_subject_owner'
        ),
    )


# MODELO FOLDER (SEM ALTERAÇÃO SIGNIFICATIVA)
class Folder(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    color = db.Column(db.String(7), nullable=False, default='#007bff')
    subject_id = db.Column(db.Integer, db.ForeignKey('subject.id'), nullable=False)
    files = db.relationship('File', backref='folder', lazy=True, cascade="all, delete-orphan")


# MODELO FILE (REUTILIZADO)
class File(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    folder_id = db.Column(db.Integer, db.ForeignKey('folder.id'), nullable=False)
    
    # NÍVEL 3.1: Vínculo com a entrega (Submission)
    submission = db.relationship('Submission', backref='file', lazy=True, uselist=False)


# NÍVEL 3: MODELO TASK (TAREFA)
class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    due_date = db.Column(db.DateTime, nullable=True) # Prazo de entrega
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Vínculo com a Turma
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False)
    # Vínculo com a Matéria (opcional, pode ser uma tarefa geral da turma)
    subject_id = db.Column(db.Integer, db.ForeignKey('subject.id'), nullable=True)
    
    submissions = db.relationship('Submission', backref='task', lazy=True, cascade="all, delete-orphan")


# NÍVEL 3: MODELO SUBMISSION (ENTREGA)
class Submission(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    task_id = db.Column(db.Integer, db.ForeignKey('task.id'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # NÍVEL 3.1: Reutiliza o seu modelo File existente!
    file_id = db.Column(db.Integer, db.ForeignKey('file.id'), nullable=False)
    
    # Garante que um aluno só pode enviar uma entrega por tarefa
    __table_args__ = (
        db.UniqueConstraint('task_id', 'student_id', name='uq_student_task_submission'),
    )


# NÍVEL 4: MODELO ANNOUNCEMENT (MURAL DE AVISOS)
class Announcement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False)
    professor_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False) # Quem postou