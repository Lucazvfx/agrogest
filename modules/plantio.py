from flask import Blueprint, render_template, request, redirect, url_for, flash
from database import get_db
from auth import login_required
from flask import session

plantio_bp = Blueprint('plantio', __name__)


def uid():
    return session['usuario_id']


# =============================
# LISTAR PLANTIOS
# =============================
@plantio_bp.route('/')
@login_required
def index():

    db = get_db()

    plantios = db.execute("""
        SELECT p.*, t.nome as talhao_nome, t.area_ha,
               c.produtividade_scha, c.receita_bruta
        FROM plantios p
        JOIN talhoes t ON t.id = p.talhao_id
        LEFT JOIN colheitas c ON c.plantio_id = p.id
        WHERE t.usuario_id = ?
        ORDER BY p.safra DESC, t.nome
    """, (uid(),)).fetchall()

    return render_template('plantio/index.html', plantios=plantios)


# =============================
# NOVO PLANTIO
# =============================
@plantio_bp.route('/novo', methods=['GET', 'POST'])
@login_required
def novo():

    db = get_db()

    talhoes = db.execute(
        "SELECT * FROM talhoes WHERE usuario_id=? ORDER BY nome",
        (uid(),)
    ).fetchall()

    if request.method == 'POST':

        f = request.form

        db.execute("""
            INSERT INTO plantios
            (talhao_id, safra, data_plantio, hibrido, populacao, area_plantada, status, observacoes)
            VALUES (?,?,?,?,?,?,?,?)
        """, (
            f['talhao_id'],
            f['safra'],
            f.get('data_plantio'),
            f.get('hibrido'),
            f.get('populacao'),
            f.get('area_plantada'),
            f.get('status', 'planejado'),
            f.get('observacoes')
        ))

        db.commit()

        flash('Plantio cadastrado!', 'success')

        return redirect(url_for('plantio.index'))

    return render_template('plantio/form.html', plantio=None, talhoes=talhoes)


# =============================
# EDITAR PLANTIO
# =============================
@plantio_bp.route('/<int:id>/editar', methods=['GET', 'POST'])
@login_required
def editar(id):

    db = get_db()

    plantio = db.execute("""
        SELECT p.*
        FROM plantios p
        JOIN talhoes t ON t.id = p.talhao_id
        WHERE p.id=? AND t.usuario_id=?
    """, (id, uid())).fetchone()

    talhoes = db.execute(
        "SELECT * FROM talhoes WHERE usuario_id=? ORDER BY nome",
        (uid(),)
    ).fetchall()

    if request.method == 'POST':

        f = request.form

        db.execute("""
            UPDATE plantios
            SET talhao_id=?, safra=?, data_plantio=?, hibrido=?,
                populacao=?, area_plantada=?, status=?, observacoes=?
            WHERE id=?
        """, (
            f['talhao_id'],
            f['safra'],
            f.get('data_plantio'),
            f.get('hibrido'),
            f.get('populacao'),
            f.get('area_plantada'),
            f.get('status'),
            f.get('observacoes'),
            id
        ))

        db.commit()

        flash('Plantio atualizado!', 'success')

        return redirect(url_for('plantio.index'))

    return render_template('plantio/form.html', plantio=plantio, talhoes=talhoes)


# =============================
# DELETAR PLANTIO
# =============================
@plantio_bp.route('/<int:id>/deletar', methods=['POST'])
@login_required
def deletar(id):

    db = get_db()

    plantio = db.execute("""
        SELECT p.id
        FROM plantios p
        JOIN talhoes t ON t.id = p.talhao_id
        WHERE p.id=? AND t.usuario_id=?
    """, (id, uid())).fetchone()

    if not plantio:
        flash("Plantio não encontrado.", "danger")
        return redirect(url_for("plantio.index"))

    # apagar aplicações vinculadas
    db.execute(
        "DELETE FROM aplicacoes_adubacao WHERE plantio_id=?",
        (id,)
    )

    # apagar plantio
    db.execute(
        "DELETE FROM plantios WHERE id=?",
        (id,)
    )

    db.commit()

    flash("Plantio removido com sucesso!", "success")

    return redirect(url_for("plantio.index"))


# =============================
# APLICAÇÕES DE ADUBAÇÃO
# =============================
@plantio_bp.route('/<int:id>/adubacoes', methods=['GET', 'POST'])
@login_required
def adubacoes(id):

    db = get_db()

    plantio = db.execute("""
        SELECT p.*, t.nome as talhao_nome
        FROM plantios p
        JOIN talhoes t ON t.id=p.talhao_id
        WHERE p.id=? AND t.usuario_id=?
    """, (id, uid())).fetchone()

    if request.method == 'POST':

        f = request.form

        db.execute("""
            INSERT INTO aplicacoes_adubacao
            (plantio_id, tipo, data_aplicacao, fertilizante, dose_kgha, area_ha, custo_kg, observacoes)
            VALUES (?,?,?,?,?,?,?,?)
        """, (
            id,
            f['tipo'],
            f.get('data_aplicacao'),
            f['fertilizante'],
            f['dose_kgha'],
            f['area_ha'],
            f.get('custo_kg'),
            f.get('observacoes')
        ))

        db.commit()

        flash('Aplicação registrada!', 'success')

           # Redireciona para a mesma rota (GET) para evitar reenvio e carregar a lista atualizada
        return redirect(url_for('plantio.adubacoes', id=id))

    # GET: busca as aplicações e renderiza
    apls = db.execute("SELECT * FROM aplicacoes_adubacao WHERE plantio_id=? ORDER BY data_aplicacao", (id,)).fetchall()
    return render_template('plantio/adubacoes.html', plantio=plantio, aplicacoes=apls)