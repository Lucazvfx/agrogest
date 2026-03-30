import sqlite3
from functools import wraps
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, g
from database import get_db
import hashlib
import os

auth_bp = Blueprint('auth', __name__)

# ── Helpers ──────────────────────────────────────────────────────────────────

def hash_senha(senha, salt=None):
    """SHA-256 com salt. Retorna 'salt$hash'."""
    if salt is None:
        salt = os.urandom(16).hex()
    h = hashlib.sha256(f"{salt}{senha}".encode()).hexdigest()
    return f"{salt}${h}"

def verificar_senha(senha, armazenada):
    salt, _ = armazenada.split('$', 1)
    return hash_senha(senha, salt) == armazenada

def login_required(f):
    """Decorator: redireciona para login se não autenticado."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'usuario_id' not in session:
            flash('Faça login para continuar.', 'warning')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated

def admin_required(f):
    """Decorator: apenas administradores."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if session.get('usuario_tipo') != 'admin':
            flash('Acesso restrito a administradores.', 'danger')
            return redirect(url_for('dashboard.index'))
        return f(*args, **kwargs)
    return decorated

def get_usuario_atual():
    """Retorna o usuário logado ou None."""
    if 'usuario_id' in session:
        db = get_db()
        return db.execute(
            "SELECT * FROM usuarios WHERE id = ?", (session['usuario_id'],)
        ).fetchone()
    return None

# ── Rotas ────────────────────────────────────────────────────────────────────

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if 'usuario_id' in session:
        return redirect(url_for('dashboard.index'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        senha = request.form.get('senha', '')
        db = get_db()
        usuario = db.execute(
            "SELECT * FROM usuarios WHERE email = ? AND ativo = 1", (email,)
        ).fetchone()

        if usuario and verificar_senha(senha, usuario['senha_hash']):
            session.permanent = True
            session['usuario_id']   = usuario['id']
            session['usuario_nome'] = usuario['nome']
            session['usuario_tipo'] = usuario['tipo']
            flash(f'Bem-vindo, {usuario["nome"]}!', 'success')
            return redirect(url_for('dashboard.index'))

        flash('E-mail ou senha incorretos.', 'danger')

    return render_template('auth/login.html')


@auth_bp.route('/logout')
def logout():
    session.clear()
    flash('Você saiu do sistema.', 'info')
    return redirect(url_for('auth.login'))


@auth_bp.route('/usuarios')
@login_required
@admin_required
def usuarios():
    db = get_db()
    lista = db.execute("SELECT id, nome, email, tipo, ativo, criado_em FROM usuarios ORDER BY nome").fetchall()
    return render_template('auth/usuarios.html', usuarios=lista)


@auth_bp.route('/usuarios/novo', methods=['GET', 'POST'])
@login_required
@admin_required
def novo_usuario():
    if request.method == 'POST':
        f = request.form
        nome  = f.get('nome', '').strip()
        email = f.get('email', '').strip().lower()
        senha = f.get('senha', '')
        tipo  = f.get('tipo', 'produtor')

        if not nome or not email or not senha:
            flash('Preencha todos os campos obrigatórios.', 'danger')
            return render_template('auth/form_usuario.html', usuario=None)

        db = get_db()
        existente = db.execute("SELECT id FROM usuarios WHERE email = ?", (email,)).fetchone()
        if existente:
            flash('Já existe um usuário com esse e-mail.', 'danger')
            return render_template('auth/form_usuario.html', usuario=None)

        db.execute(
            "INSERT INTO usuarios (nome, email, senha_hash, tipo) VALUES (?,?,?,?)",
            (nome, email, hash_senha(senha), tipo)
        )
        db.commit()
        flash(f'Usuário {nome} cadastrado com sucesso!', 'success')
        return redirect(url_for('auth.usuarios'))

    return render_template('auth/form_usuario.html', usuario=None)


@auth_bp.route('/usuarios/<int:id>/editar', methods=['GET', 'POST'])
@login_required
@admin_required
def editar_usuario(id):
    db = get_db()
    usuario = db.execute("SELECT * FROM usuarios WHERE id = ?", (id,)).fetchone()
    if not usuario:
        flash('Usuário não encontrado.', 'danger')
        return redirect(url_for('auth.usuarios'))

    if request.method == 'POST':
        f = request.form
        nome  = f.get('nome', '').strip()
        email = f.get('email', '').strip().lower()
        tipo  = f.get('tipo', 'produtor')
        ativo = 1 if f.get('ativo') else 0
        nova_senha = f.get('senha', '').strip()

        if nova_senha:
            db.execute(
                "UPDATE usuarios SET nome=?, email=?, tipo=?, ativo=?, senha_hash=? WHERE id=?",
                (nome, email, tipo, ativo, hash_senha(nova_senha), id)
            )
        else:
            db.execute(
                "UPDATE usuarios SET nome=?, email=?, tipo=?, ativo=? WHERE id=?",
                (nome, email, tipo, ativo, id)
            )
        db.commit()
        flash('Usuário atualizado!', 'success')
        return redirect(url_for('auth.usuarios'))

    return render_template('auth/form_usuario.html', usuario=usuario)


@auth_bp.route('/minha-conta', methods=['GET', 'POST'])
@login_required
def minha_conta():
    db = get_db()
    usuario = db.execute("SELECT * FROM usuarios WHERE id = ?", (session['usuario_id'],)).fetchone()

    if request.method == 'POST':
        nova_senha = request.form.get('senha', '').strip()
        confirma   = request.form.get('confirma', '').strip()
        if nova_senha and nova_senha == confirma:
            db.execute("UPDATE usuarios SET senha_hash=? WHERE id=?",
                       (hash_senha(nova_senha), session['usuario_id']))
            db.commit()
            flash('Senha alterada com sucesso!', 'success')
        elif nova_senha != confirma:
            flash('As senhas não coincidem.', 'danger')

    return render_template('auth/minha_conta.html', usuario=usuario)