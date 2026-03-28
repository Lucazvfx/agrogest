from flask import Blueprint, render_template, request, redirect, url_for, flash
from database import get_db

plantio_bp = Blueprint('plantio', __name__)

@plantio_bp.route('/')
def index():
    db = get_db()
    plantios = db.execute("""
        SELECT p.*, t.nome as talhao_nome, t.area_ha,
               c.produtividade_scha, c.receita_bruta
        FROM plantios p
        JOIN talhoes t ON t.id = p.talhao_id
        LEFT JOIN colheitas c ON c.plantio_id = p.id
        ORDER BY p.safra DESC, t.nome
    """).fetchall()
    return render_template('plantio/index.html', plantios=plantios)

@plantio_bp.route('/novo', methods=['GET', 'POST'])
def novo():
    db = get_db()
    talhoes = db.execute("SELECT * FROM talhoes ORDER BY nome").fetchall()
    if request.method == 'POST':
        f = request.form
        db.execute("""
            INSERT INTO plantios (talhao_id, safra, data_plantio, hibrido, populacao, area_plantada, status, observacoes)
            VALUES (?,?,?,?,?,?,?,?)
        """, (f['talhao_id'], f['safra'], f.get('data_plantio'), f.get('hibrido'),
              f.get('populacao'), f.get('area_plantada'), f.get('status','planejado'), f.get('observacoes')))
        db.commit()
        flash('Plantio cadastrado!', 'success')
        return redirect(url_for('plantio.index'))
    return render_template('plantio/form.html', plantio=None, talhoes=talhoes)

@plantio_bp.route('/<int:id>/editar', methods=['GET', 'POST'])
def editar(id):
    db = get_db()
    plantio = db.execute("SELECT * FROM plantios WHERE id=?", (id,)).fetchone()
    talhoes = db.execute("SELECT * FROM talhoes ORDER BY nome").fetchall()
    if request.method == 'POST':
        f = request.form
        db.execute("""
            UPDATE plantios SET talhao_id=?, safra=?, data_plantio=?, hibrido=?,
            populacao=?, area_plantada=?, status=?, observacoes=? WHERE id=?
        """, (f['talhao_id'], f['safra'], f.get('data_plantio'), f.get('hibrido'),
              f.get('populacao'), f.get('area_plantada'), f.get('status'), f.get('observacoes'), id))
        db.commit()
        flash('Plantio atualizado!', 'success')
        return redirect(url_for('plantio.index'))
    return render_template('plantio/form.html', plantio=plantio, talhoes=talhoes)

@plantio_bp.route('/<int:id>/adubacoes', methods=['GET', 'POST'])
def adubacoes(id):
    db = get_db()
    plantio = db.execute("SELECT p.*, t.nome as talhao_nome FROM plantios p JOIN talhoes t ON t.id=p.talhao_id WHERE p.id=?", (id,)).fetchone()
    if request.method == 'POST':
        f = request.form
        db.execute("""
            INSERT INTO aplicacoes_adubacao (plantio_id, tipo, data_aplicacao, fertilizante, dose_kgha, area_ha, custo_kg, observacoes)
            VALUES (?,?,?,?,?,?,?,?)
        """, (id, f['tipo'], f.get('data_aplicacao'), f['fertilizante'],
              f['dose_kgha'], f['area_ha'], f.get('custo_kg'), f.get('observacoes')))
        db.commit()
        flash('Aplicação registrada!', 'success')
    apls = db.execute("SELECT * FROM aplicacoes_adubacao WHERE plantio_id=? ORDER BY data_aplicacao", (id,)).fetchall()
    return render_template('plantio/adubacoes.html', plantio=plantio, aplicacoes=apls)
