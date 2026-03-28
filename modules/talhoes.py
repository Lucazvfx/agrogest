from flask import Blueprint, render_template, request, redirect, url_for, flash
from database import get_db

talhoes_bp = Blueprint('talhoes', __name__)

@talhoes_bp.route('/')
def index():
    db = get_db()
    talhoes = db.execute("""
        SELECT t.*, 
               COUNT(DISTINCT p.id) as num_plantios,
               MAX(c.produtividade_scha) as melhor_produtividade,
               (SELECT COUNT(*) FROM analises_solo a WHERE a.talhao_id = t.id) as num_analises
        FROM talhoes t
        LEFT JOIN plantios p ON p.talhao_id = t.id
        LEFT JOIN colheitas c ON c.plantio_id = p.id
        GROUP BY t.id
        ORDER BY t.nome
    """).fetchall()
    return render_template('talhoes/index.html', talhoes=talhoes)

@talhoes_bp.route('/novo', methods=['GET', 'POST'])
def novo():
    if request.method == 'POST':
        db = get_db()
        db.execute(
            "INSERT INTO talhoes (nome, area_ha, localizacao, tipo_solo, observacoes) VALUES (?,?,?,?,?)",
            (request.form['nome'], request.form['area_ha'],
             request.form.get('localizacao'), request.form.get('tipo_solo'),
             request.form.get('observacoes'))
        )
        db.commit()
        flash('Talhão cadastrado com sucesso!', 'success')
        return redirect(url_for('talhoes.index'))
    return render_template('talhoes/form.html', talhao=None)

@talhoes_bp.route('/<int:id>/editar', methods=['GET', 'POST'])
def editar(id):
    db = get_db()
    talhao = db.execute("SELECT * FROM talhoes WHERE id=?", (id,)).fetchone()
    if request.method == 'POST':
        db.execute(
            "UPDATE talhoes SET nome=?, area_ha=?, localizacao=?, tipo_solo=?, observacoes=? WHERE id=?",
            (request.form['nome'], request.form['area_ha'],
             request.form.get('localizacao'), request.form.get('tipo_solo'),
             request.form.get('observacoes'), id)
        )
        db.commit()
        flash('Talhão atualizado!', 'success')
        return redirect(url_for('talhoes.index'))
    return render_template('talhoes/form.html', talhao=talhao)

@talhoes_bp.route('/<int:id>/excluir', methods=['POST'])
def excluir(id):
    db = get_db()
    db.execute("DELETE FROM talhoes WHERE id=?", (id,))
    db.commit()
    flash('Talhão excluído.', 'info')
    return redirect(url_for('talhoes.index'))

@talhoes_bp.route('/<int:id>/detalhe')
def detalhe(id):
    db = get_db()
    talhao = db.execute("SELECT * FROM talhoes WHERE id=?", (id,)).fetchone()
    analises = db.execute("SELECT * FROM analises_solo WHERE talhao_id=? ORDER BY data_coleta DESC", (id,)).fetchall()
    plantios = db.execute("""
        SELECT p.*, c.produtividade_scha, c.receita_bruta
        FROM plantios p
        LEFT JOIN colheitas c ON c.plantio_id = p.id
        WHERE p.talhao_id=? ORDER BY p.safra DESC
    """, (id,)).fetchall()
    return render_template('talhoes/detalhe.html', talhao=talhao, analises=analises, plantios=plantios)
